"""local_storage — physical volume storage adapter implementing FileStoragePort."""
from __future__ import annotations

from pathlib import Path
import shutil
import os
import tempfile
from typing import BinaryIO

from src.core.config import settings
from src.modules.file_upload.application.ports.outbound.file_storage_port import FileStoragePort


class LocalDiskFileStorage(FileStoragePort):
    """Storage adapter persisting files to disk / mounted Docker volume."""

    def __init__(self, base_directory: Path = settings.UPLOAD_DIR) -> None:
        self._base_dir = Path(base_directory)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def build_destination_path(self, filename: str) -> str:
        """Pre-computes the target absolute path."""
        target_path = self._base_dir / filename
        return str(target_path.resolve())

    def save_to_path(self, file_content: BinaryIO, destination_path: str) -> int:
        """Write and flush a sibling temporary file, then atomically rename."""
        target = Path(destination_path).resolve()
        if target.parent != self._base_dir.resolve():
            raise ValueError("Destination is outside the upload directory")
        target.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(file_content, "seek"):
            file_content.seek(0)

        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", prefix=".upload-", suffix=".tmp", dir=target.parent, delete=False) as destination:
                temporary_path = Path(destination.name)
                shutil.copyfileobj(file_content, destination)
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(temporary_path, target)
            directory_fd = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        return target.stat().st_size

    def delete(self, file_path: str) -> bool:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False

    def exists(self, file_path: str) -> bool:
        return Path(file_path).exists()
