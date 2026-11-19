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
from src.modules.extraction.adapters.outbound.ai.provider_factory import ModelConfig, create_chat_model
from dataclasses import replace


def build_process_job(extractor=None) -> LangGraphProcessor:
    model_config = ModelConfig(
        provider=settings.LLM_PROVIDER,
        model=settings.EXTRACTION_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        ollama_base_url=settings.OLLAMA_BASE_URL,
    )
    chat_model = create_chat_model(model_config) if model_config.ready else None
    vision = None
    if settings.ENABLE_VISION_FALLBACK:
        from src.modules.extraction.adapters.outbound.ai.vision_transcriber import LangChainVisionTranscriber
        vision_provider = settings.VISION_PROVIDER or model_config.provider
        vision_model_name = settings.VISION_MODEL or (model_config.model if vision_provider == model_config.provider else "")
        vision_config = replace(model_config, provider=vision_provider, model=vision_model_name)
        if vision_config.ready:
            vision_model = chat_model if vision_config == model_config else create_chat_model(vision_config)
            vision = LangChainVisionTranscriber(vision_model, vision_config.provider)
    ocr = TesseractOCR(languages=settings.OCR_LANGUAGES, vision=vision, max_pixels=settings.MAX_IMAGE_PIXELS)
    image = ImageReader(ocr)
    docx = DocxReader(ocr)
    pdf = PdfReader(ocr, max_pages=settings.MAX_PDF_PAGES)
    if extractor is None and chat_model is not None:
        from src.modules.extraction.adapters.outbound.ai.langchain_extractor import LangChainExtractor
        extractor = LangChainExtractor(chat_model, model_config.resolved_model)
    return LangGraphProcessor({".jpg": image, ".jpeg": image, ".png": image, ".docx": docx, ".pdf": pdf}, extractor, settings.ARTIFACT_DIR)


def get_submit_extraction(session: Session = Depends(get_db_session)) -> SubmitExtraction:
    return SubmitExtraction(SqlAlchemyFileLookup(session), SqlAlchemyJobRepository(session))


def get_get_extraction(session: Session = Depends(get_db_session)) -> GetExtraction:
    return GetExtraction(SqlAlchemyJobRepository(session))


def get_retry_extraction(session: Session = Depends(get_db_session)) -> RetryExtraction:
    return RetryExtraction(SqlAlchemyJobRepository(session))


def get_get_cdr(session: Session = Depends(get_db_session)) -> GetCDR:
    return GetCDR(SqlAlchemyJobRepository(session), LocalCDRStore(settings.ARTIFACT_DIR))
