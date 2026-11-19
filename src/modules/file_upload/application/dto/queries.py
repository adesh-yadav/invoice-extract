"""queries — application input DTOs for read requests."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GetFileInput:
    """Input query to fetch file by ID."""
    file_id: str


@dataclass(frozen=True)
class ListFilesInput:
    """Input query to list files with pagination."""
    limit: int = 50
    offset: int = 0
