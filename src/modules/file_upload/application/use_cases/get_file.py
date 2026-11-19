"""get_file — use case for retrieving a single file view."""
from __future__ import annotations

from src.modules.file_upload.application.dto.queries import GetFileInput
from src.modules.file_upload.application.dto.results import FileView
from src.modules.file_upload.application.ports.outbound.file_repository_port import FileRepositoryPort
from src.modules.file_upload.application.use_cases.upload_file import _to_view


class GetFile:
    """Implements GetFileQuery inbound port."""

    def __init__(self, repository: FileRepositoryPort) -> None:
        self._repository = repository

    def handle(self, request: GetFileInput) -> FileView | None:
        entity = self._repository.get_by_id(request.file_id)
        if not entity:
            return None
        return _to_view(entity)
