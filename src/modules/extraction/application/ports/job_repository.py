from __future__ import annotations
from typing import Protocol
from src.modules.extraction.domain.processing import ProcessingEvent
from src.modules.extraction.domain.cdr import CDR


class JobRecord(Protocol):
    id: str
    file_id: str
    status: str
    stage: str
    error_code: str | None
    error_message: str | None
    cdr_ref: str | None


class ResultRecord(Protocol):
    extracted_json: dict | None
    validation_report: dict | None


class JobRepository(Protocol):
    def create(self, file_id: str, idempotency_key: str | None = None) -> JobRecord: ...
    def get(self, job_id: str) -> JobRecord | None: ...
    def claim(self, worker_id: str) -> JobRecord | None: ...
    def finish(self, job_id: str, status: str, result: dict | None, validation: dict | None, cdr_ref: str | None, document_type: str | None, error_code: str | None) -> None: ...
    def result(self, job_id: str) -> ResultRecord | None: ...
    def record_event(self, job_id: str, event: ProcessingEvent) -> None: ...
    def events(self, job_id: str) -> list[dict]: ...
    def save_cdr(self, job_id: str, cdr: CDR) -> None: ...
    def cdr(self, job_id: str) -> CDR | None: ...
