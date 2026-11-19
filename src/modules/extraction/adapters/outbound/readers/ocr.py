"""Shared OCR adapter used by images, DOCX media and PDF raster pages."""
from __future__ import annotations
from PIL import Image, ImageOps
import pytesseract
from pytesseract import Output
from src.modules.extraction.domain.cdr import Page, ReaderStatus, TextBlock, Warning


class TesseractOCR:
    def __init__(self, languages: str = "eng", timeout: int = 30, vision=None, max_pixels: int = 40_000_000):
        self.languages = languages
        self.timeout = timeout
        self.vision = vision
        self.max_pixels = max_pixels

    def read_page(self, image: Image.Image, page_number: int) -> Page:
        image = ImageOps.exif_transpose(image)
        if image.width * image.height > self.max_pixels or min(image.size) < 1:
            raise ValueError("IMAGE_PIXEL_LIMIT")
        rgb = image.convert("RGB")
        data = pytesseract.image_to_data(rgb, lang=self.languages, output_type=Output.DICT, timeout=self.timeout)
        groups: dict[tuple[int, int, int], list[int]] = {}
        for i, value in enumerate(data["text"]):
            if value.strip():
                key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
                groups.setdefault(key, []).append(i)
        blocks = []
        for order, indices in enumerate(groups.values(), 1):
            x0 = min(data["left"][i] for i in indices)
            y0 = min(data["top"][i] for i in indices)
            x1 = max(data["left"][i] + data["width"][i] for i in indices)
            y1 = max(data["top"][i] + data["height"][i] for i in indices)
            conf = [float(data["conf"][i]) for i in indices if float(data["conf"][i]) >= 0]
            blocks.append(TextBlock(block_id=f"p{page_number}_b{order}", text=" ".join(data["text"][i].strip() for i in indices), order=order, bbox=(x0/rgb.width, y0/rgb.height, x1/rgb.width, y1/rgb.height), source="ocr", confidence=(sum(conf)/len(conf)/100 if conf else None), confidence_provider="tesseract"))
        page = Page(page_number=page_number, width=rgb.width, height=rgb.height, methods=["ocr"], text_blocks=blocks)
        if not blocks:
            page.warnings.append(Warning(code="NO_TEXT", severity="high", message="OCR found no readable text"))
        elif any(b.confidence is not None and b.confidence < 0.45 for b in blocks):
            page.warnings.append(Warning(code="LOW_OCR_CONFIDENCE", message="Some text is uncertain"))
        uncertain = not blocks or (blocks and sum((b.confidence or 0) for b in blocks)/len(blocks) < 0.45)
        if uncertain and self.vision is not None:
            try:
                transcript = self.vision.transcribe(rgb)
                if transcript:
                    observed = " ".join(b.text for b in blocks).casefold()
                    if not observed:
                        page.text_blocks.append(TextBlock(block_id=f"p{page_number}_b1", text=transcript, order=1, source="vision"))
                    elif transcript.casefold() != observed:
                        page.text_blocks.append(TextBlock(block_id=f"p{page_number}_b{len(blocks)+1}", text=transcript, order=len(blocks)+1, source="vision_candidate"))
                        page.warnings.append(Warning(code="CONFLICTING_READINGS", severity="high", message="OCR and vision transcriptions differ"))
                    page.methods.append("vision")
            except Exception:
                page.warnings.append(Warning(code="VISION_UNAVAILABLE", message="Vision fallback could not run"))
        return page


def reader_status(pages: list[Page]) -> ReaderStatus:
    if not any(p.text_blocks for p in pages):
        return ReaderStatus.FAILED
    if any(p.warnings for p in pages):
        return ReaderStatus.PARTIAL
    return ReaderStatus.COMPLETE
