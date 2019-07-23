# Automatically generated by pb2py
# fmt: off
import protobuf as p

from .HDNodeType import HDNodeType

if __debug__:
    try:
        from typing import Dict, List, Optional
        from typing_extensions import Literal  # noqa: F401
    except ImportError:
        Dict, List, Optional = None, None, None  # type: ignore


class EthereumPublicKey(p.MessageType):
    MESSAGE_WIRE_TYPE = 451

    def __init__(
        self,
        node: HDNodeType = None,
        xpub: str = None,
    ) -> None:
        self.node = node
        self.xpub = xpub

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            1: ('node', HDNodeType, 0),
            2: ('xpub', p.UnicodeType, 0),
        }
