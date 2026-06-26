import os
import tempfile
import unittest

from calamus_model import Document
import calamus_commands as commands


class ModelTests(unittest.TestCase):
    def test_document_load_save_and_modified_state(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "note.txt")
            doc = Document()
            doc.set_text("hello", modified=True)
            self.assertTrue(doc.modified)
            doc.save(path)
            self.assertFalse(doc.modified)
            self.assertEqual(doc.file_path, path)
            loaded = Document()
            self.assertEqual(loaded.load(path), "hello")
            self.assertFalse(loaded.modified)
            loaded.mark_modified("hello!")
            self.assertTrue(loaded.modified)

    def test_document_clear(self):
        doc = Document("x", "/tmp/x", True)
        doc.clear()
        self.assertEqual(doc.get_text(), "")
        self.assertIsNone(doc.file_path)
        self.assertFalse(doc.modified)


class CommandTests(unittest.TestCase):
    def test_replace_insert_and_transform_range(self):
        text, sel = commands.replace_range("abc", 1, 2, "XYZ")
        self.assertEqual(text, "aXYZc")
        self.assertEqual(sel, (1, 4))
        text, sel = commands.insert_at(text, 999, "!")
        self.assertEqual(text, "aXYZc!")
        self.assertEqual(sel, (5, 6))
        text, sel = commands.transform_range("ciao mondo", 5, 10, str.upper)
        self.assertEqual(text, "ciao MONDO")
        self.assertEqual(sel, (5, 10))

    def test_shortcut_table_has_no_conflicts(self):
        self.assertEqual(commands.shortcut_conflicts(), {})


if __name__ == "__main__":
    unittest.main()
