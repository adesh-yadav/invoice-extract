"""Durable database backed worker. Launch separately from the API process."""
from __future__ import annotations
from pathlib import Path
import logging
import os
import time
from src.core.config import settings
from src.infrastructure.database.session import SessionLocal, init_db
from src.modules.file_upload.adapters.outbound.persistence.models import UploadedFileModel
from src.modules.file_upload.adapters.outbound.persistence.recovery import reconcile_stale_uploads
from src.modules.extraction.adapters.outbound.persistence.job_repository import SqlAlchemyJobRepository
from src.modules.extraction.adapters.outbound.persistence.processing_events import SqlAlchemyProcessingEventSink
from src.modules.extraction.config.module import build_process_job
from src.modules.extraction.adapters.outbound.ai.provider_factory import ModelConfig
from src.modules.extraction.adapters.outbound.ai.langchain_extractor import PROMPT_VERSION
from src.modules.extraction.domain.processing import ProcessingEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_one(worker_id: str, workflow=None) -> bool:
    with SessionLocal() as db:
        repo = SqlAlchemyJobRepository(db)
        job = repo.claim(worker_id)
        if job is None:
            return False
        file = db.get(UploadedFileModel, job.file_id)
        try:
            if file is None or file.status != "SUCCESS":
                raise ValueError("FILE_NOT_READY")
            path = Path(file.file_path).resolve()
            if path.parent != settings.UPLOAD_DIR.resolve() or path.name != file.stored_name or not path.is_file():
                raise ValueError("STORED_FILE_MISSING")
            if path.stat().st_size > settings.MAX_FILE_SIZE_BYTES:
                raise ValueError("FILE_SIZE_LIMIT")
            repo.record_event(job.id, ProcessingEvent("input", "stored_file_verified", details={"file_format": file.file_extension, "size_bytes": path.stat().st_size}))
            configured = ModelConfig(settings.LLM_PROVIDER, settings.EXTRACTION_MODEL)
            job.model_name = f"{configured.provider}:{configured.resolved_model}"
            job.prompt_version = PROMPT_VERSION
            db.commit()
            workflow = workflow or build_process_job(event_sink=SqlAlchemyProcessingEventSink(SessionLocal))
            repo.record_event(job.id, ProcessingEvent("configuration", "ai_models_selected", details=getattr(workflow, "model_info", {})))
            state = workflow.run(job.id, file.id, str(path), file.content_type, file.file_extension)
            payload = state.get("payload")
            result = ({"schema_version": "1.0", "job_id": job.id, "file_id": file.id, "status": state.get("status"), **payload} if payload else None)
            validation = {"passed": state.get("status") == "completed", "issues": state.get("issues", [])}
            repo.finish(job.id, state.get("status", "failed"), result, validation, state.get("cdr_ref"), state.get("document_type"), state.get("error_code"))
        except Exception as exc:
            logger.exception("Extraction job %s failed", job.id)
            db.rollback()
            try:
                repo.record_event(job.id, ProcessingEvent("worker", "job_exception", "failed", {"error_type": type(exc).__name__}))
                repo.finish(job.id, "failed", None, None, None, None, type(exc).__name__)
            except Exception:
                db.rollback()
                logger.exception("Could not persist failure for job %s; lease recovery will retry", job.id)
        return True


def main():
    init_db()
    worker_id = f"worker-{os.getpid()}"
    next_reconciliation = 0.0
    while True:
        if time.monotonic() >= next_reconciliation:
            try:
                with SessionLocal() as db:
                    reconcile_stale_uploads(db)
            except Exception:
                logger.exception("Upload reconciliation failed")
            next_reconciliation = time.monotonic() + 60
        try:
            worked = process_one(worker_id)
        except Exception:
            logger.exception("Worker poll failed")
            worked = False
        if not worked:
            time.sleep(2)


if __name__ == "__main__":
    main()
