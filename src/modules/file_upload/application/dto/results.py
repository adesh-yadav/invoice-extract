"""results — application output DTOs (views) decoupling domain model from callers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class FileView:
    """Read view of an uploaded file."""
    id: str
    original_name: str
    stored_name: str
    file_extension: str
    content_type: str
    file_size_bytes: int
    file_path: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
