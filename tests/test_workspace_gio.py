from pathlib import Path
import tempfile
import unittest

from calamus_workspace_gio import HAVE_GIO, WorkspaceGioAdapter
from calamus_workspace_operations import plan_new_folder, plan_new_text_file


@unittest.skipUnless(HAVE_GIO, "PyGObject/GIO unavailable in this environment")
class WorkspaceGioAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Workspace"
        self.root.mkdir()
        self.adapter = WorkspaceGioAdapter()

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_is_real_empty_regular_file(self):
        plan = plan_new_text_file(str(self.root), str(self.root), "Created", suffix=".md")
        result = self.adapter.create_new_text_file(plan)
        self.assertTrue(result.success, result.message)
        target = self.root / "Created.md"
        self.assertTrue(target.is_file())
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_bytes(), b"")

    def test_existing_target_is_never_overwritten(self):
        target = self.root / "Existing.txt"
        target.write_text("keep me", encoding="utf-8")
        plan = plan_new_text_file(str(self.root), str(self.root), "Existing.txt", suffix=".txt")
        result = self.adapter.create_new_text_file(plan)
        self.assertFalse(result.success)
        self.assertEqual(target.read_text(encoding="utf-8"), "keep me")


    def test_parent_replaced_by_symlink_before_execute_is_blocked(self):
        parent = self.root / "Drafts"
        parent.mkdir()
        plan = plan_new_text_file(str(self.root), str(parent), "Escaped", suffix=".txt")
        outside = Path(self.tmp.name) / "Outside"
        outside.mkdir()
        parent.rmdir()
        try:
            parent.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unavailable")
        result = self.adapter.create_new_text_file(plan)
        self.assertFalse(result.success)
        self.assertFalse(result.committed)
        self.assertFalse((outside / "Escaped.txt").exists())

    def test_missing_parent_is_structured_failure(self):
        missing = self.root / "Missing"
        plan = plan_new_text_file(str(self.root), str(missing), "New", suffix=".txt")
        result = self.adapter.create_new_text_file(plan)
        self.assertFalse(result.success)
        self.assertFalse((missing / "New.txt").exists())

    def test_new_folder_is_real_exclusive_directory(self):
        plan = plan_new_folder(str(self.root), str(self.root), "Research")
        result = self.adapter.create_new_folder(plan)
        self.assertTrue(result.success, result.message)
        target = self.root / "Research"
        self.assertTrue(target.is_dir())
        self.assertFalse(target.is_symlink())

    def test_existing_folder_or_file_is_never_replaced(self):
        folder = self.root / "ExistingFolder"
        folder.mkdir()
        result = self.adapter.create_new_folder(
            plan_new_folder(str(self.root), str(self.root), "ExistingFolder")
        )
        self.assertFalse(result.success)
        self.assertTrue(folder.is_dir())

        file_target = self.root / "ExistingFile"
        file_target.write_text("keep", encoding="utf-8")
        result = self.adapter.create_new_folder(
            plan_new_folder(str(self.root), str(self.root), "ExistingFile")
        )
        self.assertFalse(result.success)
        self.assertEqual(file_target.read_text(encoding="utf-8"), "keep")

    def test_new_folder_parent_replaced_by_symlink_is_blocked(self):
        parent = self.root / "Drafts"
        parent.mkdir()
        plan = plan_new_folder(str(self.root), str(parent), "Escaped")
        outside = Path(self.tmp.name) / "OutsideFolder"
        outside.mkdir()
        parent.rmdir()
        try:
            parent.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unavailable")
        result = self.adapter.create_new_folder(plan)
        self.assertFalse(result.success)
        self.assertFalse(result.committed)
        self.assertFalse((outside / "Escaped").exists())

    def test_new_folder_missing_parent_is_structured_failure(self):
        missing = self.root / "MissingFolderParent"
        plan = plan_new_folder(str(self.root), str(missing), "Child")
        result = self.adapter.create_new_folder(plan)
        self.assertFalse(result.success)
        self.assertFalse(result.committed)
        self.assertFalse((missing / "Child").exists())

    def test_new_folder_target_replaced_by_symlink_is_not_followed(self):
        outside = Path(self.tmp.name) / "OutsideTarget"
        outside.mkdir()
        target = self.root / "TargetLink"
        try:
            target.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unavailable")
        result = self.adapter.create_new_folder(
            plan_new_folder(str(self.root), str(self.root), "TargetLink")
        )
        self.assertFalse(result.success)
        self.assertFalse(result.committed)
        self.assertTrue(target.is_symlink())
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
