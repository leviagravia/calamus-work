"""GTK list view for the Calamus References client."""
from __future__ import annotations

from typing import Any, Callable

from calamus_references import ReferenceRecord


class ReferencePanelViewAdapter:
    def __init__(self, widget: Any, search: Any, listbox: Any, status: Any) -> None:
        self.widget = widget
        self.search = search
        self._listbox = listbox
        self._status = status
        self._rows: dict[str, Any] = {}
        self._on_search: Callable[[str], None] | None = None

    def bind_search(self, callback: Callable[[str], None]) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._on_search = callback
        self.search.connect("search-changed", lambda entry: callback(entry.get_text()))

    def render(self, records: tuple[ReferenceRecord, ...], selected_key: str | None, status: str) -> None:
        from gi.repository import Gtk, Pango

        for child in list(self._listbox.get_children()):
            self._listbox.remove(child)
        self._rows = {}
        for record in records:
            row = Gtk.ListBoxRow()
            row.reference_key = record.key
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            box.set_margin_start(4)
            box.set_margin_end(4)
            primary = Gtk.Label()
            primary.set_markup(f"<b>{_escape(record.author_year)}</b>")
            primary.set_xalign(0)
            primary.set_ellipsize(Pango.EllipsizeMode.END)
            secondary = Gtk.Label(label=record.title)
            secondary.set_xalign(0)
            secondary.set_ellipsize(Pango.EllipsizeMode.END)
            tertiary = Gtk.Label(label=record.key)
            tertiary.set_xalign(0)
            tertiary.get_style_context().add_class("dim-label")
            tertiary.set_ellipsize(Pango.EllipsizeMode.END)
            box.pack_start(primary, False, False, 0)
            box.pack_start(secondary, False, False, 0)
            box.pack_start(tertiary, False, False, 0)
            row.add(box)
            self._listbox.add(row)
            self._rows[record.key] = row
        self._listbox.show_all()
        self._status.set_text(status)
        self.select_key(selected_key)

    def selected_key(self) -> str | None:
        row = self._listbox.get_selected_row()
        return getattr(row, "reference_key", None) if row is not None else None

    def select_key(self, key: str | None) -> bool:
        if key is None:
            self._listbox.unselect_all()
            return False
        row = self._rows.get(key)
        if row is None:
            return False
        self._listbox.select_row(row)
        return True

    def focus_search(self) -> None:
        self.search.grab_focus()


def build_reference_panel_view(on_add, on_edit, on_delete, on_copy_key):
    from gi.repository import Gtk

    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    panel.set_margin_start(4)
    panel.set_margin_end(4)
    panel.set_margin_top(4)
    panel.set_margin_bottom(4)

    search = Gtk.SearchEntry()
    search.set_placeholder_text("Search references…")
    panel.pack_start(search, False, False, 0)

    status = Gtk.Label()
    status.set_xalign(0)
    panel.pack_start(status, False, False, 0)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)
    scroll.add(listbox)
    panel.pack_start(scroll, True, True, 0)

    primary = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    for label, callback in (("Add", on_add), ("Edit", on_edit), ("Delete", on_delete)):
        button = Gtk.Button(label=label)
        button.set_relief(Gtk.ReliefStyle.NORMAL)
        button.set_size_request(52, 26)
        button.connect("clicked", callback)
        primary.pack_start(button, True, True, 0)
    panel.pack_start(primary, False, False, 0)

    copy_button = Gtk.Button(label="Copy Key")
    copy_button.set_size_request(-1, 26)
    copy_button.connect("clicked", on_copy_key)
    panel.pack_start(copy_button, False, False, 0)

    adapter = ReferencePanelViewAdapter(panel, search, listbox, status)
    listbox.connect("row-activated", lambda *_: on_edit())
    return adapter


def _escape(value: str) -> str:
    from gi.repository import GLib
    return GLib.markup_escape_text(value or "")
