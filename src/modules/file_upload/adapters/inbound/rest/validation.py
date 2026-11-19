"""Validate untrusted upload bytes before the existing upload use case persists them."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import pymupdf as fitz
from PIL import Image, UnidentifiedImageError
from src.core.config import settings


class UploadValidationError(ValueError):
    def __init__(self, code: str, http_status: int):
        super().__init__(code)
        self.code = code
        self.http_status = http_status


def validate_upload(stream, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    known = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if extension not in known:
        raise UploadValidationError("UNSUPPORTED_FILE_TYPE", 415)
    data = stream.read(settings.MAX_FILE_SIZE_BYTES + 1)
    stream.seek(0)
    if not data or len(data) > settings.MAX_FILE_SIZE_BYTES:
        raise UploadValidationError("FILE_SIZE_LIMIT", 413)
    try:
        if extension in {".jpg", ".jpeg", ".png"}:
            with Image.open(BytesIO(data)) as image:
                if image.format != ("PNG" if extension == ".png" else "JPEG") or image.width * image.height > settings.MAX_IMAGE_PIXELS:
                    raise UploadValidationError("INVALID_IMAGE", 422)
                image.verify()
        elif extension == ".pdf":
            with fitz.open(stream=data, filetype="pdf") as pdf:
                if pdf.needs_pass:
                    raise UploadValidationError("PASSWORD_PROTECTED_DOCUMENT", 422)
                if len(pdf) > settings.MAX_PDF_PAGES:
                    raise UploadValidationError("PDF_PAGE_LIMIT", 422)
        else:
            with ZipFile(BytesIO(data)) as archive:
                parts = archive.infolist()
                names = {part.filename for part in parts}
                if "word/document.xml" not in names or "[Content_Types].xml" not in names:
                    raise UploadValidationError("INVALID_DOCX", 422)
                if len(parts) > 1000 or sum(part.file_size for part in parts) > 100_000_000 or any(part.file_size > 40_000_000 for part in parts):
                    raise UploadValidationError("DOCX_RESOURCE_LIMIT", 422)
    except UploadValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, BadZipFile, fitz.FileDataError):
        raise UploadValidationError("CORRUPT_DOCUMENT", 422)
    return known[extension]
