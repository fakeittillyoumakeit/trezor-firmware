# Automatically generated by pb2py
# fmt: off
import protobuf as p

from .BinanceCoin import BinanceCoin

if __debug__:
    try:
        from typing import Dict, List, Optional
    except ImportError:
        Dict, List, Optional = None, None, None  # type: ignore


class BinanceInputOutput(p.MessageType):

    def __init__(
        self,
        address: str = None,
        coins: List[BinanceCoin] = None,
    ) -> None:
        self.address = address
        self.coins = coins if coins is not None else []

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            1: ('address', p.UnicodeType, 0),
            2: ('coins', BinanceCoin, p.FLAG_REPEATED),
        }
