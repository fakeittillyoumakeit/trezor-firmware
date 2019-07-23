# Automatically generated by pb2py
# fmt: off
import protobuf as p

from .NEMCosignatoryModification import NEMCosignatoryModification

if __debug__:
    try:
        from typing import Dict, List, Optional
        from typing_extensions import Literal  # noqa: F401
    except ImportError:
        Dict, List, Optional = None, None, None  # type: ignore


class NEMAggregateModification(p.MessageType):

    def __init__(
        self,
        modifications: List[NEMCosignatoryModification] = None,
        relative_change: int = None,
    ) -> None:
        self.modifications = modifications if modifications is not None else []
        self.relative_change = relative_change

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            1: ('modifications', NEMCosignatoryModification, p.FLAG_REPEATED),
            2: ('relative_change', p.SVarintType, 0),
        }
