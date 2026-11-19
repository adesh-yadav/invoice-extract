"""uploaded_file — aggregate root representing an uploaded invoice file."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import uuid

from src.modules.file_upload.domain.exceptions import (
    InvalidFileNameError,
    InvalidStatusTransitionError,
)
from src.modules.file_upload.domain.model.upload_status import UploadStatus


@dataclass
class UploadedFile:
    """
    UploadedFile Aggregate Root.
    Encapsulates lifecycle rules and business invariants.
    `file_path` is pre-assigned at creation time so the PENDING DB record already stores it.
    `stored_name` is uniquely formatted as `uuid.ext` to prevent accidental overwrites.
    """
    original_name: str
    content_type: str
    file_path: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stored_name: Optional[str] = None
    file_extension: str = ""
    file_size_bytes: int = 0
    status: UploadStatus = UploadStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.original_name or not self.original_name.strip():
            raise InvalidFileNameError("Original file name cannot be empty.")

        if not self.file_path or not self.file_path.strip():
            raise ValueError("file_path must be pre-determined and non-empty.")

        if not self.file_extension:
            self.file_extension = Path(self.original_name).suffix.lower()

        # Enforce UUID-based stored filename to avoid overwrites
        if not self.stored_name:
            self.stored_name = f"{self.id}{self.file_extension}"

    def mark_as_success(self, file_size_bytes: int) -> None:
        """Mark status as SUCCESS after physical disk write completes."""
        if self.status == UploadStatus.SUCCESS:
            raise InvalidStatusTransitionError("File is already marked as SUCCESS.")

        self.status = UploadStatus.SUCCESS
        self.file_size_bytes = file_size_bytes
        self.error_message = None
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_failed(self, error_message: str) -> None:
        """Mark status as FAILED if physical disk write fails."""
        if self.status == UploadStatus.SUCCESS:
            raise InvalidStatusTransitionError("Cannot mark a successfully saved file as FAILED.")

        self.status = UploadStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now(timezone.utc)
