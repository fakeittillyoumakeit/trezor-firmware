# Automatically generated by pb2py
# fmt: off
import protobuf as p

if __debug__:
    try:
        from typing import Dict, List, Optional
    except ImportError:
        Dict, List, Optional = None, None, None  # type: ignore


class BinanceOrderMsg(p.MessageType):
    MESSAGE_WIRE_TYPE = 707

    def __init__(
        self,
        id: str = None,
        ordertype: int = None,
        price: int = None,
        quantity: int = None,
        sender: str = None,
        side: int = None,
        symbol: str = None,
        timeinforce: int = None,
    ) -> None:
        self.id = id
        self.ordertype = ordertype
        self.price = price
        self.quantity = quantity
        self.sender = sender
        self.side = side
        self.symbol = symbol
        self.timeinforce = timeinforce

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            1: ('id', p.UnicodeType, 0),
            2: ('ordertype', p.UVarintType, 0),
            3: ('price', p.SVarintType, 0),
            4: ('quantity', p.SVarintType, 0),
            5: ('sender', p.UnicodeType, 0),
            6: ('side', p.UVarintType, 0),
            7: ('symbol', p.UnicodeType, 0),
            8: ('timeinforce', p.UVarintType, 0),
        }
