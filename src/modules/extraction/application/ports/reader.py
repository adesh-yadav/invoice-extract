from __future__ import annotations
from pathlib import Path
from typing import Protocol
from src.modules.extraction.domain.cdr import CDR


class DocumentReader(Protocol):
    def read(self, file_id: str, path: Path, content_type: str) -> CDR: ...
