"""GTK dialogs for Quick Cite and multi-key citation selection."""
from __future__ import annotations

from typing import Iterable

from calamus_citations import format_pandoc_citation, normalize_locator
from calamus_references import ReferenceRecord


def run_quick_cite_dialog(
    parent,
    records: Iterable[ReferenceRecord],
    *,
    initial_key: str | None = None,
) -> tuple[str, str] | None:
    from gi.repository import GLib, Gtk, Pango

    records = tuple(records)
    if any(not isinstance(record, ReferenceRecord) for record in records):
        raise TypeError("records must contain ReferenceRecord values")

    dialog = Gtk.Dialog(title="Quick Cite", transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Insert Citation", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_default_size(580, 470)

    content = dialog.get_content_area()
    content.set_spacing(8)
    content.set_margin_start(10)
    content.set_margin_end(10)
    content.set_margin_top(10)
    content.set_margin_bottom(10)

    search = Gtk.SearchEntry()
    search.set_placeholder_text("Search author, title, year, key or tag…")
    search.set_activates_default(True)
    content.pack_start(search, False, False, 0)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)
    scroll.add(listbox)
    content.pack_start(scroll, True, True, 0)

    locator_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    locator_label = Gtk.Label(label="Locator")
    locator_label.set_xalign(0)
    locator = Gtk.Entry()
    locator.set_placeholder_text("Optional, for example: p. 42")
    locator.set_activates_default(True)
    locator_box.pack_start(locator_label, False, False, 0)
    locator_box.pack_start(locator, True, True, 0)
    content.pack_start(locator_box, False, False, 0)

    preview = Gtk.Label()
    preview.set_xalign(0)
    preview.set_selectable(True)
    content.pack_start(preview, False, False, 0)

    rows: dict[str, object] = {}

    def selected_key() -> str | None:
        row = listbox.get_selected_row()
        return getattr(row, "reference_key", None) if row is not None else None

    def update_preview(*_):
        key = selected_key()
        if not key:
            preview.set_text("Select a reference.")
            return
        preview.set_text(format_pandoc_citation(key, locator.get_text()))

    def render(query: str = ""):
        previous = selected_key() or initial_key
        needle = (query or "").strip().casefold()
        for child in list(listbox.get_children()):
            listbox.remove(child)
        rows.clear()
        visible = tuple(
            record for record in records
            if not needle or needle in record.search_text
        )
        for record in visible:
            row = Gtk.ListBoxRow()
            row.reference_key = record.key
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            box.set_margin_start(5)
            box.set_margin_end(5)

            primary = Gtk.Label()
            primary.set_markup(
                f"<b>{GLib.markup_escape_text(record.author_year)}</b>"
            )
            primary.set_xalign(0)
            primary.set_ellipsize(Pango.EllipsizeMode.END)

            secondary = Gtk.Label(label=record.title)
            secondary.set_xalign(0)
            secondary.set_ellipsize(Pango.EllipsizeMode.END)

            key_label = Gtk.Label(label=record.key)
            key_label.set_xalign(0)
            key_label.get_style_context().add_class("dim-label")
            key_label.set_ellipsize(Pango.EllipsizeMode.END)

            box.pack_start(primary, False, False, 0)
            box.pack_start(secondary, False, False, 0)
            box.pack_start(key_label, False, False, 0)
            row.add(box)
            listbox.add(row)
            rows[record.key] = row

        listbox.show_all()
        row = rows.get(previous)
        if row is None and visible:
            row = rows.get(visible[0].key)
        if row is not None:
            listbox.select_row(row)
        update_preview()

    search.connect("search-changed", lambda entry: render(entry.get_text()))
    locator.connect("changed", update_preview)
    listbox.connect("row-selected", lambda *_: update_preview())
    listbox.connect("row-activated", lambda *_: dialog.response(Gtk.ResponseType.OK))

    render()
    dialog.show_all()
    search.grab_focus()

    result = None
    while True:
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            break
        key = selected_key()
        if key:
            result = (key, normalize_locator(locator.get_text()))
            break
        message = Gtk.MessageDialog(
            transient_for=dialog,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Select a reference to cite.",
        )
        message.run()
        message.destroy()

    dialog.destroy()
    return result


def choose_citation_key(parent, keys: Iterable[str]) -> str | None:
    from gi.repository import Gtk

    unique: list[str] = []
    for key in keys:
        value = key.strip() if isinstance(key, str) else ""
        if value and value not in unique:
            unique.append(value)
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]

    dialog = Gtk.Dialog(
        title="Choose Citation",
        transient_for=parent,
        modal=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Open Reference", Gtk.ResponseType.OK)
    dialog.set_default_size(420, 160)

    box = dialog.get_content_area()
    box.set_spacing(8)
    box.set_margin_start(10)
    box.set_margin_end(10)
    box.set_margin_top(10)
    box.set_margin_bottom(10)

    label = Gtk.Label(label="This citation contains more than one key.")
    label.set_xalign(0)
    box.pack_start(label, False, False, 0)

    combo = Gtk.ComboBoxText()
    for key in unique:
        combo.append_text(key)
    combo.set_active(0)
    box.pack_start(combo, False, False, 0)

    dialog.show_all()
    response = dialog.run()
    result = combo.get_active_text() if response == Gtk.ResponseType.OK else None
    dialog.destroy()
    return result
