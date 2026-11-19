from src.modules.extraction.application.ports.job_repository import JobRepository
from src.modules.extraction.domain.exceptions import ExtractionError


class RetryExtraction:
    def __init__(self, jobs: JobRepository):
        self.jobs = jobs

    def handle(self, job_id: str) -> dict:
        old = self.jobs.get(job_id)
        if old is None:
            raise ExtractionError("JOB_NOT_FOUND", 404)
        if old.status not in {"failed", "needs_review"}:
            raise ExtractionError("JOB_NOT_RETRYABLE", 409)
        job = self.jobs.create(old.file_id)
        return {"job_id": job.id, "file_id": job.file_id, "status": job.status, "status_url": f"/v1/extractions/{job.id}"}
