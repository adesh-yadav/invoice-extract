"""list_files — use case for retrieving paginated file views."""
from __future__ import annotations

from src.modules.file_upload.application.dto.queries import ListFilesInput
from src.modules.file_upload.application.dto.results import FileView
from src.modules.file_upload.application.ports.outbound.file_repository_port import FileRepositoryPort
from src.modules.file_upload.application.use_cases.upload_file import _to_view


class ListFiles:
    """Implements ListFilesQuery inbound port."""

    def __init__(self, repository: FileRepositoryPort) -> None:
        self._repository = repository

    def handle(self, request: ListFilesInput) -> list[FileView]:
        entities = self._repository.list_all(limit=request.limit, offset=request.offset)
        return [_to_view(e) for e in entities]
