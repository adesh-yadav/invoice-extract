from datetime import datetime, timezone
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.infrastructure.database.session import Base
from src.modules.file_upload.adapters.outbound.persistence.models import UploadedFileModel
from src.modules.extraction.adapters.outbound.persistence.models import ExtractionJobModel
from src.modules.extraction.adapters.outbound.persistence.job_repository import SqlAlchemyJobRepository
from src.modules.extraction.domain.processing import ProcessingEvent
from src.modules.extraction.domain.cdr import CDR, Page, ReaderStatus, TextBlock


class TestJobPersistence(unittest.TestCase):
    def test_job_claim_result_and_idempotency(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add(UploadedFileModel(id="f", original_name="receipt.png", stored_name="f.png", file_extension=".png", content_type="image/png", file_size_bytes=10, file_path="/tmp/f.png", status="SUCCESS", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)))
            db.commit()
            repo = SqlAlchemyJobRepository(db)
            job = repo.create("f", "request-a")
            self.assertEqual(repo.create("f", "request-a").id, job.id)
            claimed = repo.claim("test-worker")
            self.assertEqual(claimed.id, job.id)
            repo.record_event(job.id, ProcessingEvent("ocr", "text_recognized", details={"engine": "tesseract"}))
            cdr = CDR(file_id="f", source_format="image/png", reader_status=ReaderStatus.COMPLETE, pages=[Page(page_number=1, text_blocks=[TextBlock(block_id="p1_b1", text="ABC Store", order=1, source="ocr")])])
            repo.save_cdr(job.id, cdr)
            repo.finish(job.id, "completed", {"schema_version": "1.0"}, {"passed": True}, "cdr.json", "receipt", None)
            self.assertEqual(repo.get(job.id).status, "completed")
            self.assertEqual(repo.result(job.id).extracted_json["schema_version"], "1.0")
            self.assertEqual([event["action"] for event in repo.events(job.id)], ["job_queued", "job_claimed", "text_recognized", "job_finished"])
            self.assertEqual(repo.cdr(job.id).pages[0].text_blocks[0].text, "ABC Store")
        engine.dispose()
