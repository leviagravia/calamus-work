import os
from pathlib import Path
import tempfile
import unittest

from calamus_workspace_operations import (
    WorkspaceOperationError,
    normalize_text_suffix,
    normalize_workspace_basename,
    plan_new_text_file,
)


class WorkspaceOperationPlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Workspace"
        self.parent = self.root / "Drafts"
        self.parent.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_suffix_is_explicit_and_limited_to_txt_md(self):
        self.assertEqual(normalize_text_suffix("txt"), ".txt")
        self.assertEqual(normalize_text_suffix(".MD"), ".md")
        with self.assertRaises(WorkspaceOperationError):
            normalize_text_suffix(".pdf")

    def test_basename_appends_selected_suffix(self):
        self.assertEqual(normalize_workspace_basename("Chapter 1", suffix=".md"), "Chapter 1.md")
        self.assertEqual(normalize_workspace_basename("notes.txt", suffix=".md"), "notes.txt")

    def test_basename_rejects_paths_hidden_reserved_and_unsupported_suffix(self):
        for value in ("../escape", "folder/name", r"folder\name", ".secret", ".", "..", "bad.pdf"):
            with self.subTest(value=value):
                with self.assertRaises(WorkspaceOperationError):
                    normalize_workspace_basename(value, suffix=".txt")

    def test_basename_rejects_empty_nul_and_overlong(self):
        for value in ("", "   ", "bad\x00name", "x" * 256):
            with self.subTest(value=value):
                with self.assertRaises(WorkspaceOperationError):
                    normalize_workspace_basename(value, suffix=".txt")

    def test_plan_is_immutable_root_confined_and_open_after_commit(self):
        plan = plan_new_text_file(str(self.root), str(self.parent), "Chapter", suffix=".md")
        self.assertEqual(plan.kind, "new-text-file")
        self.assertEqual(plan.root, str(self.root))
        self.assertEqual(plan.parent_path, str(self.parent))
        self.assertEqual(plan.target_path, str(self.parent / "Chapter.md"))
        self.assertTrue(plan.open_after_commit)
        with self.assertRaises(Exception):
            plan.target_path = "other"

    def test_plan_rejects_parent_outside_root(self):
        outside = Path(self.tmp.name) / "Outside"
        outside.mkdir()
        with self.assertRaises(WorkspaceOperationError):
            plan_new_text_file(str(self.root), str(outside), "Chapter", suffix=".md")

    def test_planner_is_compute_only_and_does_not_create_target(self):
        plan = plan_new_text_file(str(self.root), str(self.parent), "New", suffix=".txt")
        self.assertFalse(os.path.exists(plan.target_path))


if __name__ == "__main__":
    unittest.main()
