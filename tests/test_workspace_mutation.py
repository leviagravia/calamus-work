import os
import shutil
from pathlib import Path
import tempfile
import unittest

from calamus_workspace_application import WorkspaceApplicationRuntime
from calamus_workspace_controller import WorkspaceController
from calamus_workspace_gio import WorkspaceOperationResult
from calamus_workspace_identity import WorkspacePathReferenceSnapshot
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

    def create_new_folder(self, plan):
        try:
            os.mkdir(plan.target_path)
            return WorkspaceOperationResult(True, plan.target_path, committed=True)
        except OSError as exc:
            return WorkspaceOperationResult(False, plan.target_path, str(exc), committed=False)

    def duplicate_text_file(self, plan):
        try:
            if os.path.lexists(plan.target_path):
                raise FileExistsError(plan.target_path)
            shutil.copyfile(plan.source_path, plan.target_path)
            for source_path, target_path in (
                (plan.companion_source_path, plan.companion_target_path),
                (plan.scratchpad_source_path, plan.scratchpad_target_path),
            ):
                if source_path:
                    if os.path.lexists(target_path):
                        os.unlink(plan.target_path)
                        raise FileExistsError(target_path)
                    shutil.copyfile(source_path, target_path)
            return WorkspaceOperationResult(
                True, plan.target_path, committed=True, source_path=plan.source_path,
                companion_path=plan.companion_target_path or '',
                scratchpad_path=plan.scratchpad_target_path or '',
            )
        except OSError as exc:
            return WorkspaceOperationResult(False, plan.target_path, str(exc), committed=False)

    def rename_item(self, plan):
        try:
            if os.path.lexists(plan.target_path):
                raise FileExistsError(plan.target_path)
            for source_path, target_path in (
                (plan.companion_source_path, plan.companion_target_path),
                (plan.scratchpad_source_path, plan.scratchpad_target_path),
            ):
                if target_path and os.path.lexists(target_path):
                    raise FileExistsError(target_path)
                if source_path:
                    os.rename(source_path, target_path)
            os.rename(plan.source_path, plan.target_path)
            return WorkspaceOperationResult(
                True, plan.target_path, committed=True, source_path=plan.source_path,
                companion_path=plan.companion_target_path or '',
                scratchpad_path=plan.scratchpad_target_path or '',
            )
        except OSError as exc:
            return WorkspaceOperationResult(False, plan.target_path, str(exc), committed=False, source_path=plan.source_path)

    def move_to_trash(self, plan):
        bucket = Path(plan.root).parent / "SystemTrash"
        bucket.mkdir(exist_ok=True)
        primary_target = bucket / plan.source_name
        companion_targets = tuple(
            (source_path, bucket / Path(source_path).name)
            for source_path in (plan.companion_source_path, plan.scratchpad_source_path)
            if source_path
        )
        try:
            if primary_target.exists() or any(target.exists() for _source, target in companion_targets):
                raise FileExistsError("trash collision")
            os.rename(plan.source_path, primary_target)
            for source_path, target_path in companion_targets:
                os.rename(source_path, target_path)
            return WorkspaceOperationResult(
                True, plan.parent_path, committed=True, source_path=plan.source_path,
                companion_path=plan.companion_source_path or "",
                scratchpad_path=plan.scratchpad_source_path or "",
            )
        except OSError as exc:
            return WorkspaceOperationResult(
                False, plan.parent_path, str(exc), committed=not os.path.lexists(plan.source_path),
                source_path=plan.source_path, companion_path=plan.companion_source_path or "",
                scratchpad_path=plan.scratchpad_source_path or "",
            )


class CommittedFailureAdapter:
    def create_new_text_file(self, plan):
        Path(plan.target_path).write_bytes(b"")
        return WorkspaceOperationResult(
            False, plan.target_path, "created but verification failed", committed=True
        )

    def create_new_folder(self, plan):
        Path(plan.target_path).mkdir()
        return WorkspaceOperationResult(
            False, plan.target_path, "created but verification failed", committed=True
        )

    def duplicate_text_file(self, plan):
        Path(plan.target_path).write_bytes(b"partial")
        return WorkspaceOperationResult(
            False, plan.target_path, "copied but verification failed", committed=True,
            source_path=plan.source_path,
        )

    def move_to_trash(self, plan):
        bucket = Path(plan.root).parent / "SystemTrashPartial"
        bucket.mkdir(exist_ok=True)
        os.rename(plan.source_path, bucket / plan.source_name)
        return WorkspaceOperationResult(
            False, plan.parent_path,
            "item trashed but Source Notes companion remains", committed=True,
            source_path=plan.source_path, companion_path=plan.companion_source_path or "",
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
    def add(self, _path):
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
        self.reconciled = []
        self.trash_reconciled = []
        self.trash_confirmed = []
        self.current_document = None
        self.references = WorkspacePathReferenceSnapshot()
        self.workspace_controller = WorkspaceController()
        self.workspace_runtime = WorkspaceApplicationRuntime(
            self.workspace_controller,
            self.view,
            State(),
            may_continue=lambda: True,
            open_document=lambda _path: True,
            open_external=lambda _path: True,
            reveal_external=lambda _path: True,
            record_workspace_root=lambda _root: True,
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
            capture_path_references=lambda: self.references,
            reconcile_rename=lambda plan, refs: self.reconciled.append((plan, refs)) or True,
            current_document_path=lambda: self.current_document,
            confirm_trash=lambda plan, active: self.trash_confirmed.append((plan, active)) or True,
            reconcile_trash=lambda plan, refs: self.trash_reconciled.append((plan, refs)) or True,
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

    def test_new_folder_selected_folder_rescans_selects_without_open_or_unsaved_gate(self):
        self.continue_allowed = False
        self.view.selected = self.view.snapshot.by_relative_path("Drafts")
        self.assertTrue(self.runtime.create_new_folder(self.view.selected, "Research"))
        target = str(self.drafts / "Research")
        self.assertTrue(Path(target).is_dir())
        self.assertEqual(self.opens, [])
        self.assertEqual(self.view.selected_paths[-1], target)
        self.assertIsNotNone(self.workspace_controller.snapshot.by_absolute_path(target))

    def test_new_folder_selected_file_creates_sibling(self):
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        self.assertTrue(self.runtime.create_new_folder(self.view.selected, "SiblingFolder"))
        self.assertTrue((self.drafts / "SiblingFolder").is_dir())

    def test_new_folder_collision_and_invalid_name_fail_closed(self):
        self.view.selected = self.view.snapshot.by_relative_path("Drafts")
        (self.drafts / "ExistingFolder").mkdir()
        self.assertFalse(self.runtime.create_new_folder(self.view.selected, "ExistingFolder"))
        self.assertTrue((self.drafts / "ExistingFolder").is_dir())
        self.assertFalse(self.runtime.create_new_folder(self.view.selected, "../escape"))
        self.assertFalse((self.root.parent / "escape").exists())

    def test_new_folder_no_selection_creates_in_root(self):
        self.assertTrue(self.runtime.create_new_folder(None, "RootFolder"))
        target = self.root / "RootFolder"
        self.assertTrue(target.is_dir())
        self.assertEqual(self.view.selected_paths[-1], str(target))
        self.assertEqual(self.opens, [])

    def test_rename_file_rescans_selects_and_reconciles_without_open_or_unsaved_gate(self):
        self.continue_allowed = False
        source = self.drafts / "Existing.md"
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        self.assertTrue(self.runtime.rename_item(self.view.selected, "Renamed.md"))
        target = self.drafts / "Renamed.md"
        self.assertFalse(source.exists())
        self.assertEqual(target.read_text(encoding="utf-8"), "existing")
        self.assertEqual(self.opens, [])
        self.assertEqual(self.view.selected_paths[-1], str(target))
        self.assertEqual(self.reconciled[-1][0].source_path, str(source))

    def test_rename_folder_preserves_children_and_reconciles_descendant_paths(self):
        folder = self.drafts / "Folder"
        folder.mkdir()
        (folder / "Inside.md").write_text("inside", encoding="utf-8")
        self.workspace_runtime.refresh()
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Folder")
        self.assertTrue(self.runtime.rename_item(self.view.selected, "RenamedFolder"))
        self.assertEqual((self.drafts / "RenamedFolder" / "Inside.md").read_text(encoding="utf-8"), "inside")
        self.assertTrue(self.reconciled[-1][0].source_is_directory)

    def test_rename_requires_selection_and_rejects_collision_and_managed_sidecar(self):
        self.assertFalse(self.runtime.rename_item(None, "Nothing"))
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        (self.drafts / "Collision.md").write_text("collision", encoding="utf-8")
        self.assertFalse(self.runtime.rename_item(self.view.selected, "Collision.md"))
        self.assertEqual((self.drafts / "Existing.md").read_text(encoding="utf-8"), "existing")

        sidecar = self.drafts / "Existing.md.source-notes.md"
        sidecar.write_text("notes", encoding="utf-8")
        self.workspace_runtime.refresh()
        sidecar_item = self.view.snapshot.by_relative_path("Drafts/Existing.md.source-notes.md")
        self.assertFalse(self.runtime.rename_item(sidecar_item, "Other.md"))
        self.assertTrue(sidecar.exists())

    def test_rename_text_file_moves_managed_sidecar(self):
        source = self.drafts / "Existing.md"
        sidecar = Path(str(source) + ".source-notes.md")
        sidecar.write_text("notes", encoding="utf-8")
        self.workspace_runtime.refresh()
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        self.assertTrue(self.runtime.rename_item(self.view.selected, "Chapter.md"))
        self.assertFalse(sidecar.exists())
        self.assertEqual((self.drafts / "Chapter.md.source-notes.md").read_text(encoding="utf-8"), "notes")

    def test_duplicate_regular_text_file_rescans_selects_without_open_or_identity_reconciliation(self):
        source=self.drafts/'Existing.md'
        sidecar=Path(str(source)+'.source-notes.md')
        sidecar.write_text('notes',encoding='utf-8')
        self.view.selected=self.view.snapshot.by_relative_path('Drafts/Existing.md')
        self.continue_allowed=False
        self.assertTrue(self.runtime.duplicate_text_file(self.view.selected))
        target=self.drafts/'Existing copy.md'
        self.assertEqual(target.read_text(encoding='utf-8'),'existing')
        self.assertEqual(Path(str(target)+'.source-notes.md').read_text(encoding='utf-8'),'notes')
        self.assertEqual(self.opens,[])
        self.assertEqual(self.reconciled,[])
        self.assertEqual(self.view.selected_paths,[str(target)])

    def test_duplicate_uses_next_available_name_without_overwrite(self):
        (self.drafts/'Existing copy.md').write_text('first',encoding='utf-8')
        self.workspace_runtime.refresh()
        self.view.selected=self.view.snapshot.by_relative_path('Drafts/Existing.md')
        self.assertTrue(self.runtime.duplicate_text_file(self.view.selected))
        self.assertEqual((self.drafts/'Existing copy.md').read_text(encoding='utf-8'),'first')
        self.assertEqual((self.drafts/'Existing copy 2.md').read_text(encoding='utf-8'),'existing')

    def test_duplicate_rejects_folder_non_text_and_managed_sidecar(self):
        (self.drafts/'Image.png').write_bytes(b'png')
        sidecar=self.drafts/'Existing.md.source-notes.md'
        sidecar.write_text('notes',encoding='utf-8')
        self.workspace_runtime.refresh()
        for rel in ('Drafts','Drafts/Image.png','Drafts/Existing.md.source-notes.md'):
            with self.subTest(rel=rel):
                self.errors.clear()
                item=self.view.snapshot.by_relative_path(rel)
                self.assertFalse(self.runtime.duplicate_text_file(item))
                self.assertTrue(self.errors)

    def test_move_regular_text_file_and_sidecar_to_trash_reconciles_and_selects_parent(self):
        source = self.drafts / "Existing.md"
        sidecar = Path(str(source) + ".source-notes.md")
        sidecar.write_text("notes", encoding="utf-8")
        self.workspace_runtime.refresh()
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        self.references = WorkspacePathReferenceSnapshot(
            recent_files=(str(source),), favourites=(str(source),)
        )
        self.assertTrue(self.runtime.move_to_trash(self.view.selected))
        self.assertFalse(source.exists())
        self.assertFalse(sidecar.exists())
        self.assertEqual(self.view.selected_paths[-1], str(self.drafts))
        self.assertFalse(self.trash_confirmed[-1][1])
        self.assertEqual(self.trash_reconciled[-1][0].source_path, str(source))

    def test_move_folder_to_trash_marks_active_descendant_for_detach(self):
        folder = self.drafts / "Book"
        folder.mkdir()
        active = folder / "Chapter.md"
        active.write_text("chapter", encoding="utf-8")
        self.workspace_runtime.refresh()
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Book")
        self.current_document = str(active)
        self.assertTrue(self.runtime.move_to_trash(self.view.selected))
        self.assertFalse(folder.exists())
        self.assertTrue(self.trash_confirmed[-1][1])
        self.assertTrue(self.trash_reconciled[-1][0].source_is_directory)

    def test_trash_cancel_precedes_filesystem_mutation(self):
        source = self.drafts / "Existing.md"
        self.view.selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        runtime = WorkspaceMutationRuntime(
            self.mutation_controller, self.workspace_runtime, self.view,
            may_continue=lambda: True, open_document=lambda _path: True,
            report_error=self.errors.append,
            confirm_trash=lambda _plan, _active: False,
        )
        self.assertFalse(runtime.move_to_trash(self.view.selected))
        self.assertTrue(source.exists())

    def test_committed_partial_trash_still_reconciles_and_reports(self):
        source = self.drafts / "Existing.md"
        sidecar = Path(str(source) + ".source-notes.md")
        sidecar.write_text("notes", encoding="utf-8")
        self.workspace_runtime.refresh()
        selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        controller = WorkspaceMutationController(
            self.workspace_controller, CommittedFailureAdapter()
        )
        reconciled = []
        runtime = WorkspaceMutationRuntime(
            controller, self.workspace_runtime, self.view,
            may_continue=lambda: True, open_document=lambda _path: True,
            report_error=self.errors.append,
            reconcile_trash=lambda plan, refs: reconciled.append((plan, refs)) or True,
            confirm_trash=lambda _plan, _active: True,
        )
        self.assertFalse(runtime.move_to_trash(selected))
        self.assertFalse(source.exists())
        self.assertTrue(sidecar.exists())
        self.assertTrue(reconciled)
        self.assertIn("companion remains", self.errors[-1])

    def test_trash_rejects_no_selection_symlink_and_managed_sidecar(self):
        self.assertFalse(self.runtime.move_to_trash(None))
        sidecar = self.drafts / "Existing.md.source-notes.md"
        sidecar.write_text("notes", encoding="utf-8")
        outside = Path(self.tmp.name) / "Outside.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            (self.drafts / "Link.md").symlink_to(outside)
        except OSError:
            pass
        self.workspace_runtime.refresh()
        for rel in ("Drafts/Existing.md.source-notes.md", "Drafts/Link.md"):
            item = self.view.snapshot.by_relative_path(rel)
            if item is None:
                continue
            self.errors.clear()
            self.assertFalse(self.runtime.move_to_trash(item))
            self.assertTrue(self.errors)

    def test_rename_text_file_moves_source_notes_and_scratchpad_sidecars(self):
        source = self.drafts / "Existing.md"
        source_notes = Path(str(source) + ".source-notes.md")
        scratchpad = Path(str(source) + ".scratchpad.md")
        source_notes.write_text("notes", encoding="utf-8")
        scratchpad.write_text("scratch", encoding="utf-8")
        self.workspace_runtime.refresh()
        selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        self.assertTrue(self.runtime.rename_item(selected, "Chapter.md"))
        self.assertFalse(source_notes.exists())
        self.assertFalse(scratchpad.exists())
        self.assertEqual(
            (self.drafts / "Chapter.md.source-notes.md").read_text(encoding="utf-8"),
            "notes",
        )
        self.assertEqual(
            (self.drafts / "Chapter.md.scratchpad.md").read_text(encoding="utf-8"),
            "scratch",
        )

    def test_duplicate_text_file_copies_source_notes_and_scratchpad_sidecars(self):
        source = self.drafts / "Existing.md"
        Path(str(source) + ".source-notes.md").write_text("notes", encoding="utf-8")
        Path(str(source) + ".scratchpad.md").write_text("scratch", encoding="utf-8")
        self.workspace_runtime.refresh()
        selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        self.assertTrue(self.runtime.duplicate_text_file(selected))
        target = self.drafts / "Existing copy.md"
        self.assertEqual(Path(str(target) + ".source-notes.md").read_text(encoding="utf-8"), "notes")
        self.assertEqual(Path(str(target) + ".scratchpad.md").read_text(encoding="utf-8"), "scratch")

    def test_move_to_trash_carries_source_notes_and_scratchpad_sidecars(self):
        source = self.drafts / "Existing.md"
        source_notes = Path(str(source) + ".source-notes.md")
        scratchpad = Path(str(source) + ".scratchpad.md")
        source_notes.write_text("notes", encoding="utf-8")
        scratchpad.write_text("scratch", encoding="utf-8")
        self.workspace_runtime.refresh()
        selected = self.view.snapshot.by_relative_path("Drafts/Existing.md")
        self.assertTrue(self.runtime.move_to_trash(selected))
        self.assertFalse(source.exists())
        self.assertFalse(source_notes.exists())
        self.assertFalse(scratchpad.exists())

    def test_both_managed_sidecars_are_non_openable_and_direct_mutations_fail(self):
        source = self.drafts / "Existing.md"
        for suffix in (".source-notes.md", ".scratchpad.md"):
            Path(str(source) + suffix).write_text("managed", encoding="utf-8")
        self.workspace_runtime.refresh()
        for suffix in (".source-notes.md", ".scratchpad.md"):
            relative = "Drafts/Existing.md" + suffix
            item = self.view.snapshot.by_relative_path(relative)
            self.assertIsNotNone(item)
            self.assertTrue(item.managed_sidecar)
            self.assertFalse(item.internal_text)
            self.errors.clear()
            self.assertFalse(self.runtime.rename_item(item, "Other.md"))
            self.assertFalse(self.runtime.duplicate_text_file(item))
            self.assertFalse(self.runtime.move_to_trash(item))
            self.assertTrue(self.errors)


if __name__ == "__main__":
    unittest.main()
