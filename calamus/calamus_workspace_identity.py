"""Pure application-identity reconciliation after a Workspace rename."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable


@dataclass(frozen=True)
class WorkspacePathReferenceSnapshot:
    recent_files: tuple[str, ...] = ()
    favourites: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkspaceRenameIdentityPlan:
    current_file_before: str | None
    current_file_after: str | None
    recent_files_after: tuple[str, ...]
    favourites_after: tuple[str, ...]

    @property
    def document_identity_changed(self) -> bool:
        return self.current_file_before != self.current_file_after


def path_after_rename(
    path: str | None,
    source_path: str,
    target_path: str,
    *,
    source_is_directory: bool,
) -> str | None:
    if path is None:
        return None
    if not all(isinstance(value, str) and value for value in (path, source_path, target_path)):
        raise TypeError("rename paths must be non-empty strings")
    current = os.path.abspath(path)
    source = os.path.abspath(source_path)
    target = os.path.abspath(target_path)
    if current == source:
        return target
    if not source_is_directory:
        return current
    try:
        if os.path.commonpath((source, current)) != source:
            return current
    except ValueError:
        return current
    relative = os.path.relpath(current, source)
    return os.path.abspath(os.path.join(target, relative))


def rewrite_path_collection(
    paths: Iterable[str],
    source_path: str,
    target_path: str,
    *,
    source_is_directory: bool,
) -> tuple[str, ...]:
    rewritten: list[str] = []
    for item in paths:
        if not isinstance(item, str) or not item:
            continue
        mapped = path_after_rename(
            item, source_path, target_path, source_is_directory=source_is_directory
        )
        if mapped is not None and mapped not in rewritten:
            rewritten.append(mapped)
    return tuple(rewritten)


def plan_workspace_rename_identity(
    current_file: str | None,
    references: WorkspacePathReferenceSnapshot,
    source_path: str,
    target_path: str,
    *,
    source_is_directory: bool,
) -> WorkspaceRenameIdentityPlan:
    if not isinstance(references, WorkspacePathReferenceSnapshot):
        raise TypeError("references must be WorkspacePathReferenceSnapshot")
    return WorkspaceRenameIdentityPlan(
        current_file_before=os.path.abspath(current_file) if current_file else None,
        current_file_after=path_after_rename(
            current_file, source_path, target_path, source_is_directory=source_is_directory
        ),
        recent_files_after=rewrite_path_collection(
            references.recent_files, source_path, target_path, source_is_directory=source_is_directory
        ),
        favourites_after=rewrite_path_collection(
            references.favourites, source_path, target_path, source_is_directory=source_is_directory
        ),
    )
