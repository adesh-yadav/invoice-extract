import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from src.modules.extraction.application.use_cases.get_extraction import GetExtraction
from src.modules.extraction.application.use_cases.get_cdr import GetCDR
from src.modules.extraction.domain.cdr import CDR, Page, ReaderStatus, TextBlock


class TestProcessingTrace(unittest.TestCase):
    def test_unsupported_document_response_explains_scope(self):
        jobs = Mock()
        jobs.get.return_value = SimpleNamespace(id="pan-job", file_id="pan-file", status="unsupported", stage="done", model_name="anthropic:configured", cdr_ref=None, error_code="UNSUPPORTED_DOCUMENT_TYPE", error_message="UNSUPPORTED_DOCUMENT_TYPE")
        jobs.result.return_value = None
        jobs.events.return_value = []
        jobs.cdr.return_value = CDR(file_id="pan-file", source_format="image/jpeg", reader_status=ReaderStatus.PARTIAL, pages=[Page(page_number=1, methods=["ocr"], text_blocks=[TextBlock(block_id="p1_b1", text="PERMANENT ACCOUNT NUMBER", order=1, source="ocr")])])
        response = GetExtraction(jobs, Mock()).handle("pan-job")
        self.assertEqual(response["status"], "unsupported")
        self.assertEqual(response["models_used"], [])
        self.assertIn("invoice, bill, and receipt", response["error"]["message"])
        self.assertEqual(response["text_extraction"]["status"], "partial")
        self.assertEqual(response["text_extraction"]["text"], "PERMANENT ACCOUNT NUMBER")
        self.assertEqual(response["text_extraction"]["pages"], [{"page_number": 1, "text": "PERMANENT ACCOUNT NUMBER"}])

    def test_job_response_exposes_ordered_steps_models_and_source_text(self):
        jobs = Mock()
        jobs.get.return_value = SimpleNamespace(id="job-1", file_id="file-1", status="completed", stage="done", model_name="anthropic:claude-haiku-4-5-20251001", cdr_ref="cdr-ref", error_code=None)
        jobs.result.return_value = SimpleNamespace(extracted_json={"document": {"document_type": "receipt"}}, validation_report={"passed": True})
        jobs.events.return_value = [
            {"sequence": 1, "phase": "reading", "action": "embedded_text_extracted", "status": "completed", "details": {"page_number": 1}, "at": "2026-11-19T00:00:00Z"},
            {"sequence": 2, "phase": "extraction", "action": "fields_extracted", "status": "completed", "details": {"provider": "anthropic", "model": "claude-haiku-4-5-20251001"}, "at": "2026-11-19T00:00:01Z"},
        ]
        artifacts = Mock()
        jobs.cdr.return_value = CDR(file_id="file-1", source_format="application/pdf", reader_status=ReaderStatus.COMPLETE, pages=[Page(page_number=1, methods=["pdf_native"], text_blocks=[TextBlock(block_id="p1_b1", text="ABC Store", order=1, source="pdf_native")])])

        response = GetExtraction(jobs, artifacts).handle("job-1")

        self.assertEqual(response["processing_steps"][0]["action"], "embedded_text_extracted")
        self.assertEqual(response["models_used"], [{"role": "extraction", "provider": "anthropic", "model": "claude-haiku-4-5-20251001"}])
        self.assertEqual(response["source_document"]["pages"][0]["text_blocks"][0]["text"], "ABC Store")
        self.assertEqual(response["text_extraction"]["text"], "ABC Store")
        self.assertEqual(GetCDR(jobs, artifacts).handle("job-1").pages[0].text_blocks[0].text, "ABC Store")
        artifacts.read.assert_not_called()
