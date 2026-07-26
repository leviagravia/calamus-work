"""GTK dialogs for static transparent Reference Sets."""
from __future__ import annotations

from calamus_reference_sets import ReferenceSet
from calamus_references import ReferenceRecord

from calamus_modal_dialog import destroy_modal, run_modal


def _gtk():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    return Gtk

def run_reference_set_dialog(
    parent,
    records: tuple[ReferenceRecord, ...],
    existing_names: tuple[str, ...],
    item: ReferenceSet | None = None,
) -> ReferenceSet | None:
    Gtk = _gtk()

    dialog = Gtk.Dialog(
        title="Edit Reference Set" if item else "Add Reference Set",
        transient_for=parent,
        modal=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Save", Gtk.ResponseType.OK)
    dialog.set_default_size(650, 620)

    area = dialog.get_content_area()
    grid = Gtk.Grid(column_spacing=10, row_spacing=8)
    grid.set_border_width(12)
    area.pack_start(grid, False, False, 0)

    name = Gtk.Entry()
    name.set_name("reference-set-name")
    name.set_placeholder_text("Case-sensitive; preserved exactly")
    name.set_tooltip_text(
        "Reference Set names are case-sensitive and are written exactly as entered."
    )
    name.set_text(item.name if item else "")
    description = Gtk.Entry()
    description.set_name("reference-set-description")
    description.set_text(item.description if item else "")
    search = Gtk.SearchEntry()
    search.set_placeholder_text("Filter References…")

    for row, (label, widget) in enumerate((("Name", name), ("Description", description), ("Members", search))):
        prompt = Gtk.Label(label=label)
        prompt.set_xalign(0)
        grid.attach(prompt, 0, row, 1, 1)
        grid.attach(widget, 1, row, 1, 1)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.NONE)
    checks: dict[str, object] = {}
    selected = set(item.members if item else ())
    for record in records:
        row = Gtk.ListBoxRow()
        row.reference_key = record.key
        check = Gtk.CheckButton(
            label=f"{record.key} — {record.author_year} — {record.title}"
        )
        check.set_name(f"reference-set-member-{record.key}")
        check.set_active(record.key in selected)
        check.set_margin_start(4); check.set_margin_end(4)
        check.set_margin_top(3); check.set_margin_bottom(3)
        row.add(check)
        listbox.add(row)
        checks[record.key] = check

    def filter_row(row):
        needle = search.get_text().strip().casefold()
        if not needle:
            return True
        record = next((value for value in records if value.key == row.reference_key), None)
        return bool(record and needle in record.search_text)

    listbox.set_filter_func(filter_row)
    search.connect("search-changed", lambda *_: listbox.invalidate_filter())
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)
    scroll.add(listbox)
    area.pack_start(scroll, True, True, 0)

    note = Gtk.Label(
        label=(
            "Reference Sets are static ordered lists stored in reference-sets.md. "
            "Names are case-sensitive and preserved exactly. They do not copy "
            "bibliographic metadata and are never dynamic queries."
        )
    )
    note.set_xalign(0); note.set_line_wrap(True)
    note.set_margin_start(12); note.set_margin_end(12); note.set_margin_bottom(10)
    area.pack_start(note, False, False, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()
    result = None
    while True:
        response = run_modal(dialog)
        if response != Gtk.ResponseType.OK:
            break
        requested_name = name.get_text().strip()
        collision = next(
            (
                value for value in existing_names
                if value.casefold() == requested_name.casefold()
                and (item is None or value != item.name)
            ),
            None,
        )
        if collision:
            _message(dialog, "Duplicate Reference Set", f"A set named {collision} already exists.", error=True)
            continue
        try:
            result = ReferenceSet(
                requested_name,
                description.get_text(),
                tuple(record.key for record in records if checks[record.key].get_active()),
            )
        except ValueError as error:
            _message(dialog, "Invalid Reference Set", str(error), error=True)
            continue
        break
    destroy_modal(dialog)
    return result


def confirm_reference_set_delete(parent, item: ReferenceSet) -> bool:
    Gtk = _gtk()
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.NONE,
        text=f"Delete Reference Set {item.name}?",
    )
    dialog.format_secondary_text(
        f"The set contains {len(item.members)} member(s). References will not be deleted."
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Delete Set", Gtk.ResponseType.OK)
    response = run_modal(dialog)
    destroy_modal(dialog)
    return response == Gtk.ResponseType.OK


def resolve_external_reference_set_change(parent) -> str:
    Gtk = _gtk()
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text="Reference Sets changed outside Calamus.",
    )
    dialog.format_secondary_text("Reload the external version, overwrite it, or cancel this change.")
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Reload", 10)
    dialog.add_button("Overwrite", 20)
    response = run_modal(dialog)
    destroy_modal(dialog)
    return {10: "reload", 20: "overwrite"}.get(response, "cancel")


def _message(parent, title: str, detail: str, *, error: bool) -> None:
    Gtk = _gtk()
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(detail)
    run_modal(dialog)
    destroy_modal(dialog)
