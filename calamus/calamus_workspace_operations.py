"""Pure planning primitives for bounded Writing Workspace mutations.

The planner never touches GTK and never mutates the filesystem.  It accepts a
canonical root, a verified parent directory and user input, then returns one
immutable operation plan.  GIO execution and application reconciliation live
in separate modules.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

ALLOWED_TEXT_SUFFIXES = frozenset({".txt", ".md"})
DEFAULT_TEXT_SUFFIX = ".txt"
MAX_BASENAME_BYTES = 255


class WorkspaceOperationError(ValueError):
    """Raised when a Workspace mutation request is unsafe or ambiguous."""


@dataclass(frozen=True)
class WorkspaceOperationPlan:
    kind: str
    root: str
    parent_path: str
    target_path: str
    display_name: str
    open_after_commit: bool = False


def normalize_text_suffix(suffix: str) -> str:
    if not isinstance(suffix, str):
        raise TypeError("suffix must be a string")
    normalized = suffix.strip().casefold()
    if normalized and not normalized.startswith("."):
        normalized = f".{normalized}"
    if normalized not in ALLOWED_TEXT_SUFFIXES:
        raise WorkspaceOperationError("New Workspace files must use .txt or .md.")
    return normalized


def _normalize_visible_component(raw_name: str, *, label: str) -> str:
    if not isinstance(raw_name, str):
        raise TypeError(f"{label} must be a string")
    name = raw_name.strip()
    if not name:
        raise WorkspaceOperationError(f"Enter a {label}.")
    if "\x00" in name:
        raise WorkspaceOperationError(f"The {label} contains an invalid character.")
    separators = {os.sep, "/", "\\"}
    if os.altsep:
        separators.add(os.altsep)
    if any(separator and separator in name for separator in separators):
        raise WorkspaceOperationError(f"Enter one {label}, not a path.")
    if name in {".", ".."} or name.startswith("."):
        raise WorkspaceOperationError(f"Hidden or reserved {label}s are not allowed here.")
    if len(os.fsencode(name)) > MAX_BASENAME_BYTES:
        raise WorkspaceOperationError(f"The {label} is too long for the filesystem.")
    return name


def normalize_workspace_folder_name(raw_name: str) -> str:
    """Return one safe visible directory basename with no path semantics."""
    return _normalize_visible_component(raw_name, label="folder name")


def normalize_workspace_basename(raw_name: str, *, suffix: str = DEFAULT_TEXT_SUFFIX) -> str:
    """Return one safe visible filename, appending an allowed suffix if needed."""
    name = _normalize_visible_component(raw_name, label="file name")

    requested_suffix = Path(name).suffix.casefold()
    if requested_suffix:
        if requested_suffix not in ALLOWED_TEXT_SUFFIXES:
            raise WorkspaceOperationError("New Workspace files must use .txt or .md.")
        final_name = name
    else:
        final_name = f"{name}{normalize_text_suffix(suffix)}"

    if len(os.fsencode(final_name)) > MAX_BASENAME_BYTES:
        raise WorkspaceOperationError("The file name is too long for the filesystem.")
    return final_name


def plan_new_text_file(
    root: str,
    parent_path: str,
    raw_name: str,
    *,
    suffix: str = DEFAULT_TEXT_SUFFIX,
) -> WorkspaceOperationPlan:
    """Build one root-confined, no-overwrite New Text File plan.

    The caller must have already verified that ``root`` and ``parent_path``
    identify current directories.  This function performs lexical confinement
    and input validation only, keeping filesystem I/O out of the planner.
    """
    for value, label in ((root, "root"), (parent_path, "parent path")):
        if not isinstance(value, str) or not value.strip():
            raise WorkspaceOperationError(f"A valid {label} is required.")

    canonical_root = os.path.abspath(root)
    canonical_parent = os.path.abspath(parent_path)
    try:
        if os.path.commonpath((canonical_root, canonical_parent)) != canonical_root:
            raise WorkspaceOperationError("The destination resolves outside the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError("The destination is not compatible with the Writing Workspace root.") from exc

    display_name = normalize_workspace_basename(raw_name, suffix=suffix)
    target_path = os.path.abspath(os.path.join(canonical_parent, display_name))
    try:
        if os.path.commonpath((canonical_root, target_path)) != canonical_root:
            raise WorkspaceOperationError("The new file would escape the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError("The new file destination is invalid.") from exc

    return WorkspaceOperationPlan(
        kind="new-text-file",
        root=canonical_root,
        parent_path=canonical_parent,
        target_path=target_path,
        display_name=display_name,
        open_after_commit=True,
    )


def plan_new_folder(
    root: str,
    parent_path: str,
    raw_name: str,
) -> WorkspaceOperationPlan:
    """Build one root-confined, single-level New Folder plan.

    The operation never accepts a path and never implies mkdir -p semantics.
    The GIO boundary performs the current filesystem and symlink checks.
    """
    for value, label in ((root, "root"), (parent_path, "parent path")):
        if not isinstance(value, str) or not value.strip():
            raise WorkspaceOperationError(f"A valid {label} is required.")

    canonical_root = os.path.abspath(root)
    canonical_parent = os.path.abspath(parent_path)
    try:
        if os.path.commonpath((canonical_root, canonical_parent)) != canonical_root:
            raise WorkspaceOperationError("The destination resolves outside the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError(
            "The destination is not compatible with the Writing Workspace root."
        ) from exc

    display_name = normalize_workspace_folder_name(raw_name)
    target_path = os.path.abspath(os.path.join(canonical_parent, display_name))
    try:
        if os.path.commonpath((canonical_root, target_path)) != canonical_root:
            raise WorkspaceOperationError("The new folder would escape the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError("The new folder destination is invalid.") from exc

    return WorkspaceOperationPlan(
        kind="new-folder",
        root=canonical_root,
        parent_path=canonical_parent,
        target_path=target_path,
        display_name=display_name,
        open_after_commit=False,
    )
