"""GTK view for the Calamus static Reference Sets Research client."""
from __future__ import annotations

from typing import Any, Callable

from calamus_reference_sets import ReferenceSet
from calamus_references import ReferenceRecord


def _gtk_pango():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Pango", "1.0")
    from gi.repository import Gtk, Pango
    return Gtk, Pango


def _gtk():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    return Gtk


def _glib():
    from gi.repository import GLib
    return GLib

class ReferenceSetViewAdapter:
    def __init__(
        self,
        widget: Any,
        search: Any,
        selector: Any,
        description: Any,
        listbox: Any,
        status: Any,
    ) -> None:
        self.widget = widget
        self.search = search
        self._selector = selector
        self._description = description
        self._listbox = listbox
        self._status = status
        self._member_rows: dict[str, Any] = {}
        self._rendering = False

    def bind_search(self, callback: Callable[[str], None]) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        self.search.connect("search-changed", lambda entry: callback(entry.get_text()))

    def bind_set_changed(self, callback: Callable[[], None]) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._selector.connect("changed", lambda *_: None if self._rendering else callback())

    def render(
        self,
        sets: tuple[ReferenceSet, ...],
        selected_set: str | None,
        records: tuple[ReferenceRecord, ...],
        selected_member: str | None,
        status: str,
    ) -> None:
        Gtk, Pango = _gtk_pango()

        self._rendering = True
        try:
            self._selector.remove_all()
            for item in sets:
                self._selector.append(item.name, item.name)
            if selected_set is not None:
                self._selector.set_active_id(selected_set)
            elif sets:
                self._selector.set_active(0)
            selected = next((item for item in sets if item.name == self._selector.get_active_id()), None)
            self._description.set_text(selected.description if selected else "")

            for child in list(self._listbox.get_children()):
                self._listbox.remove(child)
            self._member_rows = {}
            by_key = {record.key: record for record in records}
            if selected is not None:
                for key in selected.members:
                    row = Gtk.ListBoxRow()
                    row.reference_key = key
                    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                    box.set_margin_start(4); box.set_margin_end(4)
                    box.set_margin_top(4); box.set_margin_bottom(4)
                    record = by_key.get(key)
                    primary = Gtk.Label()
                    primary.set_xalign(0)
                    primary.set_ellipsize(Pango.EllipsizeMode.END)
                    primary.set_markup(f"<b>{_escape(key)}</b>")
                    secondary = Gtk.Label(
                        label=(f"{record.author_year} — {record.title}" if record else "Missing Reference")
                    )
                    secondary.set_xalign(0)
                    secondary.set_ellipsize(Pango.EllipsizeMode.END)
                    if record is None:
                        secondary.get_style_context().add_class("error")
                    box.pack_start(primary, False, False, 0)
                    box.pack_start(secondary, False, False, 0)
                    row.add(box)
                    self._listbox.add(row)
                    self._member_rows[key] = row
            self._listbox.show_all()
            self._status.set_text(status)
            self.select_member_key(selected_member)
        finally:
            self._rendering = False

    def selected_set_name(self) -> str | None:
        return self._selector.get_active_id()

    def selected_member_key(self) -> str | None:
        row = self._listbox.get_selected_row()
        return getattr(row, "reference_key", None) if row is not None else None

    def select_set_name(self, name: str | None) -> bool:
        if name is None:
            self._selector.set_active(-1)
            return False
        return bool(self._selector.set_active_id(name))

    def select_member_key(self, key: str | None) -> bool:
        if key is None:
            self._listbox.unselect_all()
            return False
        row = self._member_rows.get(key)
        if row is None:
            return False
        self._listbox.select_row(row)
        return True

    def focus_search(self) -> None:
        self.search.grab_focus()


def build_reference_set_view(on_add, on_edit, on_delete, on_open):
    Gtk = _gtk()

    callbacks = (on_add, on_edit, on_delete, on_open)
    if any(not callable(callback) for callback in callbacks):
        raise TypeError("Reference Set action callbacks must be callable")

    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    panel.set_margin_start(4); panel.set_margin_end(4)
    panel.set_margin_top(4); panel.set_margin_bottom(4)

    search = Gtk.SearchEntry()
    search.set_placeholder_text("Search Reference Sets…")
    panel.pack_start(search, False, False, 0)

    selector = Gtk.ComboBoxText()
    selector.set_hexpand(True)
    panel.pack_start(selector, False, False, 0)

    description = Gtk.Label()
    description.set_xalign(0)
    description.set_line_wrap(True)
    description.get_style_context().add_class("dim-label")
    panel.pack_start(description, False, False, 0)

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

    buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    for label, callback in (("Add", on_add), ("Edit", on_edit), ("Delete", on_delete)):
        button = Gtk.Button(label=label)
        button.set_size_request(52, 26)
        button.connect("clicked", callback)
        buttons.pack_start(button, True, True, 0)
    panel.pack_start(buttons, False, False, 0)

    open_button = Gtk.Button(label="Open Reference")
    open_button.set_size_request(-1, 26)
    open_button.connect("clicked", on_open)
    panel.pack_start(open_button, False, False, 0)

    adapter = ReferenceSetViewAdapter(panel, search, selector, description, listbox, status)
    listbox.connect("row-activated", lambda *_: on_open())
    return adapter


def _escape(value: str) -> str:
    GLib = _glib()
    return GLib.markup_escape_text(value or "")
