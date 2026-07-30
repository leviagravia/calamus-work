"""GTK shell for built-in Calamus Research clients."""
from __future__ import annotations

from typing import Any, Callable

from calamus_panel_chrome import build_compact_close_button


class ResearchClientSelector:
    """Compact semantic selector whose client list opens below from the top.

    GtkComboBox aligns its popup around the active row. With many Research
    clients that made earlier items disappear above the control. This boundary
    keeps the same small public protocol while using a MenuButton + Popover
    whose requested position is BOTTOM and whose scroll position resets to the
    first client every time it opens.
    """

    def __init__(self) -> None:
        from gi.repository import GLib, Gtk

        self._Gtk = Gtk
        self._GLib = GLib
        self._active_id: str | None = None
        self._items: dict[str, tuple[str, Any, Any]] = {}
        self._changed_callbacks: list[Callable[[Any], None]] = []

        self.widget = Gtk.MenuButton()
        self.widget.set_name("research-client-selector")
        self.widget.set_hexpand(True)
        self.widget.set_tooltip_text("Choose a Research client")

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self._active_label = Gtk.Label(label="Choose Research client")
        self._active_label.set_xalign(0)
        self._active_label.set_hexpand(True)
        button_box.pack_start(self._active_label, True, True, 0)
        arrow = Gtk.Image.new_from_icon_name("pan-down-symbolic", Gtk.IconSize.MENU)
        button_box.pack_end(arrow, False, False, 0)
        self.widget.add(button_box)

        self.popover = Gtk.Popover.new(self.widget)
        self.popover.set_name("research-client-selector-popover")
        self.popover.set_position(Gtk.PositionType.BOTTOM)
        constrain = getattr(Gtk, "PopoverConstraint", None)
        if constrain is not None and hasattr(self.popover, "set_constrain_to"):
            self.popover.set_constrain_to(constrain.WINDOW)

        self.listbox = Gtk.ListBox()
        self.listbox.set_name("research-client-selector-list")
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.set_activate_on_single_click(True)
        self.listbox.connect("row-activated", self._on_row_activated)

        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        if hasattr(self._scroll, "set_propagate_natural_height"):
            self._scroll.set_propagate_natural_height(True)
        if hasattr(self._scroll, "set_max_content_height"):
            self._scroll.set_max_content_height(320)
        self._scroll.add(self.listbox)
        self.popover.add(self._scroll)
        # GtkPopover.popup() maps the popover itself but does not override the
        # visibility state of hidden descendants.  Keep the complete child
        # hierarchy visible before the MenuButton can open it.  This follows
        # Xed's GTK3 selector pattern, where the selector and every nested
        # scrolled/list child are explicitly visible before attachment.
        self._scroll.show_all()
        self.widget.set_popover(self.popover)
        self.popover.connect("show", self._on_popover_show)

    def connect(self, signal_name: str, callback: Callable[[Any], None]) -> int:
        if signal_name != "changed":
            raise ValueError(f"unsupported selector signal: {signal_name}")
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._changed_callbacks.append(callback)
        return len(self._changed_callbacks)

    def append(self, client_id: str, title: str) -> None:
        key = client_id.strip()
        label_text = title.strip()
        if not key or not label_text:
            raise ValueError("client ID and title must be non-empty")
        if key in self._items:
            raise ValueError(f"selector client already exists: {key}")

        Gtk = self._Gtk
        row = Gtk.ListBoxRow()
        row.set_name(f"research-client-row-{key}")
        row._calamus_client_id = key
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        content.set_margin_start(8)
        content.set_margin_end(8)
        content.set_margin_top(5)
        content.set_margin_bottom(5)
        check = Gtk.Image.new_from_icon_name("object-select-symbolic", Gtk.IconSize.MENU)
        check.set_no_show_all(True)
        check.hide()
        content.pack_start(check, False, False, 0)
        title_label = Gtk.Label(label=label_text)
        title_label.set_xalign(0)
        title_label.set_hexpand(True)
        content.pack_start(title_label, True, True, 0)
        row.add(content)
        self.listbox.add(row)
        self._items[key] = (label_text, row, check)
        row.show_all()
        check.hide()

    def get_active_id(self) -> str | None:
        return self._active_id

    def set_active_id(self, client_id: str) -> bool:
        if client_id not in self._items:
            return False
        changed = client_id != self._active_id
        self._active_id = client_id
        self._active_label.set_text(self._items[client_id][0])
        for key, (_title, _row, check) in self._items.items():
            check.set_visible(key == client_id)
        if changed:
            for callback in tuple(self._changed_callbacks):
                callback(self)
        return True

    def popup(self) -> None:
        self._ensure_popup_children_visible()
        self.popover.set_position(self._Gtk.PositionType.BOTTOM)
        self.popover.popup()

    def popdown(self) -> None:
        self.popover.popdown()

    def listed_ids(self) -> tuple[str, ...]:
        return tuple(
            getattr(row, "_calamus_client_id", "")
            for row in self.listbox.get_children()
        )

    def popup_position(self):
        return self.popover.get_position()

    def _on_row_activated(self, _listbox, row) -> None:
        client_id = getattr(row, "_calamus_client_id", "")
        if client_id in self._items:
            self.set_active_id(client_id)
        self.popdown()

    def _ensure_popup_children_visible(self) -> None:
        """Expose and size the real GTK child hierarchy before popup mapping."""
        self._scroll.show_all()
        # Keep the popup at least as wide as its selector when GTK has already
        # allocated the button.  Natural row width remains authoritative when
        # it is larger.
        width = self.widget.get_allocated_width()
        if width > 1 and hasattr(self._scroll, "set_min_content_width"):
            self._scroll.set_min_content_width(width)

    def _on_popover_show(self, *_args) -> None:
        # Reassert the downward contract and start from the first item. Do not
        # align the list around the active client as GtkComboBox does.
        self._ensure_popup_children_visible()
        self.popover.set_position(self._Gtk.PositionType.BOTTOM)
        self.listbox.unselect_all()
        rows = self.listbox.get_children()
        if rows:
            self.listbox.select_row(rows[0])

        def reset_to_top():
            adjustment = self._scroll.get_vadjustment()
            adjustment.set_value(adjustment.get_lower())
            return False

        self._GLib.idle_add(reset_to_top)


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

        self.selector = ResearchClientSelector()
        self.widget.pack_start(self.selector.widget, False, False, 0)

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

    def _on_selector_changed(self, selector) -> None:
        if self._syncing_selector:
            return
        client_id = selector.get_active_id()
        if client_id not in self._clients:
            return
        self._syncing_selector = True
        try:
            self.stack.set_visible_child_name(client_id)
        finally:
            self._syncing_selector = False
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
