# Automatically generated by pb2py
# fmt: off
import protobuf as p

if __debug__:
    try:
        from typing import Dict, List, Optional
        from typing_extensions import Literal  # noqa: F401
    except ImportError:
        Dict, List, Optional = None, None, None  # type: ignore


class MoneroRctKeyPublic(p.MessageType):

    def __init__(
        self,
        dest: bytes = None,
        commitment: bytes = None,
    ) -> None:
        self.dest = dest
        self.commitment = commitment

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            1: ('dest', p.BytesType, 0),
            2: ('commitment', p.BytesType, 0),
        }
