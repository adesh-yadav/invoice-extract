import io
import unittest
from unittest.mock import MagicMock

from src.modules.file_upload.domain.exceptions import (
    InvalidFileNameError,
    InvalidStatusTransitionError,
)
from src.modules.file_upload.domain.model.upload_status import UploadStatus
from src.modules.file_upload.domain.model.uploaded_file import UploadedFile
from src.modules.file_upload.application.dto.commands import UploadFileInput
from src.modules.file_upload.application.use_cases.upload_file import UploadFile


class TestFileUploadHexagonal(unittest.TestCase):

    def test_entity_initial_status_is_pending_with_path(self):
        entity = UploadedFile(
            original_name="invoice_march.pdf",
            content_type="application/pdf",
            file_path="/app/uploads/uuid.pdf",
        )
        self.assertEqual(entity.status, UploadStatus.PENDING)
        self.assertEqual(entity.file_path, "/app/uploads/uuid.pdf")
        self.assertEqual(entity.file_extension, ".pdf")
        self.assertEqual(entity.file_size_bytes, 0)
        self.assertIsNone(entity.error_message)
        # Ensure stored_name is uuid.ext and not original filename to prevent collisions
        self.assertTrue(entity.stored_name.endswith(".pdf"))
        self.assertNotEqual(entity.stored_name, "invoice_march.pdf")

    def test_entity_empty_name_raises(self):
        with self.assertRaises(InvalidFileNameError):
            UploadedFile(
                original_name="   ",
                content_type="application/pdf",
                file_path="/app/uploads/file.pdf",
            )

    def test_entity_empty_path_raises(self):
        with self.assertRaises(ValueError):
            UploadedFile(
                original_name="valid.pdf",
                content_type="application/pdf",
                file_path="",
            )

    def test_entity_mark_as_success(self):
        entity = UploadedFile(
            original_name="bill.png",
            content_type="image/png",
            file_path="/app/uploads/bill.png",
        )
        entity.mark_as_success(file_size_bytes=2048)
        self.assertEqual(entity.status, UploadStatus.SUCCESS)
        self.assertEqual(entity.file_path, "/app/uploads/bill.png")
        self.assertEqual(entity.file_size_bytes, 2048)

    def test_entity_invalid_status_transition(self):
        entity = UploadedFile(
            original_name="bill.png",
            content_type="image/png",
            file_path="/app/uploads/bill.png",
        )
        entity.mark_as_success(file_size_bytes=2048)

        # Cannot transition to SUCCESS again
        with self.assertRaises(InvalidStatusTransitionError):
            entity.mark_as_success(file_size_bytes=2048)

        # Cannot transition to FAILED after SUCCESS
        with self.assertRaises(InvalidStatusTransitionError):
            entity.mark_as_failed(error_message="some error")

    def test_upload_file_use_case_pre_records_path_in_pending_status(self):
        mock_repo = MagicMock()
        mock_storage = MagicMock()

        # Capture entity status at the moment save() is called
        save_status_snapshot = {}

        def record_save_snapshot(entity):
            save_status_snapshot["status"] = entity.status
            save_status_snapshot["file_path"] = entity.file_path
            save_status_snapshot["stored_name"] = entity.stored_name
            return entity

        mock_repo.save.side_effect = record_save_snapshot

        # Mock storage behavior
        mock_storage.build_destination_path.side_effect = lambda filename: f"/app/uploads/{filename}"
        mock_storage.save_to_path.return_value = 4096

        use_case = UploadFile(repository=mock_repo, storage=mock_storage)

        fake_stream = io.BytesIO(b"invoice dummy bytes")
        request = UploadFileInput(
            filename="vendor_bill.pdf",
            content_type="application/pdf",
            file_stream=fake_stream,
        )

        view = use_case.handle(request)

        # 1. Verify build_destination_path was called
        mock_storage.build_destination_path.assert_called_once()

        # 2. Check snapshot when repo.save() was called: Status MUST BE PENDING and path already set
        self.assertEqual(save_status_snapshot["status"], UploadStatus.PENDING)
        self.assertTrue(save_status_snapshot["file_path"].startswith("/app/uploads/"))
        self.assertTrue(save_status_snapshot["file_path"].endswith(".pdf"))
        # Verify stored_name is UUID.ext and NOT the original filename!
        self.assertNotEqual(save_status_snapshot["stored_name"], "vendor_bill.pdf")
        self.assertTrue(save_status_snapshot["stored_name"].endswith(".pdf"))

        # 3. Verify storage wrote to the exact target path
        mock_storage.save_to_path.assert_called_once_with(
            file_content=fake_stream,
            destination_path=save_status_snapshot["file_path"],
        )

        # 4. Verify repo.update() was called with SUCCESS status
        self.assertEqual(mock_repo.update.call_count, 1)
        updated_entity = mock_repo.update.call_args[0][0]
        self.assertEqual(updated_entity.status, UploadStatus.SUCCESS)
        self.assertEqual(updated_entity.file_size_bytes, 4096)

        # 5. Verify final output view
        self.assertEqual(view.status, "SUCCESS")
        self.assertEqual(view.original_name, "vendor_bill.pdf")
        self.assertNotEqual(view.stored_name, "vendor_bill.pdf")
        self.assertTrue(view.stored_name.endswith(".pdf"))
        self.assertEqual(view.file_path, save_status_snapshot["file_path"])
        self.assertEqual(view.file_size_bytes, 4096)

    def test_upload_file_use_case_failure_flow(self):
        mock_repo = MagicMock()
        mock_storage = MagicMock()

        save_status_snapshot = {}

        def record_save_snapshot(entity):
            save_status_snapshot["status"] = entity.status
            save_status_snapshot["file_path"] = entity.file_path
            return entity

        mock_repo.save.side_effect = record_save_snapshot

        mock_storage.build_destination_path.side_effect = lambda filename: f"/app/uploads/{filename}"
        mock_storage.save_to_path.side_effect = IOError("Disk full")

        use_case = UploadFile(repository=mock_repo, storage=mock_storage)

        fake_stream = io.BytesIO(b"corrupt content")
        request = UploadFileInput(
            filename="corrupt.pdf",
            content_type="application/pdf",
            file_stream=fake_stream,
        )

        with self.assertRaises(RuntimeError) as ctx:
            use_case.handle(request)

        self.assertIn("Disk full", str(ctx.exception))

        # Verify initial repo.save() had PENDING and file_path set
        self.assertEqual(save_status_snapshot["status"], UploadStatus.PENDING)
        self.assertTrue(save_status_snapshot["file_path"].endswith(".pdf"))

        # Verify repo.update() recorded FAILED status
        self.assertEqual(mock_repo.update.call_count, 1)
        updated_entity = mock_repo.update.call_args[0][0]
        self.assertEqual(updated_entity.status, UploadStatus.FAILED)
        self.assertIn("Disk full", updated_entity.error_message)


if __name__ == "__main__":
    unittest.main()
