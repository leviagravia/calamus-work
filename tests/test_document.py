import os
import tempfile
import unittest

import calamus_document as doc


class DocumentTests(unittest.TestCase):
    def test_write_and_read_utf8(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "note.txt")
            text = "Caffè\nseconda riga"
            doc.write_text_file(path, text)
            self.assertEqual(doc.read_text_file(path), text)

    def test_large_file_detection(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "big.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("x" * 16)
            self.assertTrue(doc.is_large_text_file(path, threshold=10))
            self.assertFalse(doc.is_large_text_file(path, threshold=20))
            self.assertFalse(doc.is_large_text_file(os.path.join(td, "missing"), threshold=1))


if __name__ == "__main__":
    unittest.main()
