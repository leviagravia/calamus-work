import os
from pathlib import Path
import tempfile
import unittest

from calamus_workspace_application import WorkspaceApplicationRuntime
from calamus_workspace_controller import WorkspaceController
from calamus_workspace_gio import WorkspaceOperationResult
from calamus_workspace_mutation import WorkspaceMutationController, WorkspaceMutationRuntime


class RealExclusiveLocalAdapter:
    """Test adapter that performs a real O_EXCL filesystem commit without GTK."""
    def create_new_text_file(self, plan):
        try:
            fd = os.open(plan.target_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
            os.close(fd)
            return WorkspaceOperationResult(True, plan.target_path, committed=True)
        except OSError as exc:
            return WorkspaceOperationResult(False, plan.target_path, str(exc), committed=False)


class CommittedFailureAdapter:
    def create_new_text_file(self, plan):
        Path(plan.target_path).write_bytes(b"")
        return WorkspaceOperationResult(
            False, plan.target_path, "created but verification failed", committed=True
        )


class View:
    def __init__(self):
        self.snapshot = None
        self.selected = None
        self.selected_paths = []
    def render(self, snapshot):
        self.snapshot = snapshot
    def selected_item(self):
        return self.selected
    def select_path(self, path):
        self.selected_paths.append(path)
        if self.snapshot:
            self.selected = self.snapshot.by_absolute_path(path)
        return self.selected is not None


class State:
    def add_recent_workspace(self, _path):
        pass


class WorkspaceMutationRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Workspace"
        self.drafts = self.root / "Drafts"
        self.drafts.mkdir(parents=True)
        (self.drafts / "Existing.md").write_text("existing", encoding="utf-8")
        self.view = View()
        self.errors = []
        self.opens = []
        self.continue_allowed = True
        self.workspace_controller = WorkspaceController()
        self.workspace_runtime = WorkspaceApplicationRuntime(
            self.workspace_controller,
            self.view,
            State(),
            may_continue=lambda: True,
            open_document=lambda _path: True,
            open_external=lambda _path: True,
            reveal_external=lambda _path: True,
            save_settings=lambda _data: True,
            report_error=self.errors.append,
            on_root_changed=lambda _root: None,
            on_recent_changed=lambda: None,
        )
        self.workspace_runtime.open_root(str(self.root), persist=False)
        self.mutation_controller = WorkspaceMutationController(
            self.workspace_controller, RealExclusiveLocalAdapter()
        )
        self.runtime = WorkspaceMutationRuntime(
            self.mutation_controller,
            self.workspace_runtime,
            self.view,
            may_continue=lambda: self.continue_allowed,
            open_document=lambda path: self.opens.append(path) or True,
            report_error=self.errors.append,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_selected_folder_creates_rescans_selects_and_opens(self):
        self.view.selected = self.view.snapshot.by_relative_path("Drafts")
        self.assertTrue(self.runtime.create_new_text_file(self.view.selected, "Chapter_2", suffix=".md"))
        target = str(self.drafts / "Chapter_2.md")
        self.assertTrue(Path(target).is_file())
        self.assertEqual(self.opens, [target])
        self.assertEqual(self.view.selected_paths, [target])
        self.assertIsNotNone(self.workspace_controller.snapshot.by_absolute_path(target))

    def test_selected_file_creates_sibling(self):
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        self.assertTrue(self.runtime.create_new_text_file(self.view.selected, "Sibling", suffix=".txt"))
        self.assertTrue((self.drafts / "Sibling.txt").is_file())

    def test_no_selection_creates_in_root(self):
        self.assertTrue(self.runtime.create_new_text_file(None, "Root_Note", suffix=".txt"))
        self.assertTrue((self.root / "Root_Note.txt").is_file())

    def test_unsaved_cancel_happens_before_filesystem_mutation(self):
        self.continue_allowed = False
        self.view.selected = self.view.snapshot.by_relative_path("Drafts")
        self.assertFalse(self.runtime.create_new_text_file(self.view.selected, "Cancelled", suffix=".md"))
        self.assertFalse((self.drafts / "Cancelled.md").exists())
        self.assertEqual(self.opens, [])

    def test_collision_preserves_existing_content_and_reports_error(self):
        self.view.selected = self.view.snapshot.by_relative_path("Drafts")
        self.assertFalse(self.runtime.create_new_text_file(self.view.selected, "Existing.md", suffix=".txt"))
        self.assertEqual((self.drafts / "Existing.md").read_text(encoding="utf-8"), "existing")
        self.assertTrue(self.errors)

    def test_committed_failure_is_rescanned_selected_and_reported_without_open(self):
        controller = WorkspaceMutationController(
            self.workspace_controller, CommittedFailureAdapter()
        )
        runtime = WorkspaceMutationRuntime(
            controller, self.workspace_runtime, self.view,
            may_continue=lambda: True,
            open_document=lambda path: self.fail("committed failure must not open"),
            report_error=self.errors.append,
        )
        self.view.selected = self.view.snapshot.by_relative_path("Drafts")
        self.assertFalse(runtime.create_new_text_file(self.view.selected, "Partial", suffix=".txt"))
        target = str(self.drafts / "Partial.txt")
        self.assertTrue(Path(target).exists())
        self.assertIn(target, self.view.selected_paths)
        self.assertIn("verification failed", self.errors[-1])

    def test_stale_selection_and_symlink_destination_fail_closed(self):
        item = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        (self.drafts / "Existing.md").unlink()
        self.workspace_controller.refresh()
        self.assertFalse(self.runtime.create_new_text_file(item, "Nope", suffix=".txt"))
        self.assertFalse((self.drafts / "Nope.txt").exists())

        outside = Path(self.tmp.name) / "Outside"
        outside.mkdir()
        try:
            os.symlink(outside, self.root / "Link")
        except OSError:
            return
        self.workspace_runtime.refresh()
        link = self.view.snapshot.by_relative_path("Link")
        self.assertFalse(self.runtime.create_new_text_file(link, "Nope", suffix=".txt"))
        self.assertFalse((outside / "Nope.txt").exists())


if __name__ == "__main__":
    unittest.main()
