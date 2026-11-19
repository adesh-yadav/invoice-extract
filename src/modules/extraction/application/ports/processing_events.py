from __future__ import annotations
from typing import Protocol
from src.modules.extraction.domain.processing import ProcessingEvent
from src.modules.extraction.domain.cdr import CDR


class ProcessingEventSink(Protocol):
    def record_event(self, job_id: str, event: ProcessingEvent) -> None: ...
    def save_cdr(self, job_id: str, cdr: CDR) -> None: ...
