"""file_repository — SQLAlchemy persistence adapter implementing FileRepositoryPort."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.modules.file_upload.adapters.outbound.persistence import mappers
from src.modules.file_upload.adapters.outbound.persistence.models import UploadedFileModel
from src.modules.file_upload.application.ports.outbound.file_repository_port import FileRepositoryPort
from src.modules.file_upload.domain.model.uploaded_file import UploadedFile


class SqlAlchemyFileRepository(FileRepositoryPort):
    """PostgreSQL adapter for file persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, file_entity: UploadedFile) -> UploadedFile:
        model = mappers.to_model(file_entity)
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return mappers.to_domain(model)

    def update(self, file_entity: UploadedFile) -> UploadedFile:
        model = self._session.query(UploadedFileModel).filter_by(id=file_entity.id).first()
        if not model:
            raise ValueError(f"UploadedFileModel with id {file_entity.id} not found.")

        mappers.update_model(model, file_entity)
        self._session.commit()
        self._session.refresh(model)
        return mappers.to_domain(model)

    def get_by_id(self, file_id: str) -> UploadedFile | None:
        model = self._session.query(UploadedFileModel).filter_by(id=file_id).first()
        if not model:
            return None
        return mappers.to_domain(model)

    def list_all(self, limit: int = 50, offset: int = 0) -> list[UploadedFile]:
        models = (
            self._session.query(UploadedFileModel)
            .order_by(UploadedFileModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [mappers.to_domain(m) for m in models]
