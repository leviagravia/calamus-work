"""Closed left-panel host shared by Navigator and Writing Workspace."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calamus_layout import LEFT_PANEL_DEFAULT_WIDTH, LEFT_PANEL_MAX_FRACTION, LEFT_PANEL_MIN_WIDTH

ALLOWED_LEFT_CLIENTS = ("navigator", "workspace")


def calculate_left_panel_width(total_width: int) -> int:
    width = int(total_width or 900)
    maximum = max(LEFT_PANEL_MIN_WIDTH, int(width * LEFT_PANEL_MAX_FRACTION))
    return max(LEFT_PANEL_MIN_WIDTH, min(LEFT_PANEL_DEFAULT_WIDTH, maximum))


class LeftPanelClient:
    def __init__(self, host: "LeftPanelHost", client_id: str) -> None:
        self._host = host
        self._client_id = client_id

    @property
    def is_visible(self) -> bool:
        return self._host.active_client == self._client_id

    def show(self) -> None:
        self._host.show(self._client_id)

    def hide(self) -> None:
        self._host.hide(self._client_id)

    def subscribe(self, callback: Callable[[bool], None]) -> None:
        self._host.subscribe(self._client_id, callback)


class LeftPanelHost:
    """Own exactly one optional first child of the outer horizontal Gtk.Paned."""

    def __init__(self, paned: Any, on_layout_changed: Callable[[], None]) -> None:
        if paned is None:
            raise TypeError("paned is required")
        if not callable(on_layout_changed):
            raise TypeError("on_layout_changed must be callable")
        self._paned = paned
        self._on_layout_changed = on_layout_changed
        self._widgets: dict[str, Any] = {}
        self._listeners: dict[str, list[Callable[[bool], None]]] = {
            key: [] for key in ALLOWED_LEFT_CLIENTS
        }
        self._active_client: str | None = None

    @property
    def active_client(self) -> str | None:
        return self._active_client

    def register(self, client_id: str, widget: Any) -> LeftPanelClient:
        key = self._require_allowed(client_id)
        if widget is None:
            raise TypeError("widget is required")
        if key in self._widgets:
            raise ValueError(f"left-panel client already registered: {key}")
        self._widgets[key] = widget
        return LeftPanelClient(self, key)

    def subscribe(self, client_id: str, callback: Callable[[bool], None]) -> None:
        key = self._require_registered(client_id)
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._listeners[key].append(callback)

    def show(self, client_id: str) -> None:
        key = self._require_registered(client_id)
        previous = self._active_client
        if previous != key:
            self._detach_active()
            widget = self._widgets[key]
            if widget.get_parent() is None:
                self._paned.pack1(widget, False, True)
            self._active_client = key
            if previous is not None:
                self._notify(previous, False)
            self._notify(key, True)
        widget = self._widgets[key]
        self._configure_widget(widget)
        widget.show_all()
        self._on_layout_changed()

    def hide(self, client_id: str) -> None:
        key = self._require_registered(client_id)
        if self._active_client != key:
            return
        self._detach_active()
        self._notify(key, False)
        self._on_layout_changed()

    def _detach_active(self) -> None:
        if self._active_client is None:
            return
        widget = self._widgets[self._active_client]
        if widget.get_parent() is not None:
            self._paned.remove(widget)
        self._active_client = None

    def _configure_widget(self, widget: Any) -> None:
        allocation = self._paned.get_allocation()
        total_width = getattr(allocation, "width", 900) or 900
        panel_width = calculate_left_panel_width(total_width)
        # Xed packs its side pane with shrink enabled and lets Gtk.Paned own
        # the current width.  A positive widget size request turns the side
        # panel into a top-level minimum-width constraint and can make the
        # window appear locked.
        widget.set_size_request(-1, -1)
        widget.set_hexpand(False)
        widget.set_vexpand(True)
        self._paned.set_position(panel_width)

    def _notify(self, client_id: str, visible: bool) -> None:
        for callback in tuple(self._listeners[client_id]):
            callback(bool(visible))

    def _require_allowed(self, client_id: str) -> str:
        if not isinstance(client_id, str) or client_id not in ALLOWED_LEFT_CLIENTS:
            raise KeyError(client_id)
        return client_id

    def _require_registered(self, client_id: str) -> str:
        key = self._require_allowed(client_id)
        if key not in self._widgets:
            raise KeyError(key)
        return key
