"""GTK Clip Collection view adapter for the canonical right-panel host."""
from __future__ import annotations

from typing import Any, Callable


class ClipCollectionViewAdapter:
    """Own Clip Collection list widgets and activation semantics."""

    def __init__(
        self,
        panel: Any,
        listbox: Any,
        *,
        double_click_type: Any,
        on_activate: Callable[[], None],
    ) -> None:
        if panel is None or listbox is None:
            raise TypeError("panel and listbox are required")
        if not callable(on_activate):
            raise TypeError("on_activate must be callable")
        self._panel = panel
        self._listbox = listbox
        self._double_click_type = double_click_type
        self._on_activate = on_activate

    @property
    def widget(self) -> Any:
        return self._panel

    def render(self, clips: list[dict[str, Any]]) -> None:
        from gi.repository import Gtk

        for child in list(self._listbox.get_children()):
            self._listbox.remove(child)
        for clip in clips:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=clip.get("title", "Clip"))
            label.set_xalign(0)
            label.set_margin_top(4)
            label.set_margin_bottom(4)
            row.add(label)
            self._listbox.add(row)
        self._listbox.show_all()

    def selected_index(self) -> int | None:
        row = self._listbox.get_selected_row()
        return row.get_index() if row is not None else None

    def select_index(self, index: int) -> bool:
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            return False
        row = self._listbox.get_row_at_index(index)
        if row is None:
            return False
        self._listbox.select_row(row)
        return True

    def on_button_press(self, listbox: Any, event: Any) -> bool:
        """Activate only a primary-button double click, never keyboard Enter."""
        if event.type != self._double_click_type or getattr(event, "button", 0) != 1:
            return False
        row = listbox.get_row_at_y(int(event.y))
        if row is None:
            return False
        listbox.select_row(row)
        self._on_activate()
        return True


def build_clip_collection_view(on_add, on_insert, on_delete, on_activate):
    from gi.repository import Gdk, Gtk, Pango
    from calamus_layout import RIGHT_PANEL_DEFAULT_WIDTH

    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    panel.set_size_request(RIGHT_PANEL_DEFAULT_WIDTH, -1)
    panel.set_hexpand(False)
    panel.set_margin_start(3)
    panel.set_margin_end(3)
    panel.set_margin_top(3)
    panel.set_margin_bottom(3)

    title = Gtk.Label(label="Clip Collection")
    title.set_name("calamus-clip-title")
    title.set_xalign(0)
    title.set_ellipsize(Pango.EllipsizeMode.END)
    panel.pack_start(title, False, False, 0)

    clip_list = Gtk.ListBox()
    clip_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    clip_list.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    if hasattr(scroll, "set_propagate_natural_width"):
        scroll.set_propagate_natural_width(False)
    if hasattr(scroll, "set_propagate_natural_height"):
        scroll.set_propagate_natural_height(False)
    scroll.set_hexpand(False)
    scroll.set_vexpand(True)
    scroll.add(clip_list)
    panel.pack_start(scroll, True, True, 0)

    button_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    button_row.set_hexpand(False)
    button_row.set_halign(Gtk.Align.START)
    for label, callback in (("Add", on_add), ("Insert", on_insert), ("Delete", on_delete)):
        button = Gtk.Button(label=label)
        button.set_size_request(56, 26)
        button.set_relief(Gtk.ReliefStyle.NORMAL)
        button.set_hexpand(False)
        button.get_style_context().add_class("calamus-clip-button")
        button.connect("clicked", callback)
        button_row.pack_start(button, False, False, 0)
    panel.pack_start(button_row, False, False, 0)

    adapter = ClipCollectionViewAdapter(
        panel,
        clip_list,
        double_click_type=Gdk.EventType._2BUTTON_PRESS,
        on_activate=on_activate,
    )
    clip_list.connect("button-press-event", adapter.on_button_press)
    return adapter
