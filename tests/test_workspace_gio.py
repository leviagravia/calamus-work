import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from calamus_workspace_gio import HAVE_GIO, WorkspaceGioAdapter
from calamus_workspace_operations import (
    WorkspaceContentToken, WorkspacePathToken, plan_duplicate_text_file,
    plan_move_to_trash, plan_new_folder, plan_new_text_file,
    plan_workspace_rename,
)


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

    @staticmethod
    def content_token(path):
        st = path.lstat()
        return WorkspaceContentToken(st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns)

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

    def test_duplicate_regular_text_file_is_real_no_overwrite_and_source_preserved(self):
        source=self.root/'Draft.md'
        source.write_text('draft content',encoding='utf-8')
        plan=plan_duplicate_text_file(
            str(self.root),str(source),[source.name],source_token=self.content_token(source)
        )
        result=self.adapter.duplicate_text_file(plan)
        self.assertTrue(result.success,result.message)
        target=self.root/'Draft copy.md'
        self.assertEqual(source.read_text(encoding='utf-8'),'draft content')
        self.assertEqual(target.read_text(encoding='utf-8'),'draft content')
        self.assertFalse(target.is_symlink())

    def test_duplicate_source_replacement_and_target_collision_fail_closed(self):
        source=self.root/'Draft.md'
        source.write_text('source',encoding='utf-8')
        token=self.content_token(source)
        plan=plan_duplicate_text_file(
            str(self.root),str(source),[source.name],source_token=token
        )
        source.unlink()
        outside=Path(self.tmp.name)/'Outside.md'
        outside.write_text('outside',encoding='utf-8')
        try:
            source.symlink_to(outside)
        except OSError:
            self.skipTest('symlinks unavailable')
        result=self.adapter.duplicate_text_file(plan)
        self.assertFalse(result.success)
        self.assertFalse((self.root/'Draft copy.md').exists())
        self.assertEqual(outside.read_text(encoding='utf-8'),'outside')

        source.unlink()
        source.write_text('source',encoding='utf-8')
        target=self.root/'Draft copy.md'
        target.write_text('keep',encoding='utf-8')
        plan=plan_duplicate_text_file(
            str(self.root),str(source),[source.name],source_token=self.content_token(source)
        )
        # Force a late collision at the planned target.
        Path(plan.target_path).write_text('late keep',encoding='utf-8')
        result=self.adapter.duplicate_text_file(plan)
        self.assertFalse(result.success)
        self.assertEqual(Path(plan.target_path).read_text(encoding='utf-8'),'late keep')

    def test_duplicate_managed_sidecar_is_transactional_and_preserves_source(self):
        source=self.root/'Draft.md'
        source.write_text('draft',encoding='utf-8')
        sidecar=Path(str(source)+'.source-notes.md')
        sidecar.write_text('notes',encoding='utf-8')
        occupied=[p.name for p in self.root.iterdir()]
        plan=plan_duplicate_text_file(
            str(self.root),str(source),occupied,source_token=self.content_token(source),
            companion_source_path=str(sidecar),companion_token=self.content_token(sidecar),
        )
        result=self.adapter.duplicate_text_file(plan)
        self.assertTrue(result.success,result.message)
        self.assertEqual((self.root/'Draft copy.md').read_text(encoding='utf-8'),'draft')
        self.assertEqual((self.root/'Draft copy.md.source-notes.md').read_text(encoding='utf-8'),'notes')
        self.assertEqual(source.read_text(encoding='utf-8'),'draft')
        self.assertEqual(sidecar.read_text(encoding='utf-8'),'notes')


    def test_move_to_system_trash_is_real_and_carries_managed_sidecar(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as sandbox:
            sandbox_path = Path(sandbox)
            home = sandbox_path / "home"
            xdg = sandbox_path / "xdg"
            home.mkdir()
            xdg.mkdir()
            script = r'''
import json
import os
from pathlib import Path
from calamus_workspace_gio import WorkspaceGioAdapter
from calamus_workspace_operations import WorkspacePathToken, plan_move_to_trash

home = Path(os.environ["HOME"])
root = home / "Workspace"
root.mkdir()
source = root / "Draft.md"
source.write_text("draft", encoding="utf-8")
sidecar = Path(str(source) + ".source-notes.md")
sidecar.write_text("notes", encoding="utf-8")

def token(path):
    st = path.lstat()
    return WorkspacePathToken(st.st_dev, st.st_ino, st.st_mode)

plan = plan_move_to_trash(
    str(root), str(source), source_is_directory=False,
    source_token=token(source), companion_source_path=str(sidecar),
    companion_token=token(sidecar),
)
result = WorkspaceGioAdapter().move_to_trash(plan)
trash_files = Path(os.environ["XDG_DATA_HOME"]) / "Trash" / "files"
print(json.dumps({
    "success": result.success,
    "committed": result.committed,
    "message": result.message,
    "source_exists": os.path.lexists(source),
    "sidecar_exists": os.path.lexists(sidecar),
    "trash_names": sorted(p.name for p in trash_files.iterdir()) if trash_files.exists() else [],
}))
'''
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_DATA_HOME": str(xdg),
                "PYTHONPATH": str(repo / "calamus"),
            })
            completed = subprocess.run(
                [sys.executable, "-c", script],
                env=env, text=True, capture_output=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout.strip().splitlines()[-1])
            self.assertTrue(payload["success"], payload["message"])
            self.assertTrue(payload["committed"])
            self.assertFalse(payload["source_exists"])
            self.assertFalse(payload["sidecar_exists"])
            self.assertIn("Draft.md", payload["trash_names"])
            self.assertIn("Draft.md.source-notes.md", payload["trash_names"])

    def test_trash_source_replacement_by_symlink_is_blocked(self):
        source = self.root / "Draft.md"
        source.write_text("draft", encoding="utf-8")
        plan = plan_move_to_trash(
            str(self.root), str(source), source_is_directory=False,
            source_token=self.token(source),
        )
        source.unlink()
        outside = Path(self.tmp.name) / "Outside.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            source.symlink_to(outside)
        except OSError:
            self.skipTest("symlinks unavailable")
        result = self.adapter.move_to_trash(plan)
        self.assertFalse(result.success)
        self.assertFalse(result.committed)
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside")


if __name__ == "__main__":
    unittest.main()
