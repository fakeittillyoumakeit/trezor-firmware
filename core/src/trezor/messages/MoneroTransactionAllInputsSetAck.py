# Automatically generated by pb2py
# fmt: off
import protobuf as p

from .MoneroTransactionRsigData import MoneroTransactionRsigData

if __debug__:
    try:
        from typing import Dict, List, Optional
        from typing_extensions import Literal  # noqa: F401
    except ImportError:
        Dict, List, Optional = None, None, None  # type: ignore


class MoneroTransactionAllInputsSetAck(p.MessageType):
    MESSAGE_WIRE_TYPE = 510

    def __init__(
        self,
        rsig_data: MoneroTransactionRsigData = None,
    ) -> None:
        self.rsig_data = rsig_data

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            1: ('rsig_data', MoneroTransactionRsigData, 0),
        }
