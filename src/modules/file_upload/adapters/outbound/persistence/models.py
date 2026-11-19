"""models — SQLAlchemy ORM model for uploaded files table."""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, String, Text
from src.infrastructure.database.session import Base


class UploadedFileModel(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, index=True)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False, unique=True, index=True)
    file_extension = Column(String(32), nullable=False, index=True)
    content_type = Column(String(128), nullable=False)
    file_size_bytes = Column(BigInteger, default=0, nullable=False)
    file_path = Column(String(512), nullable=False, index=True)  # Recorded at PENDING time
    status = Column(String(32), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
