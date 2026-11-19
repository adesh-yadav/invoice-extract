from __future__ import annotations
from pathlib import Path
from io import BytesIO
import pymupdf as fitz
from PIL import Image
from src.modules.extraction.domain.cdr import CDR, Page, ReaderStatus, TextBlock, Table, Warning
from .ocr import TesseractOCR, reader_status


class PdfReader:
    def __init__(self, ocr: TesseractOCR, max_pages: int = 20):
        self.ocr = ocr
        self.max_pages = max_pages

    def read(self, file_id: str, path: Path, content_type: str) -> CDR:
        pages = []
        try:
            with fitz.open(path) as pdf:
                if pdf.needs_pass:
                    return CDR(file_id=file_id, source_format=content_type, reader_status=ReaderStatus.FAILED, warnings=[Warning(code="PASSWORD_PROTECTED_DOCUMENT", severity="high", message="PDF requires a password")])
                if len(pdf) > self.max_pages:
                    raise ValueError("PDF_PAGE_LIMIT")
                for number, source in enumerate(pdf, 1):
                    try:
                        blocks = []
                        for raw in source.get_text("blocks"):
                            if len(raw) > 6 and raw[6] != 0:
                                continue
                            value = raw[4].strip()
                            if not value or not isinstance(value, str):
                                continue
                            box = (raw[0]/source.rect.width, raw[1]/source.rect.height, raw[2]/source.rect.width, raw[3]/source.rect.height)
                            blocks.append(TextBlock(block_id=f"p{number}_b{len(blocks)+1}", text=value, order=len(blocks)+1, bbox=box, source="pdf_native"))
                        meaningful = sum(ch.isalnum() for b in blocks for ch in b.text)
                        image_area = 0.0
                        for image_info in source.get_images(full=True):
                            for rectangle in source.get_image_rects(image_info[0]):
                                image_area += rectangle.width * rectangle.height
                        large_raster = image_area > source.rect.width * source.rect.height * 0.25
                        native_usable = meaningful >= 20
                        if native_usable and not large_raster:
                            page = Page(page_number=number, width=source.rect.width, height=source.rect.height, methods=["pdf_native"], text_blocks=blocks)
                        else:
                            pixels = source.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                            with Image.open(BytesIO(pixels.tobytes("png"))) as image:
                                page = self.ocr.read_page(image, number)
                            if native_usable:
                                extra = []
                                native_text = " ".join(block.text for block in blocks).casefold()
                                for candidate in page.text_blocks:
                                    if candidate.text.casefold() in native_text:
                                        continue
                                    if candidate.bbox and any(self._overlap(candidate.bbox, block.bbox) > 0.5 for block in blocks if block.bbox):
                                        continue
                                    candidate.block_id = f"p{number}_b{len(blocks)+len(extra)+1}"
                                    candidate.order = len(blocks)+len(extra)+1
                                    extra.append(candidate)
                                page.text_blocks = blocks + extra
                                page.methods.insert(0, "pdf_native")
                            elif blocks and not page.text_blocks:
                                page.text_blocks = blocks
                                page.methods.append("pdf_native")
                        if native_usable:
                            try:
                                for index, found in enumerate(source.find_tables().tables, 1):
                                    rows = [[str(cell or "") for cell in row] for row in found.extract()]
                                    page.tables.append(Table(table_id=f"p{number}_t{index}", rows=rows, order=len(page.text_blocks)+index))
                            except Exception:
                                page.warnings.append(Warning(code="TABLE_STRUCTURE_UNAVAILABLE", severity="low", message="PDF table grid could not be recovered"))
                        pages.append(page)
                    except Exception:
                        pages.append(Page(page_number=number, warnings=[Warning(code="PAGE_READ_FAILED", severity="high", message="Page could not be read")]))
            return CDR(file_id=file_id, source_format=content_type, reader_status=reader_status(pages), pages=pages)
        except (ValueError, RuntimeError, OSError, fitz.FileDataError) as exc:
            return CDR(file_id=file_id, source_format=content_type, reader_status=ReaderStatus.FAILED, warnings=[Warning(code="PDF_READ_FAILED", severity="high", message=type(exc).__name__)])

    @staticmethod
    def _overlap(first, second) -> float:
        left, top = max(first[0], second[0]), max(first[1], second[1])
        right, bottom = min(first[2], second[2]), min(first[3], second[3])
        intersection = max(0.0, right-left) * max(0.0, bottom-top)
        area = max(0.0, first[2]-first[0]) * max(0.0, first[3]-first[1])
        return intersection / area if area else 0.0
