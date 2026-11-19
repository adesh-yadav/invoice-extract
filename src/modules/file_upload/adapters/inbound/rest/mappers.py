"""mappers — transforms application view DTOs into REST response schemas."""
from __future__ import annotations

from src.modules.file_upload.adapters.inbound.rest.schemas.responses import (
    FileListResponse,
    FileUploadResponse,
)
from src.modules.file_upload.application.dto.results import FileView


def to_file_response(view: FileView) -> FileUploadResponse:
    return FileUploadResponse(
        id=view.id,
        original_name=view.original_name,
        stored_name=view.stored_name,
        file_extension=view.file_extension,
        content_type=view.content_type,
        file_size_bytes=view.file_size_bytes,
        status=view.status,
        error_message="Upload failed" if view.error_message else None,
        created_at=view.created_at,
        updated_at=view.updated_at,
    )


def to_file_list_response(views: list[FileView]) -> FileListResponse:
    return FileListResponse(
        total=len(views),
        files=[to_file_response(v) for v in views],
    )
