"""Application/GTK coordinator for Clip Collection."""
from __future__ import annotations

from typing import Any, Callable

from calamus_clip_dialogs import (
    confirm_clip_delete,
    confirm_duplicate_body,
    run_clip_editor_dialog,
    run_clip_selector_dialog,
    show_stale_clip_message,
)
from calamus_clip_expansion import expand_clip_text
from calamus_clips import ClipError


def selected_document_text_from_view(text_view: Any) -> str:
    """Return the current selection through the narrow text-view boundary."""
    buffer = text_view.get_buffer()
    if not buffer.get_has_selection():
        return ""
    start, end = buffer.get_selection_bounds()
    return buffer.get_text(start, end, True)



def copy_clip_body(text: str) -> None:
    """Copy one clip body through the GTK clipboard boundary."""
    from gi.repository import Gdk, Gtk

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(text if isinstance(text, str) else "", -1)
    clipboard.store()


def insert_clip_expansion_through_gateway(
    text_view: Any,
    text: str,
    cursor_offset: int,
    *,
    execute_command: Callable[[str, Callable[[Any], None]], bool],
    get_cursor_offset: Callable[[], int],
    set_cursor_offset: Callable[[int], Any],
    sync_history_view_state: Callable[[], Any],
    queue_insert_scroll: Callable[..., Any],
) -> bool:
    """Insert expanded text through explicit editor command dependencies."""
    if not isinstance(text, str):
        return False
    for callback in (
        execute_command,
        get_cursor_offset,
        set_cursor_offset,
        sync_history_view_state,
        queue_insert_scroll,
    ):
        if not callable(callback):
            raise TypeError("clip insertion gateways must be callable")
    buffer = text_view.get_buffer()
    if buffer.get_has_selection():
        start_iter, _end_iter = buffer.get_selection_bounds()
        start_offset = start_iter.get_offset()
    else:
        start_offset = get_cursor_offset()
    caret = start_offset + max(0, min(int(cursor_offset), len(text)))
    text_view.grab_focus()

    def edit(target_buffer):
        target_buffer.insert_at_cursor(text)

    changed = bool(execute_command("Insert Clip", edit))
    if not changed:
        return False
    # Preserve the published single-Undo and viewport-repair semantics while
    # avoiding a whole-App input at the W101 local builder boundary.
    set_cursor_offset(caret)
    sync_history_view_state()
    queue_insert_scroll(margin=0.15)
    text_view.grab_focus()
    return True




class ClipCollectionRuntime:
    def __init__(
        self,
        parent: Any,
        controller: Any,
        *,
        selected_text_provider: Callable[[], str],
        insert_expansion: Callable[[str, int], bool],
        copy_text: Callable[[str], None],
        show_error: Callable[[str], None],
        show_info: Callable[[str], None],
        on_changed=None,
    ) -> None:
        self._parent = parent
        self._controller = controller
        self._selected_text_provider = selected_text_provider
        self._insert_expansion = insert_expansion
        self._copy_text = copy_text
        self._show_error = show_error
        if on_changed is not None and not callable(on_changed):
            raise TypeError("on_changed must be callable")
        self._show_info = show_info
        self._on_changed = on_changed or (lambda: None)

    @property
    def widget(self):
        return self._controller.widget

    def activate(self) -> None:
        self._controller.activate()

    def on_search(self, query: str) -> None:
        self._controller.set_query(query)

    def refresh_for_invalidation(self, _reasons=frozenset()) -> bool:
        return bool(self._controller.refresh())

    def shutdown(self) -> bool:
        return True

    def on_new(self, *_args) -> bool:
        record = run_clip_editor_dialog(
            self._parent,
            dialog_title="New Clip",
            existing_shortcuts=self._shortcuts(),
        )
        if record is None:
            return False
        return self._create_from_dialog(record)

    def on_capture(self, *_args) -> bool:
        text = self._selected_text_provider()
        if not isinstance(text, str) or not text.strip():
            self._show_error("Select non-empty document text before capturing a clip.")
            return False
        record = run_clip_editor_dialog(
            self._parent,
            title="",
            text=text,
            dialog_title="Capture Selection as Clip",
            existing_shortcuts=self._shortcuts(),
        )
        if record is None:
            return False
        return self._create_from_dialog(record)

    def on_edit(self, *_args) -> bool:
        selected = self._controller.selected_clip()
        if selected is None:
            return False
        record = run_clip_editor_dialog(
            self._parent,
            title=selected.get("title", ""),
            shortcut=selected.get("shortcut", ""),
            text=selected.get("text", ""),
            dialog_title="Edit Clip",
            existing_shortcuts=self._shortcuts(),
            current_shortcut=selected.get("shortcut", ""),
        )
        if record is None:
            return False
        result = self._controller.update_selected(**record)
        return self._handle_result(result, changed=True)

    def on_duplicate(self, *_args) -> bool:
        selected = self._controller.selected_clip()
        if selected is None:
            return False
        choice = confirm_duplicate_body(self._parent, selected)
        if choice == "cancel":
            return False
        if choice == "select":
            return self._controller.select_id(selected["id"], clear_query=True)
        result = self._controller.duplicate_selected()
        return self._handle_result(result, changed=True)

    def on_delete(self, *_args) -> bool:
        selected = self._controller.selected_clip()
        if selected is None or not confirm_clip_delete(self._parent, selected):
            return False
        return self._handle_result(self._controller.delete_selected(), changed=True)

    def on_refresh(self, *_args) -> bool:
        return self._handle_result(self._controller.refresh(), success_message="Clip Collection reloaded from disk.")

    def on_insert(self, *_args) -> bool:
        selected = self._controller.selected_clip()
        if selected is None:
            return False
        return self._insert_clip(selected)

    def on_copy(self, *_args) -> bool:
        selected = self._controller.selected_clip()
        if selected is None:
            return False
        self._copy_text(selected.get("text", ""))
        return True

    def on_quick_insert(self, *_args) -> bool:
        if not self._controller.refresh():
            return self._fail()
        clip_id = run_clip_selector_dialog(self._parent, self._controller.clips)
        if not clip_id:
            return False
        selected = self._controller.clip_by_id(clip_id)
        if selected is None:
            self._show_error("The selected clip is no longer available. Refresh and try again.")
            return False
        self._controller.select_id(clip_id, clear_query=True)
        return self._insert_clip(selected)

    def on_open_file(self, *_args) -> bool:
        if not self._controller.ensure_authority():
            return self._fail()
        path = self._controller.authority_path
        try:
            from gi.repository import Gio
            Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(path).get_uri(), None)
            return True
        except Exception as error:
            self._show_error(f"Could not open Clip Collection file:\n{path}\n\n{error}")
            return False

    def _create_from_dialog(self, record: dict[str, str]) -> bool:
        duplicates = self._controller.duplicate_body_ids(record["text"])
        if duplicates:
            existing = self._controller.clip_by_id(duplicates[0])
            choice = confirm_duplicate_body(self._parent, existing or {})
            if choice == "cancel":
                return False
            if choice == "select" and existing is not None:
                return self._controller.select_id(existing["id"], clear_query=True)
        return self._handle_result(self._controller.create(**record), changed=True)

    def _insert_clip(self, selected: dict[str, Any]) -> bool:
        # Re-read first so insertion never uses a stale body silently.
        selected_id = selected.get("id", "")
        if not self._controller.refresh():
            return self._fail()
        current = self._controller.clip_by_id(selected_id)
        if current is None:
            self._show_error("The selected clip changed or was deleted outside Calamus.")
            return False
        try:
            expansion = expand_clip_text(current.get("text", ""))
        except ClipError as error:
            self._show_error(str(error))
            return False
        return bool(self._insert_expansion(expansion.text, expansion.cursor_offset))

    def _shortcuts(self) -> tuple[str, ...]:
        return tuple(
            item.get("shortcut", "")
            for item in self._controller.clips
            if item.get("shortcut", "")
        )

    def _handle_result(self, result, *, success_message: str = "", changed: bool = False) -> bool:
        if result is True:
            if changed:
                getattr(self, "_on_changed", lambda: None)()
            if success_message:
                self._show_info(success_message)
            return True
        if result is False:
            return self._fail()
        return False

    def _fail(self) -> bool:
        message = self._controller.last_error or "Clip Collection operation failed."
        if "changed" in message.casefold() or "stale" in message.casefold():
            show_stale_clip_message(self._parent, message)
        else:
            self._show_error(message)
        return False
