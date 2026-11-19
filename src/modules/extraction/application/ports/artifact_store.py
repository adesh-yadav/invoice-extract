from typing import Protocol
from src.modules.extraction.domain.cdr import CDR


class CDRStore(Protocol):
    def read(self, reference: str) -> CDR: ...
