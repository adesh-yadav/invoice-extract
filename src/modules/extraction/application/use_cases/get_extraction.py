from src.modules.extraction.application.ports.job_repository import JobRepository
from src.modules.extraction.domain.exceptions import ExtractionError


class GetExtraction:
    def __init__(self, jobs: JobRepository):
        self.jobs = jobs

    def handle(self, job_id: str) -> dict:
        job = self.jobs.get(job_id)
        if job is None:
            raise ExtractionError("JOB_NOT_FOUND", 404)
        stored = self.jobs.result(job_id)
        return {"job_id": job.id, "file_id": job.file_id, "status": job.status, "stage": job.stage, "result": stored.extracted_json if stored else None, "validation": stored.validation_report if stored else None, "error": {"code": job.error_code, "message": job.error_message} if job.error_code else None}
