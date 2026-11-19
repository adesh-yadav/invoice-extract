"""upload_file — inbound port (interface) for uploading files."""
from __future__ import annotations

from typing import Protocol

from src.modules.file_upload.application.dto.commands import UploadFileInput
from src.modules.file_upload.application.dto.results import FileView


class UploadFileUseCase(Protocol):
    def handle(self, request: UploadFileInput) -> FileView: ...
