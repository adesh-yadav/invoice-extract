"""commands — application input DTOs for state mutations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True)
class UploadFileInput:
    """Input payload to upload a new file."""
    filename: str
    content_type: str
    file_stream: BinaryIO
