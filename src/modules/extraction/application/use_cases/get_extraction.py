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
        if source is None and job.cdr_ref:
            try:
                source = self.artifacts.read(job.cdr_ref)
            except ExtractionError:
                pass
        source_document = source.model_dump(mode="json") if source else None
        text_extraction = None
        if source:
            pages = [{"page_number": number, "text": text} for number, text in source.primary_text_pages()]
            text_extraction = {
                "status": source.reader_status.value.lower(),
                "text": "\n\n".join(page["text"] for page in pages if page["text"]),
                "pages": pages,
            }
        error_messages = {
            "UNSUPPORTED_DOCUMENT_TYPE": "This document is outside the supported invoice, bill, and receipt types.",
            "UNKNOWN_DOCUMENT_TYPE": "Could not confidently identify this document as an invoice, bill, or receipt.",
        }
        error = {"code": job.error_code, "message": error_messages.get(job.error_code, job.error_message)} if job.error_code else None
        return {"job_id": job.id, "file_id": job.file_id, "status": job.status, "stage": job.stage, "configured_extraction_model": job.model_name, "models_used": models_used, "processing_steps": steps, "source_document": source_document, "text_extraction": text_extraction, "result": stored.extracted_json if stored else None, "validation": stored.validation_report if stored else None, "error": error}
