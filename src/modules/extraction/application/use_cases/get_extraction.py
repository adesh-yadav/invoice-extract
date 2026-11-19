from src.modules.extraction.application.ports.job_repository import JobRepository
from src.modules.extraction.application.ports.artifact_store import CDRStore
from src.modules.extraction.domain.exceptions import ExtractionError


class GetExtraction:
    def __init__(self, jobs: JobRepository, artifacts: CDRStore):
        self.jobs = jobs
        self.artifacts = artifacts

    def handle(self, job_id: str) -> dict:
        job = self.jobs.get(job_id)
        if job is None:
            raise ExtractionError("JOB_NOT_FOUND", 404)
        stored = self.jobs.result(job_id)
        steps = self.jobs.events(job_id)
        models_used = []
        actions = {"fields_extracted": "extraction", "image_transcribed": "vision", "text_corrected": "ocr_cleanup", "fields_rechecked": "repair"}
        for step in steps:
            role = actions.get(step["action"])
            details = step["details"]
            if role and step["status"] == "completed" and details.get("provider") and details.get("model"):
                usage = {"role": role, "provider": details["provider"], "model": details["model"]}
                if usage not in models_used:
                    models_used.append(usage)
        source = self.jobs.cdr(job_id)
        source_document = source.model_dump(mode="json") if source else None
        if source_document is None and job.cdr_ref:
            try:
                source_document = self.artifacts.read(job.cdr_ref).model_dump(mode="json")
            except ExtractionError:
                pass
        return {"job_id": job.id, "file_id": job.file_id, "status": job.status, "stage": job.stage, "configured_extraction_model": job.model_name, "models_used": models_used, "processing_steps": steps, "source_document": source_document, "result": stored.extracted_json if stored else None, "validation": stored.validation_report if stored else None, "error": {"code": job.error_code, "message": job.error_message} if job.error_code else None}
