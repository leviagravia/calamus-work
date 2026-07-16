"""Pure Favorite-file action planning for Calamus.

Favorites are intentional file/document choices. They are not Recent Files and
are not text bookmarks inside a document. Gtk menu construction, save prompts,
filesystem probes, document loading, JSON persistence, notifications, and menu
refresh remain owned by the App and StateManager boundaries. This module only
describes the deterministic result of activating one existing Favorite entry.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OpenFavoritePlan:
    """Deterministic routing plan for one Favorite menu activation."""

    selected_path: str
    target_path: str | None

    @property
    def should_open(self) -> bool:
        """Whether the selected Favorite is an available regular file."""
        return self.target_path is not None


def prepare_open_favorite_plan(
    selected_path: str,
    *,
    path_is_file: bool,
) -> OpenFavoritePlan:
    """Plan activation of one existing Favorite-file menu entry.

    A Favorite remains an intentional stored choice even when it is temporarily
    unavailable. Therefore this plan never returns a persistence mutation or a
    pruning instruction. The application may open the target through the W48
    document lifecycle only when the filesystem boundary confirms a regular
    file. Missing paths and directories are reported without changing either
    the Favorites store or the active document.
    """
    if not isinstance(selected_path, str):
        raise TypeError("selected_path must be a string")
    if selected_path == "":
        raise ValueError("selected_path must not be empty")
    if not isinstance(path_is_file, bool):
        raise TypeError("path_is_file must be a boolean")

    return OpenFavoritePlan(
        selected_path=selected_path,
        target_path=selected_path if path_is_file else None,
    )
