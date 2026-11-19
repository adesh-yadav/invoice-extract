"""module — wires the file_upload module's ports, adapters, and use cases."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from src.infrastructure.database.session import get_db_session
from src.modules.file_upload.adapters.outbound.persistence.file_repository import SqlAlchemyFileRepository
from src.modules.file_upload.adapters.outbound.storage.local_storage import LocalDiskFileStorage
from src.modules.file_upload.application.ports.inbound.get_file import GetFileQuery
from src.modules.file_upload.application.ports.inbound.list_files import ListFilesQuery
from src.modules.file_upload.application.ports.inbound.upload_file import UploadFileUseCase
from src.modules.file_upload.application.ports.outbound.file_repository_port import FileRepositoryPort
from src.modules.file_upload.application.ports.outbound.file_storage_port import FileStoragePort
from src.modules.file_upload.application.use_cases.get_file import GetFile
from src.modules.file_upload.application.use_cases.list_files import ListFiles
from src.modules.file_upload.application.use_cases.upload_file import UploadFile


def get_file_storage() -> FileStoragePort:
    return LocalDiskFileStorage()


def get_file_repository(
    session: Session = Depends(get_db_session),
) -> FileRepositoryPort:
    return SqlAlchemyFileRepository(session=session)


def get_upload_file_use_case(
    repo: FileRepositoryPort = Depends(get_file_repository),
    storage: FileStoragePort = Depends(get_file_storage),
) -> UploadFileUseCase:
    return UploadFile(repository=repo, storage=storage)


def get_get_file_query(
    repo: FileRepositoryPort = Depends(get_file_repository),
) -> GetFileQuery:
    return GetFile(repository=repo)


def get_list_files_query(
    repo: FileRepositoryPort = Depends(get_file_repository),
) -> ListFilesQuery:
    return ListFiles(repository=repo)
