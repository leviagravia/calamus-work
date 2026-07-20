"""GTK text-view adapter for the canonical Calamus search session."""
from __future__ import annotations


class SearchViewAdapter:
    """Own search highlight, cursor and selection access for one text view."""

    def __init__(self, text_view, search_tag) -> None:
        required_view = ("get_buffer", "scroll_to_iter")
        if any(not callable(getattr(text_view, name, None)) for name in required_view):
            raise TypeError("text_view does not implement the required search protocol")
        if search_tag is None:
            raise TypeError("search_tag is required")
        self._text_view = text_view
        self._search_tag = search_tag

    def _buffer(self):
        return self._text_view.get_buffer()

    def text(self) -> str:
        buffer = self._buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, True)

    def cursor_offset(self, *, backwards: bool = False) -> int:
        if not isinstance(backwards, bool):
            raise TypeError("backwards must be bool")
        buffer = self._buffer()
        if buffer.get_has_selection():
            start, end = buffer.get_selection_bounds()
            return start.get_offset() if backwards else end.get_offset()
        return buffer.get_iter_at_mark(buffer.get_insert()).get_offset()

    def line_column_for_offset(self, offset: int) -> tuple[int, int]:
        """Return GtkTextBuffer-authoritative one-based coordinates."""
        if not isinstance(offset, int) or isinstance(offset, bool):
            raise TypeError("offset must be int")
        if offset < 0:
            raise ValueError("offset cannot be negative")
        iterator = self._buffer().get_iter_at_offset(offset)
        get_line = getattr(iterator, "get_line", None)
        get_line_offset = getattr(iterator, "get_line_offset", None)
        if not callable(get_line) or not callable(get_line_offset):
            raise TypeError("text iterator does not expose line coordinates")
        return int(get_line()) + 1, int(get_line_offset()) + 1

    def clear_highlights(self) -> None:
        buffer = self._buffer()
        start, end = buffer.get_bounds()
        buffer.remove_tag(self._search_tag, start, end)

    def apply_highlights(self, spans) -> int:
        buffer = self._buffer()
        self.clear_highlights()
        count = 0
        for span in spans:
            try:
                start, end = span
            except (TypeError, ValueError) as exc:
                raise TypeError("search span must contain start and end") from exc
            if not isinstance(start, int) or isinstance(start, bool):
                raise TypeError("search span start must be int")
            if not isinstance(end, int) or isinstance(end, bool):
                raise TypeError("search span end must be int")
            if start < 0 or end < start:
                raise ValueError("invalid search span")
            begin = buffer.get_iter_at_offset(start)
            finish = buffer.get_iter_at_offset(end)
            buffer.apply_tag(self._search_tag, begin, finish)
            count += 1
        return count

    def select_span(self, start: int, end: int) -> None:
        if not isinstance(start, int) or isinstance(start, bool):
            raise TypeError("start must be int")
        if not isinstance(end, int) or isinstance(end, bool):
            raise TypeError("end must be int")
        if start < 0 or end < start:
            raise ValueError("invalid selection span")
        buffer = self._buffer()
        begin = buffer.get_iter_at_offset(start)
        finish = buffer.get_iter_at_offset(end)
        buffer.select_range(begin, finish)
        self._text_view.scroll_to_iter(begin, 0.15, False, 0, 0)
        self._text_view.grab_focus()
