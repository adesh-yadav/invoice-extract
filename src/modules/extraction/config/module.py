from __future__ import annotations
from src.core.config import settings
from fastapi import Depends
from sqlalchemy.orm import Session
from src.infrastructure.database.session import get_db_session
from src.modules.extraction.adapters.outbound.persistence.job_repository import SqlAlchemyJobRepository
from src.modules.extraction.adapters.outbound.persistence.file_lookup import SqlAlchemyFileLookup
from src.modules.extraction.adapters.outbound.persistence.cdr_store import LocalCDRStore
from src.modules.extraction.application.use_cases.submit_extraction import SubmitExtraction
from src.modules.extraction.application.use_cases.get_extraction import GetExtraction
from src.modules.extraction.application.use_cases.retry_extraction import RetryExtraction
from src.modules.extraction.application.use_cases.get_cdr import GetCDR
from src.modules.extraction.adapters.outbound.readers.ocr import TesseractOCR
from src.modules.extraction.adapters.outbound.readers.image_reader import ImageReader
from src.modules.extraction.adapters.outbound.readers.docx_reader import DocxReader
from src.modules.extraction.adapters.outbound.readers.pdf_reader import PdfReader
from src.modules.extraction.adapters.outbound.orchestration.langgraph_processor import LangGraphProcessor


def build_process_job(extractor=None) -> LangGraphProcessor:
    vision = None
    if settings.OPENAI_API_KEY:
        from src.modules.extraction.adapters.outbound.ai.vision_transcriber import LangChainVisionTranscriber
        vision = LangChainVisionTranscriber(settings.EXTRACTION_MODEL)
    ocr = TesseractOCR(languages=settings.OCR_LANGUAGES, vision=vision, max_pixels=settings.MAX_IMAGE_PIXELS)
    image = ImageReader(ocr)
    docx = DocxReader(ocr)
    pdf = PdfReader(ocr, max_pages=settings.MAX_PDF_PAGES)
    if extractor is None and settings.OPENAI_API_KEY:
        from src.modules.extraction.adapters.outbound.ai.langchain_extractor import LangChainExtractor
        extractor = LangChainExtractor(settings.EXTRACTION_MODEL)
    return LangGraphProcessor({".jpg": image, ".jpeg": image, ".png": image, ".docx": docx, ".pdf": pdf}, extractor, settings.ARTIFACT_DIR)


def get_submit_extraction(session: Session = Depends(get_db_session)) -> SubmitExtraction:
    return SubmitExtraction(SqlAlchemyFileLookup(session), SqlAlchemyJobRepository(session))


def get_get_extraction(session: Session = Depends(get_db_session)) -> GetExtraction:
    return GetExtraction(SqlAlchemyJobRepository(session))


def get_retry_extraction(session: Session = Depends(get_db_session)) -> RetryExtraction:
    return RetryExtraction(SqlAlchemyJobRepository(session))


def get_get_cdr(session: Session = Depends(get_db_session)) -> GetCDR:
    return GetCDR(SqlAlchemyJobRepository(session), LocalCDRStore(settings.ARTIFACT_DIR))
