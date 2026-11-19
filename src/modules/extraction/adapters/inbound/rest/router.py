"""HTTP adapter translating requests into application use cases."""
from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from src.modules.extraction.config.module import get_submit_extraction, get_get_extraction, get_retry_extraction, get_get_cdr
from src.modules.extraction.application.use_cases.submit_extraction import SubmitExtraction
from src.modules.extraction.application.use_cases.get_extraction import GetExtraction
from src.modules.extraction.application.use_cases.retry_extraction import RetryExtraction
from src.modules.extraction.application.use_cases.get_cdr import GetCDR
from src.modules.extraction.domain.cdr import CDR
from src.modules.extraction.domain.exceptions import ExtractionError

router = APIRouter(prefix="/v1/extractions", tags=["extractions"])


class Options(BaseModel):
    document_type_hint: str | None = None
    ocr_language_hints: list[str] = Field(default_factory=lambda: ["eng"])
    output_schema_version: str = "1.0"


class CreateRequest(BaseModel):
    file_id: str
    options: Options = Field(default_factory=Options)


def respond(call):
    try:
        return call()
    except ExtractionError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_extraction(request: CreateRequest, idempotency_key: str | None = Header(None, alias="Idempotency-Key"), use_case: SubmitExtraction = Depends(get_submit_extraction)):
    if request.options.output_schema_version != "1.0":
        raise HTTPException(422, "UNSUPPORTED_SCHEMA_VERSION")
    return respond(lambda: use_case.handle(request.file_id, idempotency_key))


@router.get("/{job_id}")
def get_extraction(job_id: str, use_case: GetExtraction = Depends(get_get_extraction)):
    return respond(lambda: use_case.handle(job_id))


@router.get("/{job_id}/cdr", response_model=CDR)
def get_cdr(job_id: str, use_case: GetCDR = Depends(get_get_cdr)):
    return respond(lambda: use_case.handle(job_id))


@router.post("/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_extraction(job_id: str, use_case: RetryExtraction = Depends(get_retry_extraction)):
    return respond(lambda: use_case.handle(job_id))
