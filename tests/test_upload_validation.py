import io
import unittest
from PIL import Image
from src.modules.file_upload.adapters.inbound.rest.validation import validate_upload, UploadValidationError


class TestUploadValidation(unittest.TestCase):
    def test_real_png_is_accepted_and_stream_rewound(self):
        stream = io.BytesIO()
        Image.new("RGB", (10, 10), "white").save(stream, format="PNG")
        stream.seek(0)
        self.assertEqual(validate_upload(stream, "receipt.png"), "image/png")
        self.assertEqual(stream.tell(), 0)

    def test_spoofed_png_is_rejected(self):
        with self.assertRaises(UploadValidationError) as caught:
            validate_upload(io.BytesIO(b"not really a png"), "receipt.png")
        self.assertEqual(caught.exception.code, "CORRUPT_DOCUMENT")
