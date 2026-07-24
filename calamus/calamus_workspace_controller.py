"""Root authority and safe activation planning for Writing Workspace."""
from __future__ import annotations

from dataclasses import dataclass
import os
from collections.abc import Callable

from calamus_workspace import (
    WorkspaceError,
    WorkspaceItem,
    WorkspaceSnapshot,
    normalize_workspace_root,
    path_is_within_root,
    scan_workspace,
)


@dataclass(frozen=True)
class WorkspaceActivation:
    kind: str
    path: str
    message: str = ""


class WorkspaceController:
    def __init__(self, scanner: Callable[[str], WorkspaceSnapshot] = scan_workspace) -> None:
        if not callable(scanner):
            raise TypeError("scanner must be callable")
        self._scanner = scanner
        self._root: str | None = None
        self._snapshot: WorkspaceSnapshot | None = None

    @property
    def root(self) -> str | None:
        return self._root

    @property
    def snapshot(self) -> WorkspaceSnapshot | None:
        return self._snapshot

    def bind_root(self, root: str) -> WorkspaceSnapshot:
        canonical = normalize_workspace_root(root)
        snapshot = self._scanner(canonical)
        if snapshot.root != canonical:
            raise WorkspaceError("Workspace scanner returned a foreign root.")
        self._root = canonical
        self._snapshot = snapshot
        return snapshot

    def clear(self) -> None:
        self._root = None
        self._snapshot = None

    def refresh(self) -> WorkspaceSnapshot | None:
        if self._root is None:
            return None
        snapshot = self._scanner(self._root)
        if snapshot.root != self._root:
            raise WorkspaceError("Workspace scanner changed the bound root.")
        self._snapshot = snapshot
        return snapshot

    def activation_for(self, item: WorkspaceItem) -> WorkspaceActivation:
        current = self._require_current(item)
        if current.is_directory:
            return WorkspaceActivation("directory", current.path)
        if current.is_symlink or os.path.islink(current.path):
            return WorkspaceActivation("blocked", current.path, "Symbolic links are not opened from the Writing Workspace.")
        if not path_is_within_root(self._root, current.path):
            return WorkspaceActivation("blocked", current.path, "The selected file resolves outside the Writing Workspace.")
        if not os.path.isfile(current.path):
            return WorkspaceActivation("missing", current.path, "The selected file no longer exists.")
        return WorkspaceActivation("internal" if current.internal_text else "external", current.path)

    def _require_current(self, item: WorkspaceItem) -> WorkspaceItem:
        if not isinstance(item, WorkspaceItem):
            raise TypeError("item must be WorkspaceItem")
        if self._root is None or self._snapshot is None:
            raise WorkspaceError("No Writing Workspace is selected.")
        if item.root != self._root:
            raise WorkspaceError("Workspace item belongs to another root.")
        current = self._snapshot.by_absolute_path(item.path)
        if current != item:
            raise WorkspaceError("Workspace item is stale or foreign.")
        return current
