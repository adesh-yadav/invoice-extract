"""upload_status — value object for file upload lifecycle states."""
from __future__ import annotations

from enum import Enum


class UploadStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
