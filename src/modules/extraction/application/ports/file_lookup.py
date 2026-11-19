from typing import Protocol
from src.modules.extraction.domain.stored_file import StoredFile


class FileLookup(Protocol):
    def get(self, file_id: str) -> StoredFile | None: ...
