"""GTK shell for built-in Calamus Research clients."""
from __future__ import annotations

from typing import Any, Callable

from calamus_panel_chrome import build_compact_close_button


class ResearchPanelViewAdapter:
    def __init__(self, on_hide: Callable[[], None]) -> None:
        if not callable(on_hide):
            raise TypeError("on_hide must be callable")
        from gi.repository import Gtk

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.widget.set_margin_start(3)
        self.widget.set_margin_end(3)
        self.widget.set_margin_top(3)
        self.widget.set_margin_bottom(3)
        self._clients: dict[str, tuple[Any, Callable[[], None] | None]] = {}
        self._syncing_selector = False

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        title = Gtk.Label()
        title.set_markup("<b>Research</b>")
        title.set_xalign(0)
        title.set_hexpand(True)
        header.pack_start(title, True, True, 0)
        header.pack_end(
            build_compact_close_button(
                on_hide,
                name="research-close-button",
                tooltip="Hide Research Panel",
            ),
            False,
            False,
            0,
        )
        self.widget.pack_start(header, False, False, 0)

        # Three real clients no longer fit a narrow tab switcher without
        # forcing the whole editor wider. A compact selector preserves the
        # canonical single-client stack and full client names.
        self.selector = Gtk.ComboBoxText()
        self.selector.set_hexpand(True)
        self.widget.pack_start(self.selector, False, False, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.widget.pack_start(self.stack, True, True, 0)

        self.selector.connect("changed", self._on_selector_changed)
        self.stack.connect("notify::visible-child-name", self._on_visible_child_changed)

    @property
    def active_client(self) -> str | None:
        return self.stack.get_visible_child_name()

    def register_client(
        self,
        client_id: str,
        title: str,
        widget: Any,
        on_activate=None,
    ) -> None:
        if not isinstance(client_id, str) or not client_id.strip():
            raise ValueError("client_id must be a non-empty string")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        if client_id in self._clients:
            raise ValueError(f"Research client already registered: {client_id}")
        if widget is None:
            raise TypeError("widget is required")
        if on_activate is not None and not callable(on_activate):
            raise TypeError("on_activate must be callable")
        key = client_id.strip()
        self._clients[key] = (widget, on_activate)
        self.selector.append(key, title.strip())
        self.stack.add_named(widget, key)
        if len(self._clients) == 1:
            self.show_client(key)

    def show_client(self, client_id: str) -> None:
        if client_id not in self._clients:
            raise KeyError(client_id)
        self._syncing_selector = True
        try:
            self.selector.set_active_id(client_id)
            self.stack.set_visible_child_name(client_id)
        finally:
            self._syncing_selector = False
        self._activate(client_id)

    def focus_active(self) -> None:
        active = self.active_client
        if active:
            self._activate(active)

    def _on_selector_changed(self, selector) -> None:
        if self._syncing_selector:
            return
        client_id = selector.get_active_id()
        if client_id in self._clients:
            self.stack.set_visible_child_name(client_id)
            self._activate(client_id)

    def _on_visible_child_changed(self, *_):
        active = self.active_client
        if not active or self._syncing_selector:
            return
        if self.selector.get_active_id() != active:
            self._syncing_selector = True
            try:
                self.selector.set_active_id(active)
            finally:
                self._syncing_selector = False
        self._activate(active)

    def _activate(self, client_id: str) -> None:
        callback = self._clients[client_id][1]
        if callback is not None:
            callback()
