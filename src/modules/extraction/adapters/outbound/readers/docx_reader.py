from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from io import BytesIO
from PIL import Image
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.ns import qn
from src.modules.extraction.domain.cdr import CDR, Page, Table, TextBlock, Warning
from .ocr import TesseractOCR, reader_status


class DocxReader:
    def __init__(self, ocr: TesseractOCR):
        self.ocr = ocr

    def read(self, file_id: str, path: Path, content_type: str) -> CDR:
        try:
            with ZipFile(path) as archive:
                info = archive.infolist()
                if len(info) > 1000 or sum(i.file_size for i in info) > 100_000_000 or any(i.file_size > 40_000_000 for i in info):
                    raise ValueError("DOCX_RESOURCE_LIMIT")
                names = {i.filename for i in info}
                if "word/document.xml" not in names or "[Content_Types].xml" not in names:
                    raise ValueError("INVALID_DOCX")
            doc = Document(path)
            page = Page(page_number=1, methods=["docx_native"])
            order = 0
            for child in doc.element.body.iterchildren():
                if child.tag == qn("w:p"):
                    from docx.text.paragraph import Paragraph
                    value = Paragraph(child, doc).text.strip()
                    if value:
                        order += 1
                        page.text_blocks.append(TextBlock(block_id=f"p1_b{order}", text=value, order=order, kind="paragraph", source="docx_native"))
                elif child.tag == qn("w:tbl"):
                    from docx.table import Table as DocxTable
                    table = DocxTable(child, doc)
                    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
                    order += 1
                    page.tables.append(Table(table_id=f"p1_t{len(page.tables)+1}", rows=rows, order=order))
                    for row in rows:
                        if any(row):
                            order += 1
                            page.text_blocks.append(TextBlock(block_id=f"p1_b{order}", text=" | ".join(row), order=order, kind="table_row", source="docx_native"))
            for section in doc.sections:
                for part in (section.header, section.footer):
                    for paragraph in part.paragraphs:
                        if paragraph.text.strip():
                            order += 1
                            page.text_blocks.append(TextBlock(block_id=f"p1_b{order}", text=paragraph.text.strip(), order=order, kind="header" if part == section.header else "footer", source="docx_native"))
            for rel in doc.part.rels.values():
                if "image" not in rel.reltype or rel.is_external:
                    continue
                try:
                    with Image.open(BytesIO(rel.target_part.blob)) as image:
                        media_page = self.ocr.read_page(image, 1)
                    for block in media_page.text_blocks:
                        order += 1
                        block.block_id = f"p1_b{order}"
                        block.order = order
                        block.bbox = None
                        page.text_blocks.append(block)
                    page.methods.append("embedded_image_ocr")
                except Exception:
                    page.warnings.append(Warning(code="EMBEDDED_IMAGE_UNREADABLE", message="Embedded image could not be read"))
            return CDR(file_id=file_id, source_format=content_type, reader_status=reader_status([page]), pages=[page])
        except (BadZipFile, ValueError, OSError, KeyError, PackageNotFoundError) as exc:
            from src.modules.extraction.domain.cdr import ReaderStatus
            return CDR(file_id=file_id, source_format=content_type, reader_status=ReaderStatus.FAILED, warnings=[Warning(code="DOCX_READ_FAILED", severity="high", message=type(exc).__name__)])
