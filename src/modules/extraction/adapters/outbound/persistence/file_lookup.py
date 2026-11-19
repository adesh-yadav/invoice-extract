from sqlalchemy.orm import Session
from src.modules.file_upload.adapters.outbound.persistence.models import UploadedFileModel
from src.modules.extraction.domain.stored_file import StoredFile


class SqlAlchemyFileLookup:
    def __init__(self, session: Session):
        self.session = session

    def get(self, file_id: str) -> StoredFile | None:
        row = self.session.get(UploadedFileModel, file_id)
        if row is None:
            return None
        return StoredFile(id=row.id, status=row.status, extension=row.file_extension)
