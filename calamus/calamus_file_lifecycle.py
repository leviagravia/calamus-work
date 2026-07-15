"""Pure file-lifecycle planning for Calamus.

GTK dialogs, Gtk.TextBuffer mutation, physical file reads/writes, error
reporting, recent-file persistence, and title updates remain owned by the App
boundary.  This module describes deterministic New, Open, Save, and Save As state
transitions without performing desktop or filesystem operations.
"""
from __future__ import annotations

from dataclasses import dataclass

from calamus_writing import remove_trailing_spaces


@dataclass(frozen=True)
class NewPlan:
    """Deterministic transition for File -> New."""

    text: str = ""
    target_path: str | None = None
    modified: bool = False


def prepare_new_plan() -> NewPlan:
    """Return the pure state-transition plan for a new empty document.

    The save prompt, Gtk.TextBuffer mutation, document identity commit, Undo
    reset, and title update remain in ``App``.  Keeping the transition as an
    immutable plan prevents the previous document identity from being cleared
    before the editor buffer has accepted the empty replacement text.
    """
    return NewPlan()


@dataclass(frozen=True)
class OpenPlan:
    """Deterministic loaded-document transition for File -> Open."""

    target_path: str
    text: str
    large_file: bool = False


def prepare_open_plan(
    selected_path: str,
    text: str,
    *,
    large_file: bool = False,
) -> OpenPlan:
    """Return the pure state-transition plan for an already-read document.

    File selection, disk reads, Gtk.TextBuffer mutation, recent-file updates,
    title changes, settings persistence, and error dialogs remain in ``App``.
    The plan prevents document identity from changing before the selected file
    has been read successfully and the editor buffer has accepted its text.
    """
    if not isinstance(selected_path, str):
        raise TypeError("selected_path must be a string")
    if selected_path == "":
        raise ValueError("selected_path must not be empty")
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(large_file, bool):
        raise TypeError("large_file must be a boolean")
    return OpenPlan(
        target_path=selected_path,
        text=text,
        large_file=large_file,
    )


@dataclass(frozen=True)
class SavePlan:
    """Deterministic preflight for the visible File -> Save command."""

    requires_destination: bool
    target_path: str | None
    original_text: str
    text_to_write: str

    @property
    def replaces_buffer_text(self) -> bool:
        """Whether save-time normalization must be reflected in the editor."""
        return self.text_to_write != self.original_text


def prepare_save_plan(
    current_file: str | None,
    text: str,
    *,
    trim_trailing_on_save: bool = False,
) -> SavePlan:
    """Return the pure preflight plan for Save without performing I/O.

    Untitled documents require the existing Save As boundary. For documents
    with a destination, the plan preserves the historical optional
    trim-trailing-on-save behavior while keeping the transformation outside
    the GTK/file-write orchestration in ``App``.
    """
    if current_file is not None and not isinstance(current_file, str):
        raise TypeError("current_file must be a string or None")
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    target_path = current_file if current_file else None
    text_to_write = (
        remove_trailing_spaces(text)
        if bool(trim_trailing_on_save)
        else text
    )
    return SavePlan(
        requires_destination=target_path is None,
        target_path=target_path,
        original_text=text,
        text_to_write=text_to_write,
    )


def prepare_save_as_plan(
    selected_path: str | None,
    text: str,
    *,
    trim_trailing_on_save: bool = False,
) -> SavePlan | None:
    """Return a Save plan for an accepted Save As destination.

    ``None`` or an empty path represents a cancelled chooser and produces no
    plan.  The selected destination is otherwise treated as an explicit target
    without mutating application or document identity before the physical write
    succeeds.
    """
    if selected_path is None or selected_path == "":
        return None
    if not isinstance(selected_path, str):
        raise TypeError("selected_path must be a string or None")
    return prepare_save_plan(
        selected_path,
        text,
        trim_trailing_on_save=trim_trailing_on_save,
    )
