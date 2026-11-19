from src.modules.extraction.application.ports.job_repository import JobRepository
from src.modules.extraction.application.ports.artifact_store import CDRStore
from src.modules.extraction.domain.cdr import CDR
from src.modules.extraction.domain.exceptions import ExtractionError


class GetCDR:
    def __init__(self, jobs: JobRepository, artifacts: CDRStore):
        self.jobs = jobs
        self.artifacts = artifacts

    def handle(self, job_id: str) -> CDR:
        job = self.jobs.get(job_id)
        if job is None:
            raise ExtractionError("JOB_NOT_FOUND", 404)
        if not job.cdr_ref:
            raise ExtractionError("CDR_NOT_READY", 409)
        return self.artifacts.read(job.cdr_ref)
