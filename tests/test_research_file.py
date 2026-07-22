import os
import tempfile
import unittest
from pathlib import Path

from calamus_research_file import FileToken, atomic_write_utf8, file_token


class ResearchFileTests(unittest.TestCase):
    def test_file_token_and_atomic_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "research", "sample.md")
            self.assertEqual(file_token(path), FileToken(False))
            saved = atomic_write_utf8(path, "alpha\n")
            self.assertTrue(saved.exists)
            self.assertEqual(Path(path).read_text(encoding="utf-8"), "alpha\n")
            self.assertFalse(os.path.exists(path + ".tmp"))
            self.assertEqual(saved, file_token(path))

    def test_atomic_write_rejects_invalid_input(self):
        with self.assertRaises(ValueError):
            atomic_write_utf8("", "text")
        with self.assertRaises(TypeError):
            atomic_write_utf8("sample", None)


if __name__ == "__main__":
    unittest.main()
