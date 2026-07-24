import os
from pathlib import Path
import tempfile
import unittest

from calamus_workspace_operations import (
    WorkspaceOperationError,
    normalize_text_suffix,
    normalize_workspace_basename,
    normalize_workspace_folder_name,
    WorkspacePathToken,
    normalize_workspace_rename_name,
    plan_new_folder,
    plan_new_text_file,
    plan_workspace_rename,
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

    def test_folder_name_is_one_visible_component(self):
        self.assertEqual(normalize_workspace_folder_name("  Chapter Notes  "), "Chapter Notes")
        for value in ("", "../escape", "folder/name", r"folder\name", ".hidden", ".", "..", "bad\x00name", "x" * 256):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, WorkspaceOperationError)):
                    normalize_workspace_folder_name(value)

    def test_new_folder_plan_is_single_level_confined_and_not_opened(self):
        plan = plan_new_folder(str(self.root), str(self.parent), "Research")
        self.assertEqual(plan.kind, "new-folder")
        self.assertEqual(plan.target_path, str(self.parent / "Research"))
        self.assertFalse(plan.open_after_commit)
        self.assertFalse(os.path.exists(plan.target_path))

    def test_new_folder_plan_rejects_parent_outside_root(self):
        outside = Path(self.tmp.name) / "Outside"
        outside.mkdir()
        with self.assertRaises(WorkspaceOperationError):
            plan_new_folder(str(self.root), str(outside), "Research")

    def test_rename_name_is_one_visible_component_without_suffix_policy(self):
        self.assertEqual(normalize_workspace_rename_name("  Chapter.pdf  "), "Chapter.pdf")
        for value in ("", "../escape", "nested/name", r"nested\name", ".hidden", ".", ".."):
            with self.subTest(value=value):
                with self.assertRaises(WorkspaceOperationError):
                    normalize_workspace_rename_name(value)

    def test_file_rename_plan_is_same_parent_confined_and_can_carry_sidecar(self):
        source = self.parent / "Draft.md"
        sidecar = Path(str(source) + ".source-notes.md")
        token = WorkspacePathToken(1, 2, 3)
        companion_token = WorkspacePathToken(1, 4, 5)
        plan = plan_workspace_rename(
            str(self.root), str(source), "Chapter.md", source_is_directory=False,
            source_token=token, companion_source_path=str(sidecar),
            companion_token=companion_token, manage_source_notes=True,
        )
        self.assertEqual(plan.target_path, str(self.parent / "Chapter.md"))
        self.assertEqual(plan.companion_target_path, str(self.parent / "Chapter.md.source-notes.md"))
        self.assertFalse(plan.source_is_directory)

    def test_folder_rename_plan_has_no_document_open_or_recursive_move_semantics(self):
        source = self.parent / "Old"
        plan = plan_workspace_rename(
            str(self.root), str(source), "New", source_is_directory=True,
            source_token=WorkspacePathToken(1, 2, 3),
        )
        self.assertEqual(plan.parent_path, str(self.parent))
        self.assertEqual(plan.target_path, str(self.parent / "New"))
        self.assertIsNone(plan.companion_source_path)

    def test_rename_rejects_noop_root_and_managed_sidecar_directly(self):
        token = WorkspacePathToken(1, 2, 3)
        with self.assertRaises(WorkspaceOperationError):
            plan_workspace_rename(
                str(self.root), str(self.parent / "Draft.md"), "Draft.md",
                source_is_directory=False, source_token=token,
            )
        with self.assertRaises(WorkspaceOperationError):
            plan_workspace_rename(
                str(self.root), str(self.root), "Other",
                source_is_directory=True, source_token=token,
            )
        with self.assertRaises(WorkspaceOperationError):
            plan_workspace_rename(
                str(self.root), str(self.parent / "Draft.md.source-notes.md"), "Other.md",
                source_is_directory=False, source_token=token,
            )


if __name__ == "__main__":
    unittest.main()
