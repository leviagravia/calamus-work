"""GTK dialogs for editing and protecting document Source Notes."""
from __future__ import annotations

from calamus_source_notes import (
    SourceLocator,
    SourceNote,
    new_source_note_id,
    now_iso,
    source_note_kinds,
)


def run_source_note_dialog(
    parent,
    reference_keys,
    existing_ids,
    note: SourceNote | None = None,
) -> SourceNote | None:
    from gi.repository import Gtk

    keys = tuple(dict.fromkeys(reference_keys))
    dialog = Gtk.Dialog(
        title="Edit Source Note" if note else "Add Source Note",
        transient_for=parent,
        modal=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Save", Gtk.ResponseType.OK)
    dialog.set_default_size(650, 620)

    notebook = Gtk.Notebook()
    notebook.set_margin_start(10)
    notebook.set_margin_end(10)
    notebook.set_margin_top(10)
    notebook.set_margin_bottom(10)
    dialog.get_content_area().pack_start(notebook, True, True, 0)

    content = Gtk.Grid(column_spacing=8, row_spacing=7)
    content.set_border_width(8)
    locator_grid = Gtk.Grid(column_spacing=8, row_spacing=7)
    locator_grid.set_border_width(8)
    notebook.append_page(content, Gtk.Label(label="Content"))
    notebook.append_page(locator_grid, Gtk.Label(label="Locator"))

    id_label = Gtk.Label(label="ID")
    id_label.set_xalign(0)
    id_entry = Gtk.Entry()
    id_entry.set_text(
        note.id if note else new_source_note_id(existing_ids)
    )
    id_entry.set_editable(False)
    content.attach(id_label, 0, 0, 1, 1)
    content.attach(id_entry, 1, 0, 2, 1)

    kind_label = Gtk.Label(label="Type")
    kind_label.set_xalign(0)
    kind_combo = Gtk.ComboBoxText()
    for kind in source_note_kinds():
        kind_combo.append(kind, kind.capitalize())
    kind_combo.set_active_id(note.kind if note else "quote")
    content.attach(kind_label, 0, 1, 1, 1)
    content.attach(kind_combo, 1, 1, 2, 1)

    reference_label = Gtk.Label(label="Reference")
    reference_label.set_xalign(0)
    reference_combo = Gtk.ComboBoxText()
    reference_combo.append("__none__", "No reference (Comment only)")
    for key in keys:
        reference_combo.append(key, key)
    if note and note.reference_key and note.reference_key not in keys:
        reference_combo.append(note.reference_key, f"Missing: {note.reference_key}")
    reference_combo.set_active_id(
        note.reference_key if note and note.reference_key else "__none__"
    )
    content.attach(reference_label, 0, 2, 1, 1)
    content.attach(reference_combo, 1, 2, 2, 1)

    tags_label = Gtk.Label(label="Tags")
    tags_label.set_xalign(0)
    tags_entry = Gtk.Entry()
    tags_entry.set_text(", ".join(note.tags) if note else "")
    content.attach(tags_label, 0, 3, 1, 1)
    content.attach(tags_entry, 1, 3, 2, 1)

    text_label = Gtk.Label(label="Text")
    text_label.set_xalign(0)
    text_view = Gtk.TextView()
    text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    text_view.get_buffer().set_text(note.text if note else "")
    text_scroll = Gtk.ScrolledWindow()
    text_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    text_scroll.set_size_request(-1, 210)
    text_scroll.add(text_view)
    content.attach(text_label, 0, 4, 1, 1)
    content.attach(text_scroll, 1, 4, 2, 1)

    comment_label = Gtk.Label(label="Comment")
    comment_label.set_xalign(0)
    comment_view = Gtk.TextView()
    comment_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    comment_view.get_buffer().set_text(note.comment if note else "")
    comment_scroll = Gtk.ScrolledWindow()
    comment_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    comment_scroll.set_size_request(-1, 150)
    comment_scroll.add(comment_view)
    content.attach(comment_label, 0, 5, 1, 1)
    content.attach(comment_scroll, 1, 5, 2, 1)

    locator_entries = {}
    locator_values = note.locator if note else SourceLocator()
    for row, (label, name) in enumerate((
        ("Page", "page"),
        ("Page End", "page_end"),
        ("Chapter", "chapter"),
        ("Section", "section"),
        ("Paragraph", "paragraph"),
    )):
        lab = Gtk.Label(label=label)
        lab.set_xalign(0)
        entry = Gtk.Entry()
        entry.set_text(getattr(locator_values, name))
        locator_grid.attach(lab, 0, row, 1, 1)
        locator_grid.attach(entry, 1, row, 1, 1)
        locator_entries[name] = entry

    hint = Gtk.Label(
        label=(
            "Quote and Paraphrase require a Reference. "
            "Comment may be independent."
        )
    )
    hint.set_xalign(0)
    hint.set_line_wrap(True)
    locator_grid.attach(hint, 0, 6, 2, 1)

    dialog.show_all()
    result = None
    while True:
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            break
        try:
            text_buffer = text_view.get_buffer()
            text_start, text_end = text_buffer.get_bounds()
            comment_buffer = comment_view.get_buffer()
            comment_start, comment_end = comment_buffer.get_bounds()
            stamp = now_iso()
            selected_reference = reference_combo.get_active_id() or "__none__"
            result = SourceNote(
                id=id_entry.get_text(),
                kind=kind_combo.get_active_id() or "comment",
                reference_key=(
                    "" if selected_reference == "__none__" else selected_reference
                ),
                locator=SourceLocator(
                    **{
                        name: entry.get_text()
                        for name, entry in locator_entries.items()
                    }
                ),
                text=text_buffer.get_text(text_start, text_end, True),
                comment=comment_buffer.get_text(comment_start, comment_end, True),
                tags=tuple(tags_entry.get_text().split(",")),
                created=note.created if note and note.created else stamp,
                modified=stamp,
                extra_fields=note.extra_fields if note else (),
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


def confirm_source_note_delete(parent, note: SourceNote) -> bool:
    from gi.repository import Gtk

    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.NONE,
        text=f"Delete Source Note {note.id}?",
    )
    dialog.format_secondary_text(note.excerpt)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Delete", Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def resolve_external_source_note_change(parent) -> str:
    from gi.repository import Gtk

    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text="Source Notes changed outside Calamus.",
    )
    dialog.format_secondary_text(
        "Reload the external version, overwrite it, or cancel this change."
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Reload", 10)
    dialog.add_button("Overwrite", 20)
    response = dialog.run()
    dialog.destroy()
    return {10: "reload", 20: "overwrite"}.get(response, "cancel")
