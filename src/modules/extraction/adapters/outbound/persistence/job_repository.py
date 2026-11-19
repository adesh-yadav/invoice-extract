from __future__ import annotations
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.modules.extraction.adapters.outbound.persistence.models import ExtractionJobModel, ExtractionResultModel
from src.modules.extraction.domain.job import ensure_transition


class SqlAlchemyJobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, file_id: str, idempotency_key: str | None = None) -> ExtractionJobModel:
        if idempotency_key:
            existing = self.session.query(ExtractionJobModel).filter_by(idempotency_key=idempotency_key).first()
            if existing:
                if existing.file_id != file_id:
                    raise ValueError("IDEMPOTENCY_CONFLICT")
                return existing
        job = ExtractionJobModel(id=str(uuid4()), file_id=file_id, status="queued", stage="queued", idempotency_key=idempotency_key)
        self.session.add(job)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            if idempotency_key:
                existing = self.session.query(ExtractionJobModel).filter_by(idempotency_key=idempotency_key).first()
                if existing:
                    if existing.file_id != file_id:
                        raise ValueError("IDEMPOTENCY_CONFLICT")
                    return existing
            raise
        self.session.refresh(job)
        return job

    def get(self, job_id: str) -> ExtractionJobModel | None:
        return self.session.get(ExtractionJobModel, job_id)

    def claim(self, worker_id: str) -> ExtractionJobModel | None:
        now = datetime.now(timezone.utc)
        self.session.query(ExtractionJobModel).filter(ExtractionJobModel.status == "processing", ExtractionJobModel.lease_until < now, ExtractionJobModel.attempt_count >= 3).update({"status": "failed", "stage": "done", "error_code": "JOB_ATTEMPTS_EXHAUSTED", "completed_at": now}, synchronize_session=False)
        self.session.commit()
        job = (self.session.query(ExtractionJobModel).filter(or_(ExtractionJobModel.status == "queued", (ExtractionJobModel.status == "processing") & (ExtractionJobModel.lease_until < now))).filter(ExtractionJobModel.attempt_count < 3).order_by(ExtractionJobModel.created_at).with_for_update(skip_locked=True).first())
        if not job:
            self.session.rollback()
            return None
        ensure_transition(job.status, "processing")
        job.status = "processing"
        job.stage = "reading"
        job.locked_by = worker_id
        job.lease_until = now + timedelta(minutes=30)
        job.attempt_count += 1
        job.started_at = job.started_at or now
        self.session.commit()
        self.session.refresh(job)
        return job

    def stage(self, job_id: str, stage: str) -> None:
        job = self.session.get(ExtractionJobModel, job_id)
        if job:
            job.stage = stage
            job.lease_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            self.session.commit()

    def finish(self, job_id: str, status: str, result: dict | None, validation: dict | None, cdr_ref: str | None, document_type: str | None, error_code: str | None) -> None:
        job = self.session.get(ExtractionJobModel, job_id)
        if job is None:
            raise ValueError("JOB_NOT_FOUND")
        ensure_transition(job.status, status)
        job.status = status
        job.stage = "done"
        job.cdr_ref = cdr_ref
        job.error_code = error_code
        job.error_message = error_code
        job.completed_at = datetime.now(timezone.utc)
        job.locked_by = None
        job.lease_until = None
        if result is not None or validation is not None:
            self.session.add(ExtractionResultModel(id=str(uuid4()), job_id=job_id, document_type=document_type, extracted_json=result, validation_report=validation, evidence_ref=cdr_ref))
        self.session.commit()

    def result(self, job_id: str) -> ExtractionResultModel | None:
        return self.session.query(ExtractionResultModel).filter_by(job_id=job_id).first()
