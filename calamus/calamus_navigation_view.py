"""GtkTextView adapter for canonical Calamus navigation."""
from __future__ import annotations


class NavigationViewAdapter:
    """Own text, cursor, line and exact-offset navigation for one editor view."""

    def __init__(self, text_view) -> None:
        required = ("get_buffer", "scroll_to_iter", "grab_focus")
        if any(not callable(getattr(text_view, name, None)) for name in required):
            raise TypeError("text_view does not implement the navigation-view protocol")
        self._text_view = text_view

    def _buffer(self):
        return self._text_view.get_buffer()

    def text(self) -> str:
        buffer = self._buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, True)

    def cursor_offset(self) -> int:
        buffer = self._buffer()
        iterator = buffer.get_iter_at_mark(buffer.get_insert())
        return int(iterator.get_offset())

    def line_count(self) -> int:
        return max(1, int(self._buffer().get_line_count()))

    def _reveal(self, iterator) -> None:
        buffer = self._buffer()
        buffer.place_cursor(iterator)
        self._text_view.scroll_to_iter(iterator, 0.15, False, 0, 0)
        self._text_view.grab_focus()

    def navigate_offset(self, offset: int) -> None:
        if not isinstance(offset, int) or isinstance(offset, bool):
            raise TypeError("offset must be int")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        self._reveal(self._buffer().get_iter_at_offset(offset))

    def navigate_line(self, line_index: int) -> None:
        if not isinstance(line_index, int) or isinstance(line_index, bool):
            raise TypeError("line_index must be int")
        if line_index < 0:
            raise ValueError("line_index cannot be negative")
        buffer = self._buffer()
        safe_index = min(line_index, self.line_count() - 1)
        self._reveal(buffer.get_iter_at_line_offset(safe_index, 0))
