from pathlib import Path
import tempfile
import unittest

from calamus_workspace_gio import HAVE_GIO, WorkspaceGioAdapter
from calamus_workspace_operations import WorkspacePathToken, plan_new_folder, plan_new_text_file, plan_workspace_rename


@unittest.skipUnless(HAVE_GIO, "PyGObject/GIO unavailable in this environment")
class WorkspaceGioAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Workspace"
        self.root.mkdir()
        self.adapter = WorkspaceGioAdapter()

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def token(path):
        st = path.lstat()
        return WorkspacePathToken(st.st_dev, st.st_ino, st.st_mode)

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

    def test_regular_file_rename_is_real_and_never_overwrites(self):
        source = self.root / "Draft.md"
        source.write_text("content", encoding="utf-8")
        plan = plan_workspace_rename(
            str(self.root), str(source), "Chapter.md", source_is_directory=False,
            source_token=self.token(source),
        )
        result = self.adapter.rename_item(plan)
        self.assertTrue(result.success, result.message)
        self.assertFalse(source.exists())
        self.assertEqual((self.root / "Chapter.md").read_text(encoding="utf-8"), "content")

    def test_folder_rename_preserves_children(self):
        source = self.root / "Drafts"
        source.mkdir()
        (source / "One.md").write_text("one", encoding="utf-8")
        plan = plan_workspace_rename(
            str(self.root), str(source), "Chapters", source_is_directory=True,
            source_token=self.token(source),
        )
        result = self.adapter.rename_item(plan)
        self.assertTrue(result.success, result.message)
        self.assertEqual((self.root / "Chapters" / "One.md").read_text(encoding="utf-8"), "one")

    def test_rename_collision_and_symlink_replacement_fail_closed(self):
        source = self.root / "Draft.md"
        source.write_text("source", encoding="utf-8")
        target = self.root / "Chapter.md"
        target.write_text("target", encoding="utf-8")
        plan = plan_workspace_rename(
            str(self.root), str(source), target.name, source_is_directory=False,
            source_token=self.token(source),
        )
        result = self.adapter.rename_item(plan)
        self.assertFalse(result.success)
        self.assertEqual(source.read_text(encoding="utf-8"), "source")
        self.assertEqual(target.read_text(encoding="utf-8"), "target")

        outside = Path(self.tmp.name) / "Outside"
        outside.write_text("outside", encoding="utf-8")
        old_token = self.token(source)
        source.unlink()
        try:
            source.symlink_to(outside)
        except OSError:
            self.skipTest("symlinks unavailable")
        replaced_plan = plan_workspace_rename(
            str(self.root), str(source), "Renamed.md", source_is_directory=False,
            source_token=old_token,
        )
        result = self.adapter.rename_item(replaced_plan)
        self.assertFalse(result.success)
        self.assertTrue(source.is_symlink())
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside")

    def test_document_sidecar_renames_with_document(self):
        source = self.root / "Draft.md"
        source.write_text("draft", encoding="utf-8")
        sidecar = Path(str(source) + ".source-notes.md")
        sidecar.write_text("notes", encoding="utf-8")
        plan = plan_workspace_rename(
            str(self.root), str(source), "Chapter.md", source_is_directory=False,
            source_token=self.token(source), companion_source_path=str(sidecar),
            companion_token=self.token(sidecar), manage_source_notes=True,
        )
        result = self.adapter.rename_item(plan)
        self.assertTrue(result.success, result.message)
        self.assertFalse(sidecar.exists())
        self.assertEqual((self.root / "Chapter.md.source-notes.md").read_text(encoding="utf-8"), "notes")

    def test_sidecar_collision_blocks_primary_rename(self):
        source = self.root / "Draft.md"
        source.write_text("draft", encoding="utf-8")
        sidecar = Path(str(source) + ".source-notes.md")
        sidecar.write_text("notes", encoding="utf-8")
        target_sidecar = self.root / "Chapter.md.source-notes.md"
        target_sidecar.write_text("keep", encoding="utf-8")
        plan = plan_workspace_rename(
            str(self.root), str(source), "Chapter.md", source_is_directory=False,
            source_token=self.token(source), companion_source_path=str(sidecar),
            companion_token=self.token(sidecar), manage_source_notes=True,
        )
        result = self.adapter.rename_item(plan)
        self.assertFalse(result.success)
        self.assertTrue(source.exists())
        self.assertEqual(sidecar.read_text(encoding="utf-8"), "notes")
        self.assertEqual(target_sidecar.read_text(encoding="utf-8"), "keep")

    def test_managed_target_sidecar_collision_blocks_rename_without_source_sidecar(self):
        source = self.root / "Draft.md"
        source.write_text("draft", encoding="utf-8")
        target_sidecar = self.root / "Chapter.md.source-notes.md"
        target_sidecar.write_text("unrelated", encoding="utf-8")
        plan = plan_workspace_rename(
            str(self.root), str(source), "Chapter.md", source_is_directory=False,
            source_token=self.token(source), manage_source_notes=True,
        )
        result = self.adapter.rename_item(plan)
        self.assertFalse(result.success)
        self.assertFalse(result.committed)
        self.assertTrue(source.exists())
        self.assertFalse((self.root / "Chapter.md").exists())
        self.assertEqual(target_sidecar.read_text(encoding="utf-8"), "unrelated")

    def test_case_only_rename_is_supported_when_filesystem_allows_it(self):
        source = self.root / "CaseNote.txt"
        source.write_text("case", encoding="utf-8")
        target = self.root / "casenote.txt"
        plan = plan_workspace_rename(
            str(self.root), str(source), target.name, source_is_directory=False,
            source_token=self.token(source),
        )
        result = self.adapter.rename_item(plan)
        if not result.success:
            self.skipTest(f"filesystem does not support direct case-only rename: {result.message}")
        self.assertFalse(source.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), "case")


if __name__ == "__main__":
    unittest.main()
