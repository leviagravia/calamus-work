"""GtkTextBuffer adapter for Calamus editor transactions.

The adapter is intentionally tiny: it knows how to capture and restore the
visible buffer state and how to invoke GTK's user-action grouping.  It owns no
history, document, command, or presentation policy.
"""
from __future__ import annotations

from typing import Any, Callable

from calamus_history import HistoryState


class EditorBufferAdapter:
    __slots__ = ("text_view",)

    def __init__(self, text_view: Any) -> None:
        if text_view is None:
            raise TypeError("text_view is required")
        self.text_view = text_view

    @property
    def buffer(self) -> Any:
        return self.text_view.get_buffer()

    def capture(self) -> HistoryState:
        buffer = self.buffer
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, True)
        insert = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()
        bound = buffer.get_iter_at_mark(buffer.get_selection_bound()).get_offset()
        return HistoryState(text, insert, bound)

    def begin_user_action(self) -> None:
        self.buffer.begin_user_action()

    def end_user_action(self) -> None:
        self.buffer.end_user_action()

    def apply_callback(self, edit_func: Callable[[Any], Any]) -> Any:
        if not callable(edit_func):
            raise TypeError("edit_func must be callable")
        return edit_func(self.buffer)

    def cut_clipboard(self, clipboard: Any, editable: bool = True) -> None:
        self.buffer.cut_clipboard(clipboard, bool(editable))

    def paste_clipboard(self, clipboard: Any, editable: bool = True) -> None:
        self.buffer.paste_clipboard(clipboard, None, bool(editable))

    def select_range(self, start: int, end: int) -> None:
        buffer = self.buffer
        limit = buffer.get_char_count()
        a = max(0, min(int(start), limit))
        b = max(0, min(int(end), limit))
        buffer.select_range(buffer.get_iter_at_offset(a), buffer.get_iter_at_offset(b))

    def restore(self, state: HistoryState) -> None:
        if not isinstance(state, HistoryState):
            raise TypeError("state must be HistoryState")
        buffer = self.buffer
        buffer.set_text(state.text)
        insert = buffer.get_iter_at_offset(state.insert_offset)
        bound = buffer.get_iter_at_offset(state.selection_bound_offset)
        buffer.select_range(insert, bound)
