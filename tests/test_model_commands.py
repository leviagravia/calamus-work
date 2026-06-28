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

    def test_line_bounds_at_offset(self):
        self.assertEqual(commands.line_bounds_at_offset("one\ntwo\nthree", 0), (0, 3))
        self.assertEqual(commands.line_bounds_at_offset("one\ntwo\nthree", 5), (4, 7))
        self.assertEqual(commands.line_bounds_at_offset("one\ntwo\nthree", 999), (8, 13))

    def test_duplicate_selection_plan(self):
        plan = commands.duplicate_line_or_selection_plan("abcde", cursor=0, selection=(1, 3))
        self.assertEqual(plan, (3, "bc", (3, 5), True))

    def test_duplicate_selection_plan_normalizes_reversed_selection(self):
        plan = commands.duplicate_line_or_selection_plan("abcde", cursor=0, selection=(3, 1))
        self.assertEqual(plan, (3, "bc", (3, 5), True))

    def test_duplicate_line_plan_middle_line(self):
        plan = commands.duplicate_line_or_selection_plan("one\ntwo\nthree", cursor=5)
        self.assertEqual(plan, (8, "two\n", (12, 12), False))

    def test_duplicate_line_plan_final_line_without_newline(self):
        plan = commands.duplicate_line_or_selection_plan("one\ntwo", cursor=5)
        self.assertEqual(plan, (7, "\ntwo", (11, 11), False))

    def test_duplicate_line_plan_empty_document_preserves_legacy_newline(self):
        plan = commands.duplicate_line_or_selection_plan("", cursor=0)
        self.assertEqual(plan, (0, "\n", (1, 1), False))

    def test_paste_text_plan_inserts_at_cursor(self):
        plan = commands.paste_text_plan("alpha omega", " beta", cursor=5)
        self.assertEqual(plan, (5, 5, " beta", (5, 10)))

    def test_paste_text_plan_replaces_selection(self):
        plan = commands.paste_text_plan("alpha omega", "beta", cursor=0, selection=(6, 11))
        self.assertEqual(plan, (6, 11, "beta", (6, 10)))

    def test_paste_text_plan_normalizes_reversed_selection(self):
        plan = commands.paste_text_plan("alpha omega", "beta", cursor=0, selection=(11, 6))
        self.assertEqual(plan, (6, 11, "beta", (6, 10)))

    def test_paste_text_plan_clamps_cursor(self):
        plan = commands.paste_text_plan("alpha", "!", cursor=999)
        self.assertEqual(plan, (5, 5, "!", (5, 6)))

    def test_paste_text_plan_none_insertion_is_empty(self):
        plan = commands.paste_text_plan("alpha", None, cursor=2)
        self.assertEqual(plan, (2, 2, "", (2, 2)))

    def test_shortcut_table_has_no_conflicts(self):
        self.assertEqual(commands.shortcut_conflicts(), {})


if __name__ == "__main__":
    unittest.main()
