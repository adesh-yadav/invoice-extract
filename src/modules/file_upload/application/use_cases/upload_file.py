"""upload_file — use case coordinating the upload lifecycle."""
from __future__ import annotations

import logging
from pathlib import Path
import uuid

from src.modules.file_upload.application.dto.commands import UploadFileInput
from src.modules.file_upload.application.dto.results import FileView
from src.modules.file_upload.application.ports.outbound.file_repository_port import FileRepositoryPort
from src.modules.file_upload.application.ports.outbound.file_storage_port import FileStoragePort
from src.modules.file_upload.domain.model.upload_status import UploadStatus
from src.modules.file_upload.domain.model.uploaded_file import UploadedFile

logger = logging.getLogger(__name__)


def _to_view(entity: UploadedFile) -> FileView:
    return FileView(
        id=entity.id,
        original_name=entity.original_name,
        stored_name=entity.stored_name or "",
        file_extension=entity.file_extension,
        content_type=entity.content_type,
        file_size_bytes=entity.file_size_bytes,
        file_path=entity.file_path,
        status=entity.status.value,
        error_message=entity.error_message,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class UploadFile:
    """Implements UploadFileUseCase inbound port."""

    def __init__(
        self,
        repository: FileRepositoryPort,
        storage: FileStoragePort,
    ) -> None:
        self._repository = repository
        self._storage = storage

    def handle(self, request: UploadFileInput) -> FileView:
        file_id = str(uuid.uuid4())
        file_ext = Path(request.filename).suffix.lower()
        stored_name = f"{file_id}{file_ext}"

        # 1. Pre-determine destination path before writing
        target_path = self._storage.build_destination_path(stored_name)

        # 2. Instantiate domain entity in PENDING state
        file_entity = UploadedFile(
            id=file_id,
            original_name=request.filename,
            content_type=request.content_type,
            stored_name=stored_name,
            file_extension=file_ext,
            file_path=target_path,
            status=UploadStatus.PENDING,
        )

        # 3. Save initial record into repository with status PENDING and file_path set
        logger.info(
            f"Pre-registering upload: ID={file_entity.id}, Path={file_entity.file_path}, Status=PENDING"
        )
        self._repository.save(file_entity)

        # 4. Physically write to volume storage
        try:
            total_bytes = self._storage.save_to_path(
                file_content=request.file_stream,
                destination_path=file_entity.file_path,
            )

            # 5. Mark as SUCCESS
            file_entity.mark_as_success(file_size_bytes=total_bytes)
            logger.info(
                f"File {file_entity.id} saved successfully ({total_bytes} bytes). Marked as SUCCESS."
            )

        except Exception as exc:
            error_msg = f"Failed to physically write file to storage: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            file_entity.mark_as_failed(error_message=error_msg)
            self._repository.update(file_entity)
            raise RuntimeError(error_msg) from exc

        # 6. Update database with final SUCCESS status
        self._repository.update(file_entity)

        # 7. Return mapped view
        return _to_view(file_entity)
