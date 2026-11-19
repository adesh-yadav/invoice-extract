"""A short-lived DB session per event keeps LangGraph nodes independent of the worker session."""
from __future__ import annotations
from src.modules.extraction.domain.processing import ProcessingEvent
from src.modules.extraction.domain.cdr import CDR
from src.modules.extraction.adapters.outbound.persistence.job_repository import SqlAlchemyJobRepository


class SqlAlchemyProcessingEventSink:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def record_event(self, job_id: str, event: ProcessingEvent) -> None:
        with self.session_factory() as session:
            SqlAlchemyJobRepository(session).record_event(job_id, event)

    def save_cdr(self, job_id: str, cdr: CDR) -> None:
        with self.session_factory() as session:
            SqlAlchemyJobRepository(session).save_cdr(job_id, cdr)
