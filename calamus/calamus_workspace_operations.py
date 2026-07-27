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
SOURCE_NOTES_SUFFIX = ".source-notes.md"
SCRATCHPAD_SUFFIX = ".scratchpad.md"
MANAGED_SIDECAR_SUFFIXES = (SOURCE_NOTES_SUFFIX, SCRATCHPAD_SUFFIX)


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
class WorkspaceContentToken:
    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int


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
    scratchpad_source_path: str | None = None
    scratchpad_target_path: str | None = None
    scratchpad_token: WorkspacePathToken | None = None
    managed_scratchpad_target_path: str | None = None


@dataclass(frozen=True)
class WorkspaceDuplicatePlan:
    kind: str
    root: str
    parent_path: str
    source_path: str
    target_path: str
    source_name: str
    display_name: str
    source_token: WorkspaceContentToken
    companion_source_path: str | None = None
    companion_target_path: str | None = None
    companion_token: WorkspaceContentToken | None = None
    scratchpad_source_path: str | None = None
    scratchpad_target_path: str | None = None
    scratchpad_token: WorkspaceContentToken | None = None


@dataclass(frozen=True)
class WorkspaceTrashPlan:
    kind: str
    root: str
    parent_path: str
    source_path: str
    source_name: str
    source_is_directory: bool
    source_token: WorkspacePathToken
    companion_source_path: str | None = None
    companion_token: WorkspacePathToken | None = None
    scratchpad_source_path: str | None = None
    scratchpad_token: WorkspacePathToken | None = None


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
    scratchpad_source_path: str | None = None,
    scratchpad_token: WorkspacePathToken | None = None,
    manage_source_notes: bool = False,
    manage_scratchpad: bool = False,
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
    if any(source_name.casefold().endswith(suffix) for suffix in MANAGED_SIDECAR_SUFFIXES):
        raise WorkspaceOperationError("Rename the document, not one of its managed sidecars.")
    display_name = normalize_workspace_rename_name(raw_name)
    if any(display_name.casefold().endswith(suffix) for suffix in MANAGED_SIDECAR_SUFFIXES):
        raise WorkspaceOperationError("That suffix is reserved for managed document sidecars.")
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
        expected_companion = canonical_source + SOURCE_NOTES_SUFFIX
        if companion_source != expected_companion or companion_token is None:
            raise WorkspaceOperationError("The managed Source Notes companion is inconsistent.")
        companion_target = target + SOURCE_NOTES_SUFFIX
    else:
        companion_source = None
        if companion_token is not None:
            raise WorkspaceOperationError("A Source Notes token requires a Source Notes path.")

    scratchpad_target = None
    if scratchpad_source_path is not None:
        scratchpad_source = os.path.abspath(scratchpad_source_path)
        expected_scratchpad = canonical_source + SCRATCHPAD_SUFFIX
        if scratchpad_source != expected_scratchpad or scratchpad_token is None:
            raise WorkspaceOperationError("The managed Scratchpad companion is inconsistent.")
        scratchpad_target = target + SCRATCHPAD_SUFFIX
    else:
        scratchpad_source = None
        if scratchpad_token is not None:
            raise WorkspaceOperationError("A Scratchpad token requires a Scratchpad path.")

    managed_target = target + SOURCE_NOTES_SUFFIX if manage_source_notes else None
    managed_scratchpad_target = target + SCRATCHPAD_SUFFIX if manage_scratchpad else None
    if companion_target is not None and managed_target != companion_target:
        raise WorkspaceOperationError("The managed Source Notes destination is inconsistent.")
    if scratchpad_target is not None and managed_scratchpad_target != scratchpad_target:
        raise WorkspaceOperationError("The managed Scratchpad destination is inconsistent.")

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
        scratchpad_source_path=scratchpad_source,
        scratchpad_target_path=scratchpad_target,
        scratchpad_token=scratchpad_token,
        managed_scratchpad_target_path=managed_scratchpad_target,
    )

def _truncate_utf8_component(value: str, max_bytes: int) -> str:
    if max_bytes < 1:
        raise WorkspaceOperationError("The duplicate file name cannot fit on this filesystem.")
    candidate = value
    while candidate and len(os.fsencode(candidate)) > max_bytes:
        candidate = candidate[:-1]
    if not candidate:
        raise WorkspaceOperationError("The duplicate file name cannot fit on this filesystem.")
    return candidate


def next_duplicate_text_name(
    source_name: str,
    occupied_names: tuple[str, ...] | list[str],
    *,
    reserve_managed_sidecar: bool = True,
) -> str:
    """Return a deterministic, case-conservative duplicate basename.

    Mature GTK file managers generate a sibling copy name rather than opening a
    second Save As workflow.  Calamus keeps that behavior bounded to one text
    file and treats the managed Source Notes destination as reserved too.
    """
    if not isinstance(source_name, str):
        raise TypeError("source_name must be a string")
    if not isinstance(occupied_names, (tuple, list)) or not all(
        isinstance(name, str) for name in occupied_names
    ):
        raise TypeError("occupied_names must be a tuple or list of strings")
    if not isinstance(reserve_managed_sidecar, bool):
        raise TypeError("reserve_managed_sidecar must be boolean")
    if any(source_name.casefold().endswith(suffix) for suffix in MANAGED_SIDECAR_SUFFIXES):
        raise WorkspaceOperationError("Duplicate the document, not one of its managed sidecars.")
    suffix = Path(source_name).suffix.casefold()
    if suffix not in ALLOWED_TEXT_SUFFIXES:
        raise WorkspaceOperationError("Only regular .txt and .md Workspace files can be duplicated.")
    stem = source_name[:-len(suffix)]
    occupied = {name.casefold() for name in occupied_names}
    for index in range(1, 10001):
        marker = " copy" if index == 1 else f" copy {index}"
        max_stem_bytes = MAX_BASENAME_BYTES - len(os.fsencode(marker + suffix))
        fitted_stem = _truncate_utf8_component(stem, max_stem_bytes)
        candidate = f"{fitted_stem}{marker}{suffix}"
        companions = tuple(candidate + suffix for suffix in MANAGED_SIDECAR_SUFFIXES)
        if candidate.casefold() in occupied:
            continue
        if reserve_managed_sidecar and any(name.casefold() in occupied for name in companions):
            continue
        return candidate
    raise WorkspaceOperationError("No safe duplicate name is available in this folder.")


def plan_duplicate_text_file(
    root: str,
    source_path: str,
    occupied_names: tuple[str, ...] | list[str],
    *,
    source_token: WorkspaceContentToken,
    companion_source_path: str | None = None,
    companion_token: WorkspaceContentToken | None = None,
    scratchpad_source_path: str | None = None,
    scratchpad_token: WorkspaceContentToken | None = None,
) -> WorkspaceDuplicatePlan:
    """Build one same-parent, no-overwrite text-file duplication plan."""
    if not isinstance(root, str) or not root.strip():
        raise WorkspaceOperationError("A valid root is required.")
    if not isinstance(source_path, str) or not source_path.strip():
        raise WorkspaceOperationError("Select one .txt or .md Workspace file to duplicate.")
    if not isinstance(source_token, WorkspaceContentToken):
        raise TypeError("source_token must be WorkspaceContentToken")

    canonical_root = os.path.abspath(root)
    canonical_source = os.path.abspath(source_path)
    parent = os.path.dirname(canonical_source)
    try:
        if canonical_source == canonical_root or os.path.commonpath((canonical_root, canonical_source)) != canonical_root:
            raise WorkspaceOperationError("The selected file resolves outside the Writing Workspace.")
        if os.path.commonpath((canonical_root, parent)) != canonical_root:
            raise WorkspaceOperationError("The duplicate destination resolves outside the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError("The selected file is incompatible with the Workspace root.") from exc

    source_name = os.path.basename(canonical_source)
    display_name = next_duplicate_text_name(
        source_name, occupied_names, reserve_managed_sidecar=True
    )
    target = os.path.abspath(os.path.join(parent, display_name))
    try:
        if os.path.dirname(target) != parent or os.path.commonpath((canonical_root, target)) != canonical_root:
            raise WorkspaceOperationError("The duplicate would escape the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError("The duplicate destination is invalid.") from exc

    companion_source = None
    companion_target = None
    if companion_source_path is not None:
        if not isinstance(companion_source_path, str) or companion_token is None:
            raise WorkspaceOperationError("The managed Source Notes companion is inconsistent.")
        companion_source = os.path.abspath(companion_source_path)
        if companion_source != canonical_source + SOURCE_NOTES_SUFFIX:
            raise WorkspaceOperationError("The managed Source Notes companion is inconsistent.")
        if not isinstance(companion_token, WorkspaceContentToken):
            raise TypeError("companion_token must be WorkspaceContentToken")
        companion_target = target + SOURCE_NOTES_SUFFIX
    elif companion_token is not None:
        raise WorkspaceOperationError("A Source Notes token requires a Source Notes path.")

    scratchpad_source = None
    scratchpad_target = None
    if scratchpad_source_path is not None:
        if not isinstance(scratchpad_source_path, str) or scratchpad_token is None:
            raise WorkspaceOperationError("The managed Scratchpad companion is inconsistent.")
        scratchpad_source = os.path.abspath(scratchpad_source_path)
        if scratchpad_source != canonical_source + SCRATCHPAD_SUFFIX:
            raise WorkspaceOperationError("The managed Scratchpad companion is inconsistent.")
        if not isinstance(scratchpad_token, WorkspaceContentToken):
            raise TypeError("scratchpad_token must be WorkspaceContentToken")
        scratchpad_target = target + SCRATCHPAD_SUFFIX
    elif scratchpad_token is not None:
        raise WorkspaceOperationError("A Scratchpad token requires a Scratchpad path.")

    return WorkspaceDuplicatePlan(
        kind="duplicate-text-file",
        root=canonical_root,
        parent_path=parent,
        source_path=canonical_source,
        target_path=target,
        source_name=source_name,
        display_name=display_name,
        source_token=source_token,
        companion_source_path=companion_source,
        companion_target_path=companion_target,
        companion_token=companion_token,
        scratchpad_source_path=scratchpad_source,
        scratchpad_target_path=scratchpad_target,
        scratchpad_token=scratchpad_token,
    )


def plan_move_to_trash(
    root: str,
    source_path: str,
    *,
    source_is_directory: bool,
    source_token: WorkspacePathToken,
    companion_source_path: str | None = None,
    companion_token: WorkspacePathToken | None = None,
    scratchpad_source_path: str | None = None,
    scratchpad_token: WorkspacePathToken | None = None,
) -> WorkspaceTrashPlan:
    """Build one root-confined system-Trash plan without filesystem I/O.

    The final Trash destination is intentionally opaque and owned by GIO.  The
    planner therefore records only the selected source identity, its parent and
    an optional managed Source Notes companion.  Permanent deletion, arbitrary
    move destinations and internal application trash directories are excluded.
    """
    if not isinstance(root, str) or not root.strip():
        raise WorkspaceOperationError("A valid root is required.")
    if not isinstance(source_path, str) or not source_path.strip():
        raise WorkspaceOperationError("Select one Workspace file or folder to move to Trash.")
    if not isinstance(source_is_directory, bool):
        raise TypeError("source_is_directory must be boolean")
    if not isinstance(source_token, WorkspacePathToken):
        raise TypeError("source_token must be WorkspacePathToken")

    canonical_root = os.path.abspath(root)
    canonical_source = os.path.abspath(source_path)
    parent = os.path.dirname(canonical_source)
    try:
        if canonical_source == canonical_root:
            raise WorkspaceOperationError("The Writing Workspace root cannot be moved to Trash here.")
        if os.path.commonpath((canonical_root, canonical_source)) != canonical_root:
            raise WorkspaceOperationError("The selected item resolves outside the Writing Workspace.")
        if os.path.commonpath((canonical_root, parent)) != canonical_root:
            raise WorkspaceOperationError("The selected item parent resolves outside the Writing Workspace.")
    except ValueError as exc:
        raise WorkspaceOperationError("The selected item is incompatible with the Workspace root.") from exc

    source_name = os.path.basename(canonical_source)
    if any(source_name.casefold().endswith(suffix) for suffix in MANAGED_SIDECAR_SUFFIXES):
        raise WorkspaceOperationError(
            "Move the document to Trash, not one of its managed sidecars."
        )

    companion_source = None
    if companion_source_path is not None:
        if not isinstance(companion_source_path, str) or companion_token is None:
            raise WorkspaceOperationError("The managed Source Notes companion is inconsistent.")
        companion_source = os.path.abspath(companion_source_path)
        if companion_source != canonical_source + SOURCE_NOTES_SUFFIX:
            raise WorkspaceOperationError("The managed Source Notes companion is inconsistent.")
        if not isinstance(companion_token, WorkspacePathToken):
            raise TypeError("companion_token must be WorkspacePathToken")
    elif companion_token is not None:
        raise WorkspaceOperationError("A Source Notes token requires a Source Notes path.")

    scratchpad_source = None
    if scratchpad_source_path is not None:
        if not isinstance(scratchpad_source_path, str) or scratchpad_token is None:
            raise WorkspaceOperationError("The managed Scratchpad companion is inconsistent.")
        scratchpad_source = os.path.abspath(scratchpad_source_path)
        if scratchpad_source != canonical_source + SCRATCHPAD_SUFFIX:
            raise WorkspaceOperationError("The managed Scratchpad companion is inconsistent.")
        if not isinstance(scratchpad_token, WorkspacePathToken):
            raise TypeError("scratchpad_token must be WorkspacePathToken")
    elif scratchpad_token is not None:
        raise WorkspaceOperationError("A Scratchpad token requires a Scratchpad path.")

    return WorkspaceTrashPlan(
        kind="move-to-trash",
        root=canonical_root,
        parent_path=parent,
        source_path=canonical_source,
        source_name=source_name,
        source_is_directory=source_is_directory,
        source_token=source_token,
        companion_source_path=companion_source,
        companion_token=companion_token,
        scratchpad_source_path=scratchpad_source,
        scratchpad_token=scratchpad_token,
    )
