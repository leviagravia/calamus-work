"""GTK-free filesystem model for the read-only Writing Workspace."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

INTERNAL_SUFFIXES = frozenset({".txt", ".md"})
DEFAULT_MAX_ITEMS = 5000
DEFAULT_MAX_DEPTH = 32


class WorkspaceError(ValueError):
    pass


@dataclass(frozen=True)
class WorkspaceItem:
    root: str
    path: str
    relative_path: str
    name: str
    depth: int
    is_directory: bool
    is_symlink: bool
    internal_text: bool


@dataclass(frozen=True)
class WorkspaceSnapshot:
    root: str
    items: tuple[WorkspaceItem, ...]
    diagnostics: tuple[str, ...] = ()

    def by_relative_path(self, relative_path: str) -> WorkspaceItem | None:
        return next((item for item in self.items if item.relative_path == relative_path), None)

    def by_absolute_path(self, path: str) -> WorkspaceItem | None:
        target = os.path.abspath(path)
        return next((item for item in self.items if item.path == target), None)


def normalize_workspace_root(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise WorkspaceError("Choose a non-empty Writing Workspace folder.")
    absolute = os.path.abspath(os.path.expanduser(path.strip()))
    if os.path.islink(absolute):
        raise WorkspaceError("The Writing Workspace root cannot be a symbolic link.")
    if not os.path.isdir(absolute):
        raise WorkspaceError(f"Writing Workspace folder does not exist: {absolute}")
    return absolute


def path_is_within_root(root: str, path: str) -> bool:
    try:
        real_root = os.path.realpath(normalize_workspace_root(root))
        real_path = os.path.realpath(os.path.abspath(path))
        return os.path.commonpath((real_root, real_path)) == real_root
    except (OSError, TypeError, ValueError, WorkspaceError):
        return False


def scan_workspace(
    root: str,
    *,
    max_items: int = DEFAULT_MAX_ITEMS,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> WorkspaceSnapshot:
    canonical_root = normalize_workspace_root(root)
    if not isinstance(max_items, int) or max_items < 1:
        raise ValueError("max_items must be positive")
    if not isinstance(max_depth, int) or max_depth < 0:
        raise ValueError("max_depth must be non-negative")

    items: list[WorkspaceItem] = []
    diagnostics: list[str] = []
    stopped = False

    def visit(directory: str, depth: int) -> None:
        nonlocal stopped
        if stopped:
            return
        if depth > max_depth:
            diagnostics.append(f"Maximum depth {max_depth} reached at {os.path.relpath(directory, canonical_root)}")
            return
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            diagnostics.append(f"Cannot read {os.path.relpath(directory, canonical_root)}: {exc}")
            return
        entries.sort(key=lambda entry: (
            not entry.is_dir(follow_symlinks=False),
            entry.name.casefold(),
            entry.name,
        ))
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if len(items) >= max_items:
                diagnostics.append(f"Workspace scan stopped after {max_items} items.")
                stopped = True
                return
            path = os.path.abspath(entry.path)
            relative = os.path.relpath(path, canonical_root)
            is_symlink = entry.is_symlink()
            is_directory = entry.is_dir(follow_symlinks=False)
            suffix = Path(entry.name).suffix.casefold()
            items.append(WorkspaceItem(
                root=canonical_root,
                path=path,
                relative_path=relative,
                name=entry.name,
                depth=depth,
                is_directory=is_directory,
                is_symlink=is_symlink,
                internal_text=(not is_directory and not is_symlink and suffix in INTERNAL_SUFFIXES),
            ))
            if is_directory and not is_symlink:
                visit(path, depth + 1)

    visit(canonical_root, 0)
    return WorkspaceSnapshot(canonical_root, tuple(items), tuple(diagnostics))


def parent_relative_path(item: WorkspaceItem) -> str | None:
    parent = os.path.dirname(item.relative_path)
    return None if parent in ("", ".") else parent
