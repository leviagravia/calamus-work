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


@dataclass(frozen=True)
class WorkspacePathToken:
    device: int
    inode: int
    mode: int


@dataclass(frozen=True)
class WorkspaceRenamePlan:
    kind: str
    root: str
    parent_path: str
    source_path: str
    target_path: str
    source_name: str
    display_name: str
    source_is_directory: bool
    source_token: WorkspacePathToken
    companion_source_path: str | None = None
    companion_target_path: str | None = None
    companion_token: WorkspacePathToken | None = None
    managed_target_path: str | None = None


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


def normalize_workspace_rename_name(raw_name: str) -> str:
    """Return one visible basename for a file or folder rename."""
    return _normalize_visible_component(raw_name, label="new name")


def plan_workspace_rename(
    root: str,
    source_path: str,
    raw_name: str,
    *,
    source_is_directory: bool,
    source_token: WorkspacePathToken,
    companion_source_path: str | None = None,
    companion_token: WorkspacePathToken | None = None,
    manage_source_notes: bool = False,
) -> WorkspaceRenamePlan:
    """Build one same-parent, root-confined rename plan without I/O.

    A document Source Notes sidecar may be included as a managed companion.
    The GIO boundary revalidates every identity immediately before commit.
    """
    if not isinstance(root, str) or not root.strip():
        raise WorkspaceOperationError("A valid root is required.")
    if not isinstance(source_path, str) or not source_path.strip():
        raise WorkspaceOperationError("Select one Workspace file or folder to rename.")
    if not isinstance(source_is_directory, bool):
        raise TypeError("source_is_directory must be boolean")
    if not isinstance(source_token, WorkspacePathToken):
        raise TypeError("source_token must be WorkspacePathToken")

    canonical_root = os.path.abspath(root)
    canonical_source = os.path.abspath(source_path)
    parent = os.path.dirname(canonical_source)
    try:
        if canonical_source == canonical_root or os.path.commonpath((canonical_root, canonical_source)) != canonical_root:
            raise WorkspaceOperationError("The Workspace root itself cannot be renamed here.")
        if os.path.commonpath((canonical_root, parent)) != canonical_root:
            raise WorkspaceOperationError("The selected item resolves outside the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError("The selected item is incompatible with the Workspace root.") from exc

    source_name = os.path.basename(canonical_source)
    if source_name.endswith(".source-notes.md"):
        raise WorkspaceOperationError("Rename the document, not its managed Source Notes sidecar.")
    display_name = normalize_workspace_rename_name(raw_name)
    if display_name.endswith(".source-notes.md"):
        raise WorkspaceOperationError("That suffix is reserved for managed Source Notes sidecars.")
    if display_name == source_name:
        raise WorkspaceOperationError("The new name is unchanged.")
    target = os.path.abspath(os.path.join(parent, display_name))
    try:
        if os.path.dirname(target) != parent or os.path.commonpath((canonical_root, target)) != canonical_root:
            raise WorkspaceOperationError("The renamed item would escape the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError("The rename destination is invalid.") from exc

    companion_target = None
    if companion_source_path is not None:
        companion_source = os.path.abspath(companion_source_path)
        expected_companion = canonical_source + ".source-notes.md"
        if companion_source != expected_companion or companion_token is None:
            raise WorkspaceOperationError("The managed Source Notes companion is inconsistent.")
        companion_target = target + ".source-notes.md"
    else:
        companion_source = None
        if companion_token is not None:
            raise WorkspaceOperationError("A companion token requires a companion path.")
    managed_target = target + ".source-notes.md" if manage_source_notes else None
    if companion_target is not None and managed_target != companion_target:
        raise WorkspaceOperationError("The managed Source Notes destination is inconsistent.")

    return WorkspaceRenamePlan(
        kind="rename",
        root=canonical_root,
        parent_path=parent,
        source_path=canonical_source,
        target_path=target,
        source_name=source_name,
        display_name=display_name,
        source_is_directory=source_is_directory,
        source_token=source_token,
        companion_source_path=companion_source,
        companion_target_path=companion_target,
        companion_token=companion_token,
        managed_target_path=managed_target,
    )
