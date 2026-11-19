from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from src.infrastructure.database.session import Base


def now():
    return datetime.now(timezone.utc)


class ExtractionJobModel(Base):
    __tablename__ = "extraction_jobs"
    id = Column(String(36), primary_key=True)
    file_id = Column(String(36), ForeignKey("uploaded_files.id"), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True, default="queued")
    stage = Column(String(32), nullable=False, default="queued")
    attempt_count = Column(Integer, nullable=False, default=0)
    idempotency_key = Column(String(128), unique=True, nullable=True)
    locked_by = Column(String(128), nullable=True)
    lease_until = Column(DateTime(timezone=True), nullable=True)
    cdr_ref = Column(String(512), nullable=True)
    model_name = Column(String(128), nullable=True)
    prompt_version = Column(String(64), nullable=True)
    schema_version = Column(String(16), nullable=False, default="1.0")
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class ExtractionResultModel(Base):
    __tablename__ = "extraction_results"
    id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey("extraction_jobs.id"), unique=True, nullable=False)
    document_type = Column(String(32), nullable=True)
    extracted_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    validation_report = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    evidence_ref = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now, nullable=False)
