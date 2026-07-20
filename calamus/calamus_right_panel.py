"""Canonical single-slot right-panel host for Calamus."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calamus_layout import (
    RIGHT_PANEL_DEFAULT_WIDTH,
    RIGHT_PANEL_MAX_FRACTION,
    RIGHT_PANEL_MIN_WIDTH,
)


def calculate_right_panel_width(total_width: int) -> int:
    """Return a bounded width for the single right-side panel slot."""
    width = int(total_width or 900)
    max_width = int(width * RIGHT_PANEL_MAX_FRACTION)
    return max(RIGHT_PANEL_MIN_WIDTH, min(RIGHT_PANEL_DEFAULT_WIDTH, max_width))


class RightPanelHost:
    """Own the only secondary child of the application's horizontal paned.

    The host owns layout and visibility only. Section widgets own their own
    content and state. A future panel can replace the current section without
    introducing a second Gtk.Paned or a second width/visibility authority.
    """

    def __init__(
        self,
        paned: Any,
        on_layout_changed: Callable[[], None],
        *,
        width_calculator: Callable[[int], int] = calculate_right_panel_width,
    ) -> None:
        if paned is None:
            raise TypeError("paned is required")
        if not callable(on_layout_changed):
            raise TypeError("on_layout_changed must be callable")
        if not callable(width_calculator):
            raise TypeError("width_calculator must be callable")
        self._paned = paned
        self._on_layout_changed = on_layout_changed
        self._width_calculator = width_calculator
        self._sections: dict[str, Any] = {}
        self._active_section: str | None = None

    @property
    def active_section(self) -> str | None:
        return self._active_section

    @property
    def is_visible(self) -> bool:
        return self._active_section is not None

    def register(self, section_id: str, widget: Any) -> None:
        if not isinstance(section_id, str) or not section_id.strip():
            raise ValueError("section_id must be a non-empty string")
        if widget is None:
            raise TypeError("widget is required")
        key = section_id.strip()
        if key in self._sections:
            raise ValueError(f"right-panel section already registered: {key}")
        self._sections[key] = widget

    def has_section(self, section_id: str) -> bool:
        return isinstance(section_id, str) and section_id.strip() in self._sections

    def toggle(self, section_id: str) -> bool:
        key = self._require_section(section_id)
        if self._active_section == key:
            self.hide()
            return False
        self.show(key)
        return True

    def show(self, section_id: str) -> None:
        key = self._require_section(section_id)
        if self._active_section == key:
            self._configure_widget(self._sections[key])
            self._sections[key].show_all()
            self._on_layout_changed()
            return

        self._detach_active()
        widget = self._sections[key]
        if widget.get_parent() is None:
            self._paned.pack2(widget, False, False)
        self._configure_widget(widget)
        widget.show_all()
        self._active_section = key
        self._on_layout_changed()

    def hide(self) -> None:
        if self._active_section is None:
            return
        self._detach_active()
        self._on_layout_changed()

    def _require_section(self, section_id: str) -> str:
        if not isinstance(section_id, str) or not section_id.strip():
            raise ValueError("section_id must be a non-empty string")
        key = section_id.strip()
        if key not in self._sections:
            raise KeyError(key)
        return key

    def _detach_active(self) -> None:
        if self._active_section is None:
            return
        widget = self._sections[self._active_section]
        try:
            self._paned.remove(widget)
        except Exception:
            widget.hide()
        self._active_section = None

    def _configure_widget(self, widget: Any) -> None:
        allocation = self._paned.get_allocation()
        total_width = getattr(allocation, "width", 900) or 900
        panel_width = self._width_calculator(total_width)
        widget.set_size_request(panel_width, -1)
        widget.set_hexpand(False)
        widget.set_vexpand(True)
        self._paned.set_position(max(1, total_width - panel_width))
