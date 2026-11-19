from src.modules.extraction.application.ports.file_lookup import FileLookup
from src.modules.extraction.application.ports.job_repository import JobRepository
from src.modules.extraction.domain.exceptions import ExtractionError


class SubmitExtraction:
    def __init__(self, files: FileLookup, jobs: JobRepository):
        self.files = files
        self.jobs = jobs

    def handle(self, file_id: str, idempotency_key: str | None = None) -> dict:
        file = self.files.get(file_id)
        if file is None:
            raise ExtractionError("FILE_NOT_FOUND", 404)
        if file.status != "SUCCESS":
            raise ExtractionError("FILE_NOT_READY", 409)
        if file.extension.lower() not in {".jpg", ".jpeg", ".png", ".docx", ".pdf"}:
            raise ExtractionError("UNSUPPORTED_FILE_TYPE", 415)
        try:
            job = self.jobs.create(file_id, idempotency_key)
        except ValueError:
            raise ExtractionError("IDEMPOTENCY_CONFLICT", 409)
        return {"job_id": job.id, "file_id": job.file_id, "status": job.status, "status_url": f"/v1/extractions/{job.id}"}
