import unittest
from unittest.mock import Mock
from src.modules.extraction.domain.stored_file import StoredFile
from src.modules.extraction.domain.exceptions import ExtractionError
from src.modules.extraction.application.use_cases.submit_extraction import SubmitExtraction
from src.modules.extraction.application.use_cases.retry_extraction import RetryExtraction
from src.modules.extraction.domain.job import ensure_transition


class TestExtractionUseCases(unittest.TestCase):
    def test_job_lifecycle_rejects_terminal_transition(self):
        ensure_transition("queued", "processing")
        ensure_transition("processing", "needs_review")
        with self.assertRaises(ValueError):
            ensure_transition("completed", "processing")

    def test_submit_requires_stored_file(self):
        files, jobs = Mock(), Mock()
        files.get.return_value = StoredFile("f", "PENDING", ".png")
        with self.assertRaises(ExtractionError) as caught:
            SubmitExtraction(files, jobs).handle("f")
        self.assertEqual(caught.exception.code, "FILE_NOT_READY")
        jobs.create.assert_not_called()

    def test_submit_reuses_idempotent_job(self):
        files, jobs = Mock(), Mock()
        files.get.return_value = StoredFile("f", "SUCCESS", ".png")
        jobs.create.return_value = Mock(id="j", file_id="f", status="queued")
        result = SubmitExtraction(files, jobs).handle("f", "request-1")
        self.assertEqual(result["job_id"], "j")
        jobs.create.assert_called_once_with("f", "request-1")

    def test_retry_creates_new_job_only_after_terminal_failure(self):
        jobs = Mock()
        jobs.get.return_value = Mock(file_id="f", status="processing")
        with self.assertRaises(ExtractionError):
            RetryExtraction(jobs).handle("j")
        jobs.create.assert_not_called()
        jobs.get.return_value.status = "failed"
        jobs.create.return_value = Mock(id="new", file_id="f", status="queued")
        self.assertEqual(RetryExtraction(jobs).handle("j")["job_id"], "new")
