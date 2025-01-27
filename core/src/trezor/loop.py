"""
Implements an event loop with cooperative multitasking and async I/O.  Tasks in
the form of python coroutines (either plain generators or `async` functions) are
stepped through until completion, and can get asynchronously blocked by
`yield`ing or `await`ing a syscall.

See `schedule`, `run`, and syscalls `sleep`, `wait`, `signal` and `spawn`.
"""

import utime
import utimeq
from micropython import const

from trezor import io, log

if False:
    from typing import (
        Any,
        Awaitable,
        Callable,
        Coroutine,
        Dict,
        Generator,
        List,
        Optional,
        Set,
    )

    Task = Coroutine
    Finalizer = Callable[[Task, Any], None]

# function to call after every task step
after_step_hook = None  # type: Optional[Callable[[], None]]

# tasks scheduled for execution in the future
_queue = utimeq.utimeq(64)

# tasks paused on I/O
_paused = {}  # type: Dict[int, Set[Task]]

# functions to execute after a task is finished
_finalizers = {}  # type: Dict[int, Finalizer]

if __debug__:
    # for performance stats
    import array

    log_delay_pos = 0
    log_delay_rb_len = const(10)
    log_delay_rb = array.array("i", [0] * log_delay_rb_len)


def schedule(
    task: Task, value: Any = None, deadline: int = None, finalizer: Finalizer = None
) -> None:
    """
    Schedule task to be executed with `value` on given `deadline` (in
    microseconds).  Does not start the event loop itself, see `run`.
    """
    if deadline is None:
        deadline = utime.ticks_us()
    if finalizer is not None:
        _finalizers[id(task)] = finalizer
    _queue.push(deadline, task, value)


def pause(task: Task, iface: int) -> None:
    tasks = _paused.get(iface, None)
    if tasks is None:
        tasks = _paused[iface] = set()
    tasks.add(task)


def finalize(task: Task, value: Any) -> None:
    fn = _finalizers.pop(id(task), None)
    if fn is not None:
        fn(task, value)


def close(task: Task) -> None:
    for iface in _paused:
        _paused[iface].discard(task)
    _queue.discard(task)
    task.close()
    finalize(task, GeneratorExit())


def run() -> None:
    """
    Loop forever, stepping through scheduled tasks and awaiting I/O events
    inbetween.  Use `schedule` first to add a coroutine to the task queue.
    Tasks yield back to the scheduler on any I/O, usually by calling `await` on
    a `Syscall`.
    """

    if __debug__:
        global log_delay_pos

    max_delay = const(1000000)  # usec delay if queue is empty

    task_entry = [0, 0, 0]  # deadline, task, value
    msg_entry = [0, 0]  # iface | flags, value
    while _queue or _paused:
        # compute the maximum amount of time we can wait for a message
        if _queue:
            delay = utime.ticks_diff(_queue.peektime(), utime.ticks_us())
        else:
            delay = max_delay

        if __debug__:
            # add current delay to ring buffer for performance stats
            log_delay_rb[log_delay_pos] = delay
            log_delay_pos = (log_delay_pos + 1) % log_delay_rb_len

        if io.poll(_paused, msg_entry, delay):
            # message received, run tasks paused on the interface
            msg_tasks = _paused.pop(msg_entry[0], ())
            for task in msg_tasks:
                _step(task, msg_entry[1])
        else:
            # timeout occurred, run the first scheduled task
            if _queue:
                _queue.pop(task_entry)
                _step(task_entry[1], task_entry[2])  # type: ignore
                # error: Argument 1 to "_step" has incompatible type "int"; expected "Coroutine[Any, Any, Any]"
                # rationale: We use untyped lists here, because that is what the C API supports.


def clear() -> None:
    """Clear all queue state.  Any scheduled or paused tasks will be forgotten."""
    _ = [0, 0, 0]
    while _queue:
        _queue.pop(_)
    _paused.clear()
    _finalizers.clear()


def _step(task: Task, value: Any) -> None:
    try:
        if isinstance(value, BaseException):
            result = task.throw(value)  # type: ignore
            # error: Argument 1 to "throw" of "Coroutine" has incompatible type "Exception"; expected "Type[BaseException]"
            # rationale: In micropython, generator.throw() accepts the exception object directly.
        else:
            result = task.send(value)
    except StopIteration as e:  # as e:
        if __debug__:
            log.debug(__name__, "finish: %s", task)
        finalize(task, e.value)
    except Exception as e:
        if __debug__:
            log.exception(__name__, e)
        finalize(task, e)
    else:
        if isinstance(result, Syscall):
            result.handle(task)
        elif result is None:
            schedule(task)
        else:
            if __debug__:
                log.error(__name__, "unknown syscall: %s", result)
        if after_step_hook:
            after_step_hook()


class Syscall:
    """
    When tasks want to perform any I/O, or do any sort of communication with the
    scheduler, they do so through instances of a class derived from `Syscall`.
    """

    def __iter__(self) -> Task:  # type: ignore
        # support `yield from` or `await` on syscalls
        return (yield self)

    def __await__(self) -> Generator:
        return self.__iter__()  # type: ignore

    def handle(self, task: Task) -> None:
        pass


class sleep(Syscall):
    """
    Pause current task and resume it after given delay.  Although the delay is
    given in microseconds, sub-millisecond precision is not guaranteed.  Result
    value is the calculated deadline.

    Example:

    >>> planned = await loop.sleep(1000 * 1000)  # sleep for 1ms
    >>> print('missed by %d us', utime.ticks_diff(utime.ticks_us(), planned))
    """

    def __init__(self, delay_us: int) -> None:
        self.delay_us = delay_us

    def handle(self, task: Task) -> None:
        deadline = utime.ticks_add(utime.ticks_us(), self.delay_us)
        schedule(task, deadline, deadline)


class wait(Syscall):
    """
    Pause current task, and resume only after a message on `msg_iface` is
    received.  Messages are received either from an USB interface, or the
    touch display.  Result value a tuple of message values.

    Example:

    >>> hid_report, = await loop.wait(0xABCD)  # await USB HID report
    >>> event, x, y = await loop.wait(io.TOUCH)  # await touch event
    """

    def __init__(self, msg_iface: int) -> None:
        self.msg_iface = msg_iface

    def handle(self, task: Task) -> None:
        pause(task, self.msg_iface)


_NO_VALUE = object()


class signal(Syscall):
    """
    Pause current task, and let other running task to resume it later with a
    result value or an exception.

    Example:

    >>> # in task #1:
    >>> signal = loop.signal()
    >>> result = await signal
    >>> print('awaited result:', result)
    >>> # in task #2:
    >>> signal.send('hello from task #2')
    >>> # prints in the next iteration of the event loop
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.value = _NO_VALUE
        self.task = None  # type: Optional[Task]

    def handle(self, task: Task) -> None:
        self.task = task
        self._deliver()

    def send(self, value: Any) -> None:
        self.value = value
        self._deliver()

    def _deliver(self) -> None:
        if self.task is not None and self.value is not _NO_VALUE:
            schedule(self.task, self.value)
            self.task = None
            self.value = _NO_VALUE

    def __iter__(self) -> Task:  # type: ignore
        try:
            return (yield self)
        except:  # noqa: E722
            self.task = None
            raise


_type_gen = type((lambda: (yield))())


class spawn(Syscall):
    """
    Execute one or more children tasks and wait until one of them exits.
    Return value of `spawn` is the return value of task that triggered the
    completion.  By default, `spawn` returns after the first child completes, and
    other running children are killed (by cancelling any pending schedules and
    calling `close()`).

    Example:

    >>> # async def wait_for_touch(): ...
    >>> # async def animate_logo(): ...
    >>> touch_task = wait_for_touch()
    >>> animation_task = animate_logo()
    >>> waiter = loop.spawn(touch_task, animation_task)
    >>> result = await waiter
    >>> if animation_task in waiter.finished:
    >>>     print('animation task returned', result)
    >>> else:
    >>>     print('touch task returned', result)

    Note: You should not directly `yield` a `spawn` instance, see logic in
    `spawn.__iter__` for explanation.  Always use `await`.
    """

    def __init__(self, *children: Awaitable, exit_others: bool = True) -> None:
        self.children = children
        self.exit_others = exit_others
        self.finished = []  # type: List[Awaitable]  # children that finished
        self.scheduled = []  # type: List[Task]  # scheduled wrapper tasks

    def handle(self, task: Task) -> None:
        finalizer = self._finish
        scheduled = self.scheduled
        finished = self.finished

        self.callback = task
        scheduled.clear()
        finished.clear()

        for child in self.children:
            if isinstance(child, _type_gen):
                child_task = child
            else:
                child_task = iter(child)  # type: ignore
            schedule(child_task, None, None, finalizer)  # type: ignore
            scheduled.append(child_task)  # type: ignore
            # TODO: document the types here

    def exit(self, except_for: Task = None) -> None:
        for task in self.scheduled:
            if task != except_for:
                close(task)

    def _finish(self, task: Task, result: Any) -> None:
        if not self.finished:
            for index, child_task in enumerate(self.scheduled):
                if child_task is task:
                    child = self.children[index]
                    break
            self.finished.append(child)
            if self.exit_others:
                self.exit(task)
            schedule(self.callback, result)

    def __iter__(self) -> Task:  # type: ignore
        try:
            return (yield self)
        except:  # noqa: E722
            # exception was raised on the waiting task externally with
            # close() or throw(), kill the children tasks and re-raise
            self.exit()
            raise
