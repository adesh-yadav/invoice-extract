import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel


class Settings(BaseModel):
    APP_NAME: str = "Invoice Extract API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/invoice_db",
    )
    
    # Upload storage directory
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
    ARTIFACT_DIR: Path = Path(os.getenv("ARTIFACT_DIR", "/app/artifacts"))
    LLM_PROVIDER: Literal["openai", "anthropic", "ollama"] = os.getenv("LLM_PROVIDER", "openai").lower()
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    EXTRACTION_MODEL: str = os.getenv("EXTRACTION_MODEL", "")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "")
    ENABLE_VISION_FALLBACK: bool = os.getenv("ENABLE_VISION_FALLBACK", "true").lower() == "true"
    OCR_LANGUAGES: str = os.getenv("OCR_LANGUAGES", "eng")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")

    # Max upload file size in bytes (e.g., 25 MB)
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_FILE_SIZE_BYTES", 25 * 1024 * 1024))
    MAX_PDF_PAGES: int = int(os.getenv("MAX_PDF_PAGES", 20))
    MAX_IMAGE_PIXELS: int = int(os.getenv("MAX_IMAGE_PIXELS", 40_000_000))


settings = Settings()
