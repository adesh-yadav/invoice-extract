from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from PIL import Image
from docx import Document
import pymupdf as fitz
from src.modules.extraction.domain.cdr import CDR, Page, ReaderStatus, TextBlock
from src.modules.extraction.domain.financial import ExtractionPayload, FinancialDocument, Totals, Party, Evidence, validate
from src.modules.extraction.application.use_cases.classify import classify
from src.modules.extraction.adapters.outbound.orchestration.langgraph_processor import LangGraphProcessor
from src.modules.extraction.adapters.outbound.readers.image_reader import ImageReader
from src.modules.extraction.adapters.outbound.readers.docx_reader import DocxReader
from src.modules.extraction.adapters.outbound.readers.pdf_reader import PdfReader
from src.modules.extraction.adapters.outbound.readers.ocr import TesseractOCR


class FakeOCR:
    def read_page(self, image, page_number):
        return Page(page_number=page_number, width=image.width, height=image.height, methods=["ocr"], text_blocks=[TextBlock(block_id=f"p{page_number}_b1", text="ABC Store Receipt Total 100.00", order=1, source="ocr")])


class FakeExtractor:
    def extract(self, cdr, document_type):
        return ExtractionPayload(document=FinancialDocument(document_type=document_type, seller=Party(name="ABC Store"), totals=Totals(grand_total="100.00")), evidence=[Evidence(field_path="document.seller.name", page_number=1, block_ids=["p1_b1"], raw_text="ABC Store"), Evidence(field_path="document.totals.grand_total", page_number=1, block_ids=["p1_b1"], raw_text="Receipt Total 100.00")])


class RepairingExtractor(FakeExtractor):
    def __init__(self):
        self.repairs = 0

    def extract(self, cdr, document_type):
        value = super().extract(cdr, document_type)
        value.document.totals.grand_total = "900.00"
        return value

    def repair(self, cdr, document_type, previous, issues):
        self.repairs += 1
        return super().extract(cdr, document_type)


class TestReaders(unittest.TestCase):
    def test_image_reader_and_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "receipt.png"
            Image.new("RGB", (400, 200), "white").save(path)
            reader = ImageReader(FakeOCR())
            cdr = reader.read("file-1", path, "image/png")
            self.assertEqual(cdr.reader_status, ReaderStatus.COMPLETE)
            self.assertEqual(classify(cdr), "receipt")
            process = LangGraphProcessor({".png": reader}, FakeExtractor(), root / "artifacts")
            state = process.run("job-1", "file-1", str(path), "image/png", ".png")
            self.assertEqual(state["status"], "completed")
            self.assertTrue(Path(state["cdr_ref"]).is_file())

    def test_docx_preserves_paragraph_table_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invoice.docx"
            doc = Document()
            doc.add_paragraph("Invoice")
            table = doc.add_table(rows=1, cols=2)
            table.cell(0, 0).text = "Item"
            table.cell(0, 1).text = "Amount"
            doc.add_paragraph("Total 100")
            doc.save(path)
            cdr = DocxReader(FakeOCR()).read("file-2", path, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self.assertEqual(cdr.reader_status, ReaderStatus.COMPLETE)
            self.assertEqual([b.text for b in cdr.pages[0].text_blocks], ["Invoice", "Item | Amount", "Total 100"])
            self.assertEqual(cdr.pages[0].tables[0].rows[0], ["Item", "Amount"])

    def test_graph_repairs_wrong_total_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "receipt.png"
            Image.new("RGB", (400, 200), "white").save(path)
            extractor = RepairingExtractor()
            process = LangGraphProcessor({".png": ImageReader(FakeOCR())}, extractor, root / "artifacts")
            state = process.run("job-2", "file-1", str(path), "image/png", ".png")
            self.assertEqual(state["status"], "completed")
            self.assertEqual(state["repair_count"], 1)
            self.assertEqual(extractor.repairs, 1)

    def test_pdf_native_and_scanned_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mixed.pdf"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((30, 50), "Invoice number INV-1 Total amount 100.00")
            doc.new_page()
            doc.save(path)
            cdr = PdfReader(FakeOCR()).read("file-3", path, "application/pdf")
            self.assertEqual(len(cdr.pages), 2)
            self.assertEqual(cdr.pages[0].methods, ["pdf_native"])
            self.assertEqual(cdr.pages[1].methods, ["ocr"])

    def test_validation_detects_missing_evidence_and_total_mismatch(self):
        cdr = CDR(file_id="f", source_format="image/png", reader_status=ReaderStatus.COMPLETE, pages=[Page(page_number=1, text_blocks=[TextBlock(block_id="p1_b1", text="Total 100", order=1, source="ocr")])])
        payload = ExtractionPayload(document=FinancialDocument(document_type="invoice", totals=Totals(subtotal="80", tax_total="10", grand_total="100")))
        codes = {issue.code for issue in validate(payload, cdr)}
        self.assertTrue({"MISSING_TOTAL_EVIDENCE", "TOTAL_MISMATCH", "MISSING_SELLER", "MISSING_INVOICE_NUMBER"} <= codes)

    def test_evidence_paths_from_model_are_canonicalized(self):
        self.assertEqual(Evidence(field_path="seller.name", page_number=1, block_ids=["p1_b1"], raw_text="ABC Store").field_path, "document.seller.name")
        self.assertEqual(Evidence(field_path="line_items[0].amount", page_number=1, block_ids=["p1_b1"], raw_text="100").field_path, "document.line_items.0.amount")

    @patch("src.modules.extraction.adapters.outbound.readers.ocr.pytesseract.image_to_data")
    def test_low_confidence_cleanup_preserves_raw_ocr(self, image_to_data):
        image_to_data.return_value = {"text": ["Tota1", "100.00"], "block_num": [1, 1], "par_num": [1, 1], "line_num": [1, 1], "left": [1, 40], "top": [1, 1], "width": [35, 40], "height": [10, 10], "conf": [20, 20]}
        cleaner = Mock()
        cleaner.clean.return_value = "Total 100.00"
        page = TesseractOCR(cleaner=cleaner).read_page(Image.new("RGB", (100, 30), "white"), 1)
        self.assertEqual([block.source for block in page.text_blocks], ["ocr", "ocr_cleanup_candidate"])
        self.assertEqual(page.text_blocks[0].text, "Tota1 100.00")
        self.assertEqual(page.text_blocks[1].text, "Total 100.00")
        self.assertIn("ocr_cleanup", page.methods)
        self.assertIn("OCR_CLEANUP_CANDIDATE", [warning.code for warning in page.warnings])


if __name__ == "__main__":
    unittest.main()
