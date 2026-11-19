"""get_file — inbound port (interface) for retrieving single file metadata."""
from __future__ import annotations

from typing import Protocol

from src.modules.file_upload.application.dto.queries import GetFileInput
from src.modules.file_upload.application.dto.results import FileView


class GetFileQuery(Protocol):
    def handle(self, request: GetFileInput) -> FileView | None: ...
