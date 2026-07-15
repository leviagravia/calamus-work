import os
import tempfile
import unittest

from calamus_file_lifecycle import SavePlan, prepare_save_as_plan, prepare_save_plan
from calamus_model import Document


class SaveLifecyclePlanTests(unittest.TestCase):
    def test_untitled_document_requires_existing_save_as_boundary(self):
        plan = prepare_save_plan(None, "Body")
        self.assertIsInstance(plan, SavePlan)
        self.assertTrue(plan.requires_destination)
        self.assertIsNone(plan.target_path)
        self.assertEqual(plan.text_to_write, "Body")
        self.assertFalse(plan.replaces_buffer_text)

    def test_empty_destination_is_treated_as_untitled(self):
        plan = prepare_save_plan("", "Body")
        self.assertTrue(plan.requires_destination)
        self.assertIsNone(plan.target_path)

    def test_named_document_preserves_destination_and_text(self):
        plan = prepare_save_plan("/tmp/note.txt", "A  B\n")
        self.assertFalse(plan.requires_destination)
        self.assertEqual(plan.target_path, "/tmp/note.txt")
        self.assertEqual(plan.text_to_write, "A  B\n")
        self.assertFalse(plan.replaces_buffer_text)

    def test_trim_trailing_on_save_is_pure_and_line_preserving(self):
        original = "  alpha  \n\tbeta\t\n\n"
        plan = prepare_save_plan(
            "/tmp/note.txt",
            original,
            trim_trailing_on_save=True,
        )
        self.assertEqual(plan.original_text, original)
        self.assertEqual(plan.text_to_write, "  alpha\n\tbeta\n")
        self.assertTrue(plan.replaces_buffer_text)

    def test_trim_noop_does_not_request_buffer_replacement(self):
        plan = prepare_save_plan(
            "/tmp/note.txt",
            "alpha\nbeta\n",
            trim_trailing_on_save=True,
        )
        self.assertFalse(plan.replaces_buffer_text)


    def test_save_as_cancelled_selection_returns_no_plan(self):
        self.assertIsNone(prepare_save_as_plan(None, "Body"))
        self.assertIsNone(prepare_save_as_plan("", "Body"))

    def test_save_as_accepted_destination_reuses_save_plan_contract(self):
        plan = prepare_save_as_plan("/tmp/copy.txt", "Body\n")
        self.assertIsInstance(plan, SavePlan)
        self.assertFalse(plan.requires_destination)
        self.assertEqual(plan.target_path, "/tmp/copy.txt")
        self.assertEqual(plan.original_text, "Body\n")
        self.assertEqual(plan.text_to_write, "Body\n")

    def test_save_as_preserves_trim_trailing_policy(self):
        plan = prepare_save_as_plan(
            "/tmp/copy.txt",
            "alpha  \nbeta\t\n",
            trim_trailing_on_save=True,
        )
        self.assertEqual(plan.text_to_write, "alpha\nbeta\n")
        self.assertTrue(plan.replaces_buffer_text)

    def test_save_as_rejects_non_string_destination(self):
        with self.assertRaises(TypeError):
            prepare_save_as_plan(123, "Body")

    def test_plan_integrates_with_existing_document_write_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "note.txt")
            plan = prepare_save_plan(
                path,
                "alpha  \nbeta\t\n",
                trim_trailing_on_save=True,
            )
            document = Document(modified=True)
            document.save(plan.target_path, plan.text_to_write)
            with open(path, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "alpha\nbeta\n")
            self.assertEqual(document.file_path, path)
            self.assertFalse(document.modified)

    def test_non_string_inputs_fail_before_io(self):
        with self.assertRaises(TypeError):
            prepare_save_plan(123, "Body")
        with self.assertRaises(TypeError):
            prepare_save_plan("/tmp/note.txt", None)


if __name__ == "__main__":
    unittest.main()
