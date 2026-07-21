"""Canonical transient navigation gateway for Calamus."""
from __future__ import annotations

from calamus_document_structure import (
    DocumentHeading,
    DocumentStructure,
    build_document_structure,
)
from calamus_navigation import clamp_line_number, line_to_buffer_index


class NavigationController:
    """Own line navigation and one lazily rebuilt heading index."""

    def __init__(self, adapter) -> None:
        required = (
            "text",
            "cursor_offset",
            "line_count",
            "navigate_offset",
            "navigate_line",
        )
        if any(not callable(getattr(adapter, name, None)) for name in required):
            raise TypeError("adapter does not implement the navigation-view protocol")
        self._adapter = adapter
        self._snapshot: str | None = None
        self._structure = DocumentStructure()

    def invalidate(self) -> None:
        self._snapshot = None

    def refresh_structure(self, *, force: bool = False) -> DocumentStructure:
        if not isinstance(force, bool):
            raise TypeError("force must be bool")
        text = self._adapter.text()
        if force or text != self._snapshot:
            self._structure = build_document_structure(text)
            self._snapshot = text
        return self._structure

    @property
    def structure(self) -> DocumentStructure:
        return self.refresh_structure()

    def line_count(self) -> int:
        count = self._adapter.line_count()
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("adapter line count must be a positive integer")
        return count

    def go_to_line(self, requested_line) -> int:
        total = self.line_count()
        line = clamp_line_number(requested_line, total)
        self._adapter.navigate_line(line_to_buffer_index(line, total))
        return line

    def headings(self, query: str = "") -> tuple[DocumentHeading, ...]:
        return self.refresh_structure().filtered(query)

    def current_heading(self) -> DocumentHeading | None:
        return self.refresh_structure().current_heading(self._adapter.cursor_offset())

    def next_heading(self) -> DocumentHeading | None:
        heading = self.refresh_structure().next_heading(self._adapter.cursor_offset())
        if heading is not None:
            self.navigate_heading(heading)
        return heading

    def previous_heading(self) -> DocumentHeading | None:
        heading = self.refresh_structure().previous_heading(self._adapter.cursor_offset())
        if heading is not None:
            self.navigate_heading(heading)
        return heading

    def navigate_heading(self, heading: DocumentHeading) -> DocumentHeading:
        if not isinstance(heading, DocumentHeading):
            raise TypeError("heading must be DocumentHeading")
        if heading not in self.refresh_structure().headings:
            raise ValueError("heading does not belong to the current structure")
        self._adapter.navigate_offset(heading.start_offset)
        return heading
