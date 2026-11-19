import io
import tempfile
import unittest
from pathlib import Path
from src.modules.file_upload.adapters.outbound.storage.local_storage import LocalDiskFileStorage


class TestLocalStorage(unittest.TestCase):
    def test_atomic_write_creates_only_final_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = LocalDiskFileStorage(Path(tmp))
            target = storage.build_destination_path("file.png")
            size = storage.save_to_path(io.BytesIO(b"complete"), target)
            self.assertEqual(size, 8)
            self.assertEqual(Path(target).read_bytes(), b"complete")
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["file.png"])

    def test_rejects_path_outside_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = LocalDiskFileStorage(Path(tmp))
            with self.assertRaises(ValueError):
                storage.save_to_path(io.BytesIO(b"x"), "/tmp/not-upload-root.png")
