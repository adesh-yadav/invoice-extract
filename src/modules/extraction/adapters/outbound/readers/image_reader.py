from __future__ import annotations
from pathlib import Path
from PIL import Image
from src.modules.extraction.domain.cdr import CDR, ReaderStatus, Warning
from .ocr import TesseractOCR, reader_status


class ImageReader:
    def __init__(self, ocr: TesseractOCR):
        self.ocr = ocr

    def read(self, file_id: str, path: Path, content_type: str) -> CDR:
        try:
            with Image.open(path) as image:
                if image.format not in {"JPEG", "PNG"}:
                    raise ValueError("UNSUPPORTED_FILE_TYPE")
                page = self.ocr.read_page(image, 1)
            return CDR(file_id=file_id, source_format=content_type, reader_status=reader_status([page]), pages=[page])
        except Exception as exc:
            return CDR(file_id=file_id, source_format=content_type, reader_status=ReaderStatus.FAILED, warnings=[Warning(code="IMAGE_READ_FAILED", severity="high", message=type(exc).__name__)])
