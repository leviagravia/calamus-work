"""Planning, execution and reconciliation for bounded Workspace mutations."""
from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any

from calamus_workspace import WorkspaceError, WorkspaceItem, path_is_within_root
from calamus_workspace_controller import WorkspaceController
from calamus_workspace_gio import WorkspaceGioAdapter, WorkspaceOperationResult
from calamus_workspace_operations import WorkspaceOperationPlan, plan_new_text_file


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

    def execute(self, plan: WorkspaceOperationPlan) -> WorkspaceOperationResult:
        return self._adapter.create_new_text_file(plan)


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
