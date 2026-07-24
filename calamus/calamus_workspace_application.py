"""Application action manager for Writing Workspace semantic events."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calamus_workspace import WorkspaceItem
from calamus_workspace_controller import WorkspaceController


class WorkspaceApplicationRuntime:
    def __init__(
        self,
        controller: WorkspaceController,
        view: Any,
        state: Any,
        *,
        may_continue: Callable[[], bool],
        open_document: Callable[[str], bool],
        open_external: Callable[[str], bool],
        reveal_external: Callable[[str], bool],
        save_settings: Callable[[dict], bool],
        report_error: Callable[[str], None],
        on_root_changed: Callable[[str | None], None],
        on_recent_changed: Callable[[], None],
    ) -> None:
        for callback in (may_continue, open_document, open_external, reveal_external,
                         save_settings, report_error, on_root_changed, on_recent_changed):
            if not callable(callback):
                raise TypeError("workspace application callbacks must be callable")
        self._controller = controller
        self._view = view
        self._state = state
        self._may_continue = may_continue
        self._open_document = open_document
        self._open_external = open_external
        self._reveal_external = reveal_external
        self._save_settings = save_settings
        self._report_error = report_error
        self._on_root_changed = on_root_changed
        self._on_recent_changed = on_recent_changed

    @property
    def root(self) -> str | None:
        return self._controller.root

    def bind_startup_root(self, root: str | None) -> bool:
        if not root:
            self._view.render(None)
            return False
        return self.open_root(root, persist=False)

    def open_root(self, root: str, *, persist: bool = True) -> bool:
        try:
            snapshot = self._controller.bind_root(root)
        except (OSError, TypeError, ValueError) as exc:
            self._report_error(str(exc))
            return False
        self._view.render(snapshot)
        self._on_root_changed(snapshot.root)
        if persist:
            self._state.add_recent_workspace(snapshot.root)
            self._on_recent_changed()
            if not self._save_settings({"workspace_root": snapshot.root}):
                self._report_error("The folder opened, but the Writing Workspace setting could not be saved.")
        return True

    def close_root(self) -> bool:
        self._controller.clear()
        self._view.render(None)
        self._on_root_changed(None)
        return self._save_settings({"workspace_root": None})

    def refresh(self) -> bool:
        try:
            snapshot = self._controller.refresh()
        except (OSError, TypeError, ValueError) as exc:
            self._report_error(str(exc))
            return False
        self._view.render(snapshot)
        return snapshot is not None

    def activate_item(self, item: WorkspaceItem) -> bool:
        try:
            activation = self._controller.activation_for(item)
        except (OSError, TypeError, ValueError) as exc:
            self._report_error(str(exc))
            return False
        if activation.kind == "directory":
            return True
        if activation.kind in ("blocked", "missing"):
            self._report_error(activation.message)
            return False
        if activation.kind == "internal":
            if not self._may_continue():
                return False
            success = bool(self._open_document(activation.path))
        else:
            success = bool(self._open_external(activation.path))
        if not success:
            self._report_error("The selected Workspace file could not be opened.")
        return success

    def reveal(self) -> bool:
        target = self._controller.root
        selected = self._view.selected_item()
        if selected is not None:
            target = selected.path
        if not target:
            self._report_error("No Writing Workspace is selected.")
            return False
        success = bool(self._reveal_external(target))
        if not success:
            self._report_error("The Writing Workspace could not be revealed in the system file manager.")
        return success
