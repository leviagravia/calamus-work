"""GTK dialogs for editing and protecting Calamus References."""
from __future__ import annotations

from calamus_references import ReferenceRecord, reference_types, suggest_reference_key


def run_reference_dialog(parent, existing_keys, record: ReferenceRecord | None = None) -> ReferenceRecord | None:
    from gi.repository import Gtk

    dialog = Gtk.Dialog(
        title="Edit Reference" if record else "Add Reference",
        transient_for=parent,
        modal=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Save", Gtk.ResponseType.OK)
    dialog.set_default_size(620, 560)

    notebook = Gtk.Notebook()
    notebook.set_margin_start(10)
    notebook.set_margin_end(10)
    notebook.set_margin_top(10)
    notebook.set_margin_bottom(10)
    dialog.get_content_area().pack_start(notebook, True, True, 0)

    basic = Gtk.Grid(column_spacing=8, row_spacing=7)
    basic.set_border_width(8)
    publication = Gtk.Grid(column_spacing=8, row_spacing=7)
    publication.set_border_width(8)
    notebook.append_page(basic, Gtk.Label(label="Basic"))
    notebook.append_page(publication, Gtk.Label(label="Publication"))

    entries = {}

    def add_entry(grid, row, label, name, value=""):
        lab = Gtk.Label(label=label)
        lab.set_xalign(0)
        entry = Gtk.Entry()
        entry.set_text(value or "")
        grid.attach(lab, 0, row, 1, 1)
        grid.attach(entry, 1, row, 1, 1)
        entries[name] = entry
        return entry

    key_entry = add_entry(basic, 0, "Key", "key", record.key if record else "")
    suggest_button = Gtk.Button(label="Suggest")
    basic.attach(suggest_button, 2, 0, 1, 1)

    type_label = Gtk.Label(label="Type")
    type_label.set_xalign(0)
    type_combo = Gtk.ComboBoxText()
    for value in reference_types():
        type_combo.append_text(value)
    current_type = record.type if record else "book"
    type_combo.set_active(max(0, reference_types().index(current_type) if current_type in reference_types() else 0))
    basic.attach(type_label, 0, 1, 1, 1)
    basic.attach(type_combo, 1, 1, 2, 1)

    authors_entry = add_entry(basic, 2, "Authors", "authors", "; ".join(record.authors) if record else "")
    authors_entry.set_placeholder_text("Separate authors with ; — use Surname, Given")
    title_entry = add_entry(basic, 3, "Title", "title", record.title if record else "")
    year_entry = add_entry(basic, 4, "Year / Date", "year", record.year if record else "")
    tags_entry = add_entry(basic, 5, "Tags", "tags", ", ".join(record.tags) if record else "")

    annotation_label = Gtk.Label(label="Annotation")
    annotation_label.set_xalign(0)
    annotation = Gtk.TextView()
    annotation.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    annotation.get_buffer().set_text(record.annotation if record else "")
    annotation_scroll = Gtk.ScrolledWindow()
    annotation_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    annotation_scroll.set_size_request(-1, 170)
    annotation_scroll.add(annotation)
    basic.attach(annotation_label, 0, 6, 1, 1)
    basic.attach(annotation_scroll, 1, 6, 2, 1)

    pub_values = {
        "editors": "; ".join(record.editors) if record else "",
        "container_title": record.container_title if record else "",
        "publisher": record.publisher if record else "",
        "location": record.location if record else "",
        "volume": record.volume if record else "",
        "issue": record.issue if record else "",
        "pages": record.pages if record else "",
        "doi": record.doi if record else "",
        "isbn": record.isbn if record else "",
        "issn": record.issn if record else "",
        "url": record.url if record else "",
        "language": record.language if record else "",
        "file_path": record.file_path if record else "",
    }
    labels = (
        ("Editors", "editors"),
        ("Container Title", "container_title"),
        ("Publisher", "publisher"),
        ("Location", "location"),
        ("Volume", "volume"),
        ("Issue", "issue"),
        ("Pages", "pages"),
        ("DOI", "doi"),
        ("ISBN", "isbn"),
        ("ISSN", "issn"),
        ("URL", "url"),
        ("Language", "language"),
        ("Local File", "file_path"),
    )
    for row, (label, name) in enumerate(labels):
        add_entry(publication, row, label, name, pub_values[name])

    def suggest(*_):
        excluded = set(existing_keys)
        if record:
            excluded.discard(record.key)
        key_entry.set_text(
            suggest_reference_key(
                authors_entry.get_text().split(";"),
                year_entry.get_text(),
                title_entry.get_text(),
                excluded,
            )
        )
    suggest_button.connect("clicked", suggest)

    dialog.show_all()
    result = None
    while True:
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            break
        try:
            buffer = annotation.get_buffer()
            start, end = buffer.get_bounds()
            result = ReferenceRecord(
                key=key_entry.get_text(),
                title=title_entry.get_text(),
                type=type_combo.get_active_text() or "other",
                authors=tuple(authors_entry.get_text().split(";")),
                year=year_entry.get_text(),
                editors=tuple(entries["editors"].get_text().split(";")),
                container_title=entries["container_title"].get_text(),
                publisher=entries["publisher"].get_text(),
                location=entries["location"].get_text(),
                volume=entries["volume"].get_text(),
                issue=entries["issue"].get_text(),
                pages=entries["pages"].get_text(),
                doi=entries["doi"].get_text(),
                isbn=entries["isbn"].get_text(),
                issn=entries["issn"].get_text(),
                url=entries["url"].get_text(),
                language=entries["language"].get_text(),
                file_path=entries["file_path"].get_text(),
                tags=tuple(entries["tags"].get_text().split(",")),
                annotation=buffer.get_text(start, end, True),
                extra_fields=record.extra_fields if record else (),
            )
        except ValueError as error:
            message = Gtk.MessageDialog(
                transient_for=dialog,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=str(error),
            )
            message.run()
            message.destroy()
            continue
        break
    dialog.destroy()
    return result


def confirm_reference_delete(parent, record: ReferenceRecord) -> bool:
    from gi.repository import Gtk
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.NONE,
        text=f"Delete reference {record.key}?",
    )
    dialog.format_secondary_text(record.title)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Delete", Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def resolve_external_reference_change(parent) -> str:
    from gi.repository import Gtk
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text="References changed outside Calamus.",
    )
    dialog.format_secondary_text("Reload the external version, overwrite it, or cancel this change.")
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Reload", 10)
    dialog.add_button("Overwrite", 20)
    response = dialog.run()
    dialog.destroy()
    return {10: "reload", 20: "overwrite"}.get(response, "cancel")
