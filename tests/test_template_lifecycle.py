import os
from pathlib import Path
import tempfile
import unittest

from calamus_templates import (
    DEFAULT_TEMPLATE_NAME,
    NewFromTemplatePlan,
    ensure_templates_dir,
    list_templates,
    prepare_new_from_template_plan,
    read_template,
)


class TemplateStoreTests(unittest.TestCase):
    def test_ensure_store_creates_default_template(self):
        with tempfile.TemporaryDirectory() as td:
            templates_dir = ensure_templates_dir(td)
            self.assertTrue(os.path.isabs(templates_dir))
            default_path = os.path.join(templates_dir, DEFAULT_TEMPLATE_NAME)
            self.assertTrue(os.path.isfile(default_path))
            self.assertEqual(read_template(default_path), "Title\n=====\n\n")

    def test_listing_is_sorted_regular_and_suffix_filtered(self):
        with tempfile.TemporaryDirectory() as td:
            templates_dir = ensure_templates_dir(td)
            for name, text in (("zeta.md", "Z"), ("alpha.txt", "A"), ("skip.rtf", "R")):
                Path(templates_dir, name).write_text(text, encoding="utf-8")
            Path(templates_dir, "folder.md").mkdir()
            items = list_templates(td)
            names = [name for name, _path in items]
            self.assertEqual(names, ["alpha.txt", "blank-note.txt", "zeta.md"])
            self.assertTrue(all(os.path.isabs(path) for _name, path in items))

    def test_read_rejects_unsupported_missing_and_directory_targets(self):
        with tempfile.TemporaryDirectory() as td:
            templates_dir = ensure_templates_dir(td)
            unsupported = Path(templates_dir, "draft.rtf")
            unsupported.write_text("text", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_template(str(unsupported))
            with self.assertRaises(FileNotFoundError):
                read_template(str(Path(templates_dir, "missing.txt")))
            directory = Path(templates_dir, "folder.md")
            directory.mkdir()
            with self.assertRaises(FileNotFoundError):
                read_template(str(directory))

    def test_invalid_utf8_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            templates_dir = ensure_templates_dir(td)
            path = Path(templates_dir, "invalid.txt")
            path.write_bytes(b"\xff\xfe")
            with self.assertRaises(UnicodeError):
                read_template(str(path))


class NewFromTemplatePlanTests(unittest.TestCase):
    def test_plan_describes_modified_untitled_document(self):
        plan = prepare_new_from_template_plan("~/Templates/note.md", "Heading\n")
        self.assertIsInstance(plan, NewFromTemplatePlan)
        self.assertTrue(os.path.isabs(plan.source_path))
        self.assertEqual(plan.text, "Heading\n")
        self.assertIsNone(plan.target_path)
        self.assertTrue(plan.modified)

    def test_plan_is_deterministic_and_immutable(self):
        first = prepare_new_from_template_plan("note.txt", "Body")
        second = prepare_new_from_template_plan("note.txt", "Body")
        self.assertEqual(first, second)
        with self.assertRaises(Exception):
            first.text = "changed"

    def test_plan_rejects_bad_types_empty_path_and_unsupported_suffix(self):
        with self.assertRaises(TypeError):
            prepare_new_from_template_plan(None, "Body")
        with self.assertRaises(ValueError):
            prepare_new_from_template_plan("", "Body")
        with self.assertRaises(TypeError):
            prepare_new_from_template_plan("note.txt", None)
        with self.assertRaises(ValueError):
            prepare_new_from_template_plan("note.rtf", "Body")


if __name__ == "__main__":
    unittest.main()
