"""list_files — inbound port (interface) for listing files."""
from __future__ import annotations

from typing import Protocol

from src.modules.file_upload.application.dto.queries import ListFilesInput
from src.modules.file_upload.application.dto.results import FileView


class ListFilesQuery(Protocol):
    def handle(self, request: ListFilesInput) -> list[FileView]: ...
