"""Canonical left-side Navigator panel boundary for Calamus.

The Navigator is a transient view of the current document structure.  It does
not persist an outline and it does not parse Markdown independently from the
W70 NavigationController.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calamus_document_structure import DocumentHeading
from calamus_layout import (
    NAVIGATOR_PANEL_DEFAULT_WIDTH,
    NAVIGATOR_PANEL_MAX_FRACTION,
    NAVIGATOR_PANEL_MIN_WIDTH,
)


def calculate_navigator_panel_width(total_width: int) -> int:
    """Return a compact bounded width for the document Navigator."""
    width = int(total_width or 900)
    maximum = max(NAVIGATOR_PANEL_MIN_WIDTH, int(width * NAVIGATOR_PANEL_MAX_FRACTION))
    return max(
        NAVIGATOR_PANEL_MIN_WIDTH,
        min(NAVIGATOR_PANEL_DEFAULT_WIDTH, maximum),
    )


class NavigatorPanelHost:
    """Own the optional first child of the outer workspace Gtk.Paned.

    This is deliberately a Navigator-specific host, not a generic extension or
    multi-client left-panel framework.  The main editor/right-panel body stays
    permanently in the second slot.
    """

    def __init__(
        self,
        paned: Any,
        widget: Any,
        on_layout_changed: Callable[[], None],
        *,
        width_calculator: Callable[[int], int] = calculate_navigator_panel_width,
    ) -> None:
        if paned is None:
            raise TypeError("paned is required")
        if widget is None:
            raise TypeError("widget is required")
        if not callable(on_layout_changed):
            raise TypeError("on_layout_changed must be callable")
        if not callable(width_calculator):
            raise TypeError("width_calculator must be callable")
        self._paned = paned
        self._widget = widget
        self._on_layout_changed = on_layout_changed
        self._width_calculator = width_calculator
        self._visible = False

    @property
    def is_visible(self) -> bool:
        return self._visible

    def toggle(self) -> bool:
        if self._visible:
            self.hide()
            return False
        self.show()
        return True

    def show(self) -> None:
        if self._widget.get_parent() is None:
            self._paned.pack1(self._widget, False, False)
        self._configure_widget()
        self._widget.show_all()
        self._visible = True
        self._on_layout_changed()

    def hide(self) -> None:
        if not self._visible and self._widget.get_parent() is None:
            return
        try:
            self._paned.remove(self._widget)
        except Exception:
            self._widget.hide()
        self._visible = False
        self._on_layout_changed()

    def _configure_widget(self) -> None:
        allocation = self._paned.get_allocation()
        total_width = getattr(allocation, "width", 900) or 900
        panel_width = self._width_calculator(total_width)
        self._widget.set_size_request(panel_width, -1)
        self._widget.set_hexpand(False)
        self._widget.set_vexpand(True)
        self._paned.set_position(panel_width)


class NavigatorPanelPresenter:
    """Bridge one canonical NavigationController to a passive panel view."""

    def __init__(self, controller: Any, view: Any) -> None:
        controller_methods = ("headings", "current_heading", "navigate_heading")
        view_methods = ("render", "select_heading")
        if any(not callable(getattr(controller, name, None)) for name in controller_methods):
            raise TypeError("controller does not implement the Navigator protocol")
        if any(not callable(getattr(view, name, None)) for name in view_methods):
            raise TypeError("view does not implement the Navigator protocol")
        self._controller = controller
        self._view = view

    def refresh(self, query: str = "") -> tuple[DocumentHeading, ...]:
        if not isinstance(query, str):
            raise TypeError("query must be str")
        headings = self._controller.headings(query)
        current = self._controller.current_heading()
        if current not in headings:
            current = None
        self._view.render(headings, current)
        return headings

    def sync_cursor(self) -> DocumentHeading | None:
        heading = self._controller.current_heading()
        self._view.select_heading(heading)
        return heading

    def activate(self, heading: DocumentHeading) -> DocumentHeading:
        if not isinstance(heading, DocumentHeading):
            raise TypeError("heading must be DocumentHeading")
        return self._controller.navigate_heading(heading)


class NavigatorPanelRuntime:
    """Own Navigator visibility, menu synchronization and focus restoration."""

    def __init__(self, host: Any, view: Any, menu_item: Any, editor_focus: Callable[[], None]) -> None:
        host_methods = ("show", "hide")
        view_methods = ("refresh", "schedule_cursor_sync", "focus_filter", "cancel_pending")
        if any(not callable(getattr(host, name, None)) for name in host_methods):
            raise TypeError("host does not implement the Navigator runtime protocol")
        if not hasattr(host, "is_visible"):
            raise TypeError("host does not expose is_visible")
        if any(not callable(getattr(view, name, None)) for name in view_methods):
            raise TypeError("view does not implement the Navigator runtime protocol")
        if menu_item is None or not callable(getattr(menu_item, "get_active", None)) or not callable(getattr(menu_item, "set_active", None)):
            raise TypeError("menu_item does not implement the check-item protocol")
        if not callable(editor_focus):
            raise TypeError("editor_focus must be callable")
        self._host = host
        self._view = view
        self._menu_item = menu_item
        self._editor_focus = editor_focus
        self._syncing_menu = False

    @property
    def is_visible(self) -> bool:
        return bool(self._host.is_visible)

    def set_visible(self, visible: bool) -> bool:
        target = bool(visible)
        if target:
            self._host.show()
            self._view.refresh()
            self._view.schedule_cursor_sync()
            self._view.focus_filter()
        else:
            self._view.cancel_pending()
            self._host.hide()
            self._editor_focus()
        self._sync_menu(target)
        return target

    def toggle(self) -> bool:
        return self.set_visible(not self.is_visible)

    def hide(self) -> bool:
        return self.set_visible(False)

    def on_menu_toggled(self, menu_item: Any) -> None:
        if self._syncing_menu:
            return
        self.set_visible(menu_item.get_active())

    def _sync_menu(self, visible: bool) -> None:
        if self._menu_item.get_active() == bool(visible):
            return
        self._syncing_menu = True
        try:
            self._menu_item.set_active(bool(visible))
        finally:
            self._syncing_menu = False
