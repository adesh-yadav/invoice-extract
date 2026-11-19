from __future__ import annotations
from typing import Protocol
from src.modules.extraction.domain.cdr import CDR
from src.modules.extraction.domain.financial import ExtractionPayload


class StructuredExtractor(Protocol):
    def extract(self, cdr: CDR, document_type: str) -> ExtractionPayload: ...
