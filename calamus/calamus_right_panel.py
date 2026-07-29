"""Canonical single-slot right-panel host for Calamus."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calamus_layout import (
    EDITOR_MIN_CONTENT_WIDTH,
    RIGHT_PANEL_DEFAULT_WIDTH,
    RIGHT_PANEL_MAX_FRACTION,
    RIGHT_PANEL_MIN_WIDTH,
)


def calculate_right_panel_width(total_width: int) -> int:
    """Return the conservative initial width for the right-side panel slot."""
    width = int(total_width or 900)
    max_width = int(width * RIGHT_PANEL_MAX_FRACTION)
    return max(RIGHT_PANEL_MIN_WIDTH, min(RIGHT_PANEL_DEFAULT_WIDTH, max_width))


def bound_right_panel_width(total_width: int, requested_width: int) -> int:
    """Clamp a remembered user width without turning it into a widget minimum.

    The initial panel is intentionally compact, but once the user drags the
    divider the current width is remembered across hide/show.  On a smaller
    window the editor keeps its minimum viewport floor.
    """
    total = max(2, int(total_width or 900))
    minimum = min(RIGHT_PANEL_MIN_WIDTH, total - 1)
    maximum = max(minimum, total - EDITOR_MIN_CONTENT_WIDTH)
    return max(minimum, min(int(requested_width), maximum))


class RightPanelHost:
    """Own the only secondary child of the application's horizontal paned.

    The host owns layout, visibility and the session-local divider width. A
    child widget never owns a positive width request: Gtk.Paned remains the
    sole geometry authority, shrink is enabled, and the last user-selected
    width is restored after the panel is hidden and shown again.
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
        self._remembered_width: int | None = None

    @property
    def active_section(self) -> str | None:
        return self._active_section

    @property
    def is_visible(self) -> bool:
        return self._active_section is not None

    @property
    def remembered_width(self) -> int | None:
        return self._remembered_width

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
            # Do not reapply a default position to an already visible panel.
            # The current Gtk.Paned divider belongs to the user.
            self._sections[key].show_all()
            self._on_layout_changed()
            return

        self._detach_active(remember=True)
        widget = self._sections[key]
        if widget.get_parent() is None:
            # The right child must be allowed to shrink below its natural
            # requisition. Otherwise a populated client can lock the divider.
            self._paned.pack2(widget, False, True)
        self._configure_widget(widget)
        widget.show_all()
        self._active_section = key
        self._on_layout_changed()

    def hide(self) -> None:
        if self._active_section is None:
            return
        self._detach_active(remember=True)
        self._on_layout_changed()

    def _require_section(self, section_id: str) -> str:
        if not isinstance(section_id, str) or not section_id.strip():
            raise ValueError("section_id must be a non-empty string")
        key = section_id.strip()
        if key not in self._sections:
            raise KeyError(key)
        return key

    def _detach_active(self, *, remember: bool) -> None:
        if self._active_section is None:
            return
        if remember:
            self._remember_current_width()
        widget = self._sections[self._active_section]
        try:
            self._paned.remove(widget)
        except Exception:
            widget.hide()
        self._active_section = None

    def _configure_widget(self, widget: Any) -> None:
        total_width = self._total_width()
        requested = (
            self._remembered_width
            if self._remembered_width is not None
            else self._width_calculator(total_width)
        )
        panel_width = bound_right_panel_width(total_width, requested)
        # A positive child request becomes a top-level minimum width after the
        # Research shell is reattached. Gtk.Paned alone owns the width.
        widget.set_size_request(-1, -1)
        widget.set_hexpand(False)
        widget.set_vexpand(True)
        self._paned.set_position(max(1, total_width - panel_width))
        self._remembered_width = panel_width

    def _remember_current_width(self) -> None:
        get_position = getattr(self._paned, "get_position", None)
        if not callable(get_position):
            return
        total_width = self._total_width()
        position = int(get_position() or 0)
        if position <= 0 or position >= total_width:
            return
        self._remembered_width = bound_right_panel_width(
            total_width,
            total_width - position,
        )

    def _total_width(self) -> int:
        allocation = self._paned.get_allocation()
        return int(getattr(allocation, "width", 900) or 900)
