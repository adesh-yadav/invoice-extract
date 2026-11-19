"""Extraction job lifecycle invariants, separate from upload status."""
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"
    CANCELLED = "cancelled"


_ALLOWED = {
    JobStatus.QUEUED: {JobStatus.PROCESSING, JobStatus.CANCELLED},
    JobStatus.PROCESSING: {JobStatus.COMPLETED, JobStatus.NEEDS_REVIEW, JobStatus.UNSUPPORTED, JobStatus.FAILED, JobStatus.PROCESSING},
}


def ensure_transition(current: str, target: str) -> None:
    source = JobStatus(current)
    destination = JobStatus(target)
    if destination not in _ALLOWED.get(source, set()):
        raise ValueError(f"Invalid extraction job transition: {source.value} -> {destination.value}")
