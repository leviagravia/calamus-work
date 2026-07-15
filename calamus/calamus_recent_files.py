"""Pure recent-file action planning for Calamus.

Gtk menu construction, save prompts, filesystem probes, document loading,
error dialogs, JSON persistence, and menu refresh remain owned by the App and
StateManager boundaries.  This module only describes the deterministic result
of activating one existing File -> Recent Files entry.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpenRecentPlan:
    """Deterministic routing plan for one recent-file menu activation."""

    target_path: str | None
    remaining_paths_after_failure: tuple[str, ...]

    @property
    def should_open(self) -> bool:
        """Whether the selected recent path still exists and should be opened."""
        return self.target_path is not None


def prepare_open_recent_plan(
    selected_path: str,
    recent_paths: list[str] | tuple[str, ...],
    *,
    path_exists: bool,
) -> OpenRecentPlan:
    """Plan activation of an existing Recent Files menu entry.

    The current save prompt and filesystem existence probe stay in ``App``.
    The plan supplies the open target when it still exists and, independently,
    the exact recent-file list to persist if opening is impossible or fails.
    This mirrors mature-editor discipline: a failed recent entry is removed
    from history instead of remaining as a repeatedly broken command.
    """
    if not isinstance(selected_path, str):
        raise TypeError("selected_path must be a string")
    if selected_path == "":
        raise ValueError("selected_path must not be empty")
    if not isinstance(recent_paths, (list, tuple)):
        raise TypeError("recent_paths must be a list or tuple")
    if not isinstance(path_exists, bool):
        raise TypeError("path_exists must be a boolean")

    clean: list[str] = []
    for item in recent_paths:
        if not isinstance(item, str):
            raise TypeError("recent_paths entries must be strings")
        if item and item not in clean:
            clean.append(item)

    return OpenRecentPlan(
        target_path=selected_path if path_exists else None,
        remaining_paths_after_failure=tuple(
            item for item in clean if item != selected_path
        ),
    )
