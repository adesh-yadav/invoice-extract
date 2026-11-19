"""file_storage_port — outbound port (interface) for physical file volume storage."""
from __future__ import annotations

from typing import BinaryIO, Protocol


class FileStoragePort(Protocol):
    def build_destination_path(self, filename: str) -> str:
        """Pre-computes the target storage path before physical save."""
        ...

    def save_to_path(self, file_content: BinaryIO, destination_path: str) -> int:
        """Saves stream to the designated target path and returns total bytes written."""
        ...

    def delete(self, file_path: str) -> bool:
        """Removes physical file from storage."""
        ...

    def exists(self, file_path: str) -> bool:
        """Checks existence of file on storage."""
        ...
