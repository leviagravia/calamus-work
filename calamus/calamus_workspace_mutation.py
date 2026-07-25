"""Planning, execution and reconciliation for bounded Workspace mutations."""
from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any

from calamus_workspace import WorkspaceError, WorkspaceItem, path_is_within_root
from calamus_workspace_controller import WorkspaceController
from calamus_workspace_gio import WorkspaceGioAdapter, WorkspaceOperationResult
from calamus_workspace_identity import WorkspacePathReferenceSnapshot, path_is_trashed
from calamus_workspace_operations import (
    WorkspaceContentToken, WorkspaceDuplicatePlan, WorkspaceOperationPlan,
    WorkspacePathToken, WorkspaceRenamePlan, WorkspaceTrashPlan,
    plan_duplicate_text_file, plan_move_to_trash, plan_new_folder,
    plan_new_text_file, plan_workspace_rename,
)


class WorkspaceMutationController:
    """Resolve current selection, build a pure plan, then delegate to GIO."""

    def __init__(
        self,
        workspace: WorkspaceController,
        adapter: WorkspaceGioAdapter | None = None,
    ) -> None:
        if not isinstance(workspace, WorkspaceController):
            raise TypeError("workspace must be WorkspaceController")
        self._workspace = workspace
        self._adapter = adapter or WorkspaceGioAdapter()

    def destination_for_selection(self, selected: WorkspaceItem | None) -> str:
        root = self._workspace.root
        if not root:
            raise WorkspaceError("Select a Writing Workspace folder first.")

        parent = root
        if selected is not None:
            current = self._workspace.current_item(selected)
            if current.is_symlink or os.path.islink(current.path):
                raise WorkspaceError("A symbolic link cannot be used as a creation destination.")
            parent = current.path if current.is_directory else os.path.dirname(current.path)

        if os.path.islink(parent):
            raise WorkspaceError("A symbolic-link folder cannot be used as a creation destination.")
        if not os.path.isdir(parent):
            raise WorkspaceError("The selected destination folder no longer exists.")
        if not path_is_within_root(root, parent):
            raise WorkspaceError("The selected destination resolves outside the Writing Workspace.")
        return parent

    def plan_new_text_file(
        self,
        selected: WorkspaceItem | None,
        raw_name: str,
        *,
        suffix: str,
    ) -> WorkspaceOperationPlan:
        root = self._workspace.root
        parent = self.destination_for_selection(selected)
        return plan_new_text_file(root, parent, raw_name, suffix=suffix)

    def plan_new_folder(
        self,
        selected: WorkspaceItem | None,
        raw_name: str,
    ) -> WorkspaceOperationPlan:
        root = self._workspace.root
        parent = self.destination_for_selection(selected)
        return plan_new_folder(root, parent, raw_name)

    @staticmethod
    def _path_token(path: str) -> WorkspacePathToken:
        stat_result = os.lstat(path)
        return WorkspacePathToken(stat_result.st_dev, stat_result.st_ino, stat_result.st_mode)

    @staticmethod
    def _content_token(path: str) -> WorkspaceContentToken:
        stat_result = os.lstat(path)
        return WorkspaceContentToken(
            stat_result.st_dev, stat_result.st_ino, stat_result.st_mode,
            stat_result.st_size, stat_result.st_mtime_ns,
        )

    def plan_duplicate(
        self, selected: WorkspaceItem | None
    ) -> WorkspaceDuplicatePlan:
        if selected is None:
            raise WorkspaceError("Select one .txt or .md Workspace file to duplicate.")
        current = self._workspace.current_item(selected)
        if current.is_directory:
            raise WorkspaceError("Folder duplication is outside Writing Workspace scope.")
        if current.is_symlink or os.path.islink(current.path):
            raise WorkspaceError("Symbolic links cannot be duplicated from Writing Workspace.")
        if not current.internal_text or not os.path.isfile(current.path):
            raise WorkspaceError("Only regular .txt and .md Workspace files can be duplicated.")
        if current.name.endswith(".source-notes.md"):
            raise WorkspaceError("Duplicate the document, not its managed Source Notes sidecar.")
        parent = os.path.dirname(current.path)
        try:
            occupied_names = tuple(os.listdir(parent))
        except OSError as exc:
            raise WorkspaceError(f"The containing folder cannot be read: {exc}") from exc
        companion_path = None
        companion_token = None
        candidate = current.path + ".source-notes.md"
        if os.path.lexists(candidate):
            if os.path.islink(candidate) or not os.path.isfile(candidate):
                raise WorkspaceError("The managed Source Notes sidecar is not a regular file.")
            companion_path = candidate
            companion_token = self._content_token(candidate)
        return plan_duplicate_text_file(
            self._workspace.root, current.path, occupied_names,
            source_token=self._content_token(current.path),
            companion_source_path=companion_path, companion_token=companion_token,
        )

    def plan_move_to_trash(
        self, selected: WorkspaceItem | None
    ) -> WorkspaceTrashPlan:
        if selected is None:
            raise WorkspaceError("Select one Workspace file or folder to move to Trash.")
        current = self._workspace.current_item(selected)
        if current.is_symlink or os.path.islink(current.path):
            raise WorkspaceError("Symbolic links cannot be moved to Trash from Writing Workspace.")
        if not current.is_directory and not os.path.isfile(current.path):
            raise WorkspaceError("Only regular files and folders can be moved to Trash.")
        if current.name.endswith(".source-notes.md"):
            raise WorkspaceError(
                "Move the document to Trash, not its managed Source Notes sidecar."
            )
        companion_path = None
        companion_token = None
        if current.internal_text and not current.is_directory:
            candidate = current.path + ".source-notes.md"
            if os.path.lexists(candidate):
                if os.path.islink(candidate) or not os.path.isfile(candidate):
                    raise WorkspaceError("The managed Source Notes sidecar is not a regular file.")
                companion_path = candidate
                companion_token = self._path_token(candidate)
        return plan_move_to_trash(
            self._workspace.root, current.path,
            source_is_directory=current.is_directory,
            source_token=self._path_token(current.path),
            companion_source_path=companion_path,
            companion_token=companion_token,
        )

    def plan_rename(
        self, selected: WorkspaceItem | None, raw_name: str
    ) -> WorkspaceRenamePlan:
        if selected is None:
            raise WorkspaceError("Select one Workspace file or folder to rename.")
        current = self._workspace.current_item(selected)
        if current.is_symlink or os.path.islink(current.path):
            raise WorkspaceError("Symbolic links cannot be renamed from Writing Workspace.")
        if not current.is_directory and not os.path.isfile(current.path):
            raise WorkspaceError("Only regular files and folders can be renamed.")
        companion_path = None
        companion_token = None
        if current.internal_text and not current.is_directory:
            candidate = current.path + ".source-notes.md"
            if os.path.lexists(candidate):
                if os.path.islink(candidate) or not os.path.isfile(candidate):
                    raise WorkspaceError("The managed Source Notes sidecar is not a regular file.")
                companion_path = candidate
                companion_token = self._path_token(candidate)
        return plan_workspace_rename(
            self._workspace.root, current.path, raw_name,
            source_is_directory=current.is_directory,
            source_token=self._path_token(current.path),
            companion_source_path=companion_path,
            companion_token=companion_token,
            manage_source_notes=bool(current.internal_text and not current.is_directory),
        )

    def execute(
        self, plan: WorkspaceOperationPlan | WorkspaceRenamePlan | WorkspaceDuplicatePlan | WorkspaceTrashPlan
    ) -> WorkspaceOperationResult:
        if plan.kind == "new-text-file":
            return self._adapter.create_new_text_file(plan)
        if plan.kind == "new-folder":
            return self._adapter.create_new_folder(plan)
        if plan.kind == "rename":
            return self._adapter.rename_item(plan)
        if plan.kind == "duplicate-text-file":
            return self._adapter.duplicate_text_file(plan)
        if plan.kind == "move-to-trash":
            return self._adapter.move_to_trash(plan)
        raise ValueError(f"unsupported Workspace operation: {plan.kind}")


class WorkspaceMutationRuntime:
    """Application lifecycle around one confirmed Workspace mutation."""

    def __init__(
        self,
        controller: WorkspaceMutationController,
        workspace_runtime: Any,
        view: Any,
        *,
        may_continue: Callable[[], bool],
        open_document: Callable[[str], bool],
        report_error: Callable[[str], None],
        capture_path_references: Callable[[], WorkspacePathReferenceSnapshot] | None = None,
        reconcile_rename: Callable[[WorkspaceRenamePlan, WorkspacePathReferenceSnapshot], bool] | None = None,
        current_document_path: Callable[[], str | None] | None = None,
        confirm_trash: Callable[[WorkspaceTrashPlan, bool], bool] | None = None,
        reconcile_trash: Callable[[WorkspaceTrashPlan, WorkspacePathReferenceSnapshot], bool] | None = None,
    ) -> None:
        if not isinstance(controller, WorkspaceMutationController):
            raise TypeError("controller must be WorkspaceMutationController")
        for callback in (may_continue, open_document, report_error):
            if not callable(callback):
                raise TypeError("Workspace mutation callbacks must be callable")
        self._controller = controller
        self._workspace_runtime = workspace_runtime
        self._view = view
        self._may_continue = may_continue
        self._open_document = open_document
        self._report_error = report_error
        self._capture_path_references = capture_path_references or (lambda: WorkspacePathReferenceSnapshot())
        self._reconcile_rename = reconcile_rename or (lambda _plan, _references: True)
        self._current_document_path = current_document_path or (lambda: None)
        self._confirm_trash = confirm_trash or (lambda _plan, _active: True)
        self._reconcile_trash = reconcile_trash or (lambda _plan, _references: True)
        for callback in (
            self._capture_path_references, self._reconcile_rename,
            self._current_document_path, self._confirm_trash, self._reconcile_trash,
        ):
            if not callable(callback):
                raise TypeError("Workspace mutation reconciliation callbacks must be callable")

    def create_new_text_file(
        self,
        selected: WorkspaceItem | None,
        raw_name: str,
        *,
        suffix: str,
    ) -> bool:
        try:
            plan = self._controller.plan_new_text_file(selected, raw_name, suffix=suffix)
        except (OSError, TypeError, ValueError) as exc:
            self._report_error(str(exc))
            return False

        # The new file is opened immediately after creation.  Resolve the
        # current document's unsaved state before any filesystem mutation, so
        # Cancel cannot leave an unwanted empty file behind.
        if not self._may_continue():
            return False

        result = self._controller.execute(plan)
        if not result.success:
            if result.committed:
                self._workspace_runtime.refresh()
                self._view.select_path(result.path)
            self._report_error(result.message or "The text file could not be created.")
            return False

        if not self._workspace_runtime.refresh():
            self._report_error(
                "The text file was created, but the Writing Workspace could not be rescanned."
            )
            return False
        self._view.select_path(result.path)

        if plan.open_after_commit and not self._open_document(result.path):
            self._report_error(
                "The text file was created, but it could not be opened in Calamus."
            )
            return False
        return True

    def create_new_folder(
        self,
        selected: WorkspaceItem | None,
        raw_name: str,
    ) -> bool:
        try:
            plan = self._controller.plan_new_folder(selected, raw_name)
        except (OSError, TypeError, ValueError) as exc:
            self._report_error(str(exc))
            return False

        # New Folder does not replace the active document.  Therefore it must
        # not invoke the unsaved-document gate merely to mutate the tree.
        result = self._controller.execute(plan)
        if not result.success:
            if result.committed:
                self._workspace_runtime.refresh()
                self._view.select_path(result.path)
            self._report_error(result.message or "The folder could not be created.")
            return False

        if not self._workspace_runtime.refresh():
            self._report_error(
                "The folder was created, but the Writing Workspace could not be rescanned."
            )
            return False
        self._view.select_path(result.path)
        return True


    def duplicate_text_file(self, selected: WorkspaceItem | None) -> bool:
        try:
            plan = self._controller.plan_duplicate(selected)
        except (OSError, TypeError, ValueError) as exc:
            self._report_error(str(exc))
            return False

        # Duplication copies the saved bytes on disk.  It neither replaces the
        # active editor document nor transfers its identity, so unsaved buffer
        # content remains attached to the original and no may_continue gate runs.
        result = self._controller.execute(plan)
        if not result.success:
            if result.committed:
                self._workspace_runtime.refresh()
                self._view.select_path(result.path)
            self._report_error(result.message or "The selected text file could not be duplicated.")
            return False
        if not self._workspace_runtime.refresh():
            self._report_error(
                "The file was duplicated, but the Writing Workspace could not be rescanned."
            )
            return False
        self._view.select_path(result.path)
        return True

    def move_to_trash(self, selected: WorkspaceItem | None) -> bool:
        try:
            plan = self._controller.plan_move_to_trash(selected)
            references = self._capture_path_references()
            if not isinstance(references, WorkspacePathReferenceSnapshot):
                raise TypeError(
                    "capture_path_references must return WorkspacePathReferenceSnapshot"
                )
            current_document = self._current_document_path()
            if current_document is not None and not isinstance(current_document, str):
                raise TypeError("current_document_path must return a string or None")
            active_affected = path_is_trashed(
                current_document, plan.source_path,
                source_is_directory=plan.source_is_directory,
            )
        except (OSError, TypeError, ValueError) as exc:
            self._report_error(str(exc))
            return False

        if not self._confirm_trash(plan, active_affected):
            return False

        result = self._controller.execute(plan)
        if not result.committed:
            self._report_error(result.message or "The selected item could not be moved to Trash.")
            return False

        # Once GIO has removed the original identity, application references
        # must be reconciled even if the sidecar step or the visual rescan fails.
        reconciled = self._reconcile_trash(plan, references)
        refreshed = bool(self._workspace_runtime.refresh())
        if refreshed:
            self._view.select_path(plan.parent_path)

        if not result.success:
            self._report_error(result.message or "The Trash operation completed only partially.")
            return False
        if not reconciled:
            self._report_error(
                "The item was moved to Trash, but Calamus could not fully reconcile document path references."
            )
            return False
        if not refreshed:
            self._report_error(
                "The item was moved to Trash, but the Writing Workspace could not be rescanned."
            )
            return False
        return True

    def rename_item(self, selected: WorkspaceItem | None, raw_name: str) -> bool:
        try:
            plan = self._controller.plan_rename(selected, raw_name)
            references = self._capture_path_references()
            if not isinstance(references, WorkspacePathReferenceSnapshot):
                raise TypeError("capture_path_references must return WorkspacePathReferenceSnapshot")
        except (OSError, TypeError, ValueError) as exc:
            self._report_error(str(exc))
            return False

        # Rename changes filesystem identity but never replaces editor content,
        # so an unsaved document remains active and no save/discard gate runs.
        result = self._controller.execute(plan)
        if not result.success:
            if result.committed:
                self._workspace_runtime.refresh()
                self._view.select_path(result.path)
            self._report_error(result.message or "The selected item could not be renamed.")
            return False

        if not self._workspace_runtime.refresh():
            self._report_error("The item was renamed, but the Writing Workspace could not be rescanned.")
            return False
        self._view.select_path(result.path)
        if not self._reconcile_rename(plan, references):
            self._report_error(
                "The item was renamed, but Calamus could not fully reconcile document path references."
            )
            return False
        return True
