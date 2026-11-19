"""mappers — bidirectional mapping between ORM model and domain entity."""
from __future__ import annotations

from src.modules.file_upload.adapters.outbound.persistence.models import UploadedFileModel
from src.modules.file_upload.domain.model.upload_status import UploadStatus
from src.modules.file_upload.domain.model.uploaded_file import UploadedFile


def to_domain(model: UploadedFileModel) -> UploadedFile:
    return UploadedFile(
        id=model.id,
        original_name=model.original_name,
        stored_name=model.stored_name,
        file_extension=model.file_extension,
        content_type=model.content_type,
        file_size_bytes=model.file_size_bytes,
        file_path=model.file_path,
        status=UploadStatus(model.status),
        error_message=model.error_message,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(entity: UploadedFile) -> UploadedFileModel:
    return UploadedFileModel(
        id=entity.id,
        original_name=entity.original_name,
        stored_name=entity.stored_name or f"{entity.id}{entity.file_extension}",
        file_extension=entity.file_extension,
        content_type=entity.content_type,
        file_size_bytes=entity.file_size_bytes,
        file_path=entity.file_path,
        status=entity.status.value,
        error_message=entity.error_message,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def update_model(model: UploadedFileModel, entity: UploadedFile) -> None:
    model.stored_name = entity.stored_name or model.stored_name
    model.file_size_bytes = entity.file_size_bytes
    model.file_path = entity.file_path
    model.status = entity.status.value
    model.error_message = entity.error_message
    model.updated_at = entity.updated_at
