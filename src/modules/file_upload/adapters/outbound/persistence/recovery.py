"""Idempotent reconciliation of stale PENDING upload rows."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from src.core.config import settings
from src.modules.file_upload.adapters.outbound.persistence.models import UploadedFileModel


def reconcile_stale_uploads(db: Session, age_minutes: int = 5) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    rows = db.query(UploadedFileModel).filter(UploadedFileModel.status == "PENDING", UploadedFileModel.created_at < cutoff).all()
    changed = 0
    for row in rows:
        path = Path(row.file_path).resolve()
        if path.parent != settings.UPLOAD_DIR.resolve() or path.name != row.stored_name:
            row.status = "FAILED"
            row.error_message = "Stored path is invalid"
        elif path.is_file() and 0 < path.stat().st_size <= settings.MAX_FILE_SIZE_BYTES:
            row.status = "SUCCESS"
            row.file_size_bytes = path.stat().st_size
            row.error_message = None
        else:
            row.status = "FAILED"
            row.error_message = "Stored file is missing or invalid"
        changed += 1
    if changed:
        db.commit()
    return changed
