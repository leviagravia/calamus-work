"""GTK dialogs for Scratchpad editing and stale-safe persistence."""
from __future__ import annotations

from calamus_modal_dialog import destroy_modal, run_modal
from calamus_scratchpad import (
    ScratchpadEntry,
    new_scratchpad_id,
    now_iso,
    scratchpad_states,
    scratchpad_types,
)


def run_scratchpad_dialog(
    parent,
    target_options,
    existing_ids,
    entry: ScratchpadEntry | None = None,
    *,
    draft: ScratchpadEntry | None = None,
) -> ScratchpadEntry | None:
    from gi.repository import Gtk

    if entry is not None and draft is not None:
        raise ValueError("entry and draft are mutually exclusive")
    initial = entry or draft
    targets = tuple(dict.fromkeys(target_options))
    dialog = Gtk.Dialog(
        title="Edit Scratchpad Entry" if entry else "New Scratchpad Entry",
        transient_for=parent,
        modal=True,
    )
    dialog.set_name("calamus-scratchpad-dialog")
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Save", Gtk.ResponseType.OK)
    dialog.set_default_size(620, 620)

    grid = Gtk.Grid(column_spacing=8, row_spacing=7)
    grid.set_margin_start(10)
    grid.set_margin_end(10)
    grid.set_margin_top(10)
    grid.set_margin_bottom(10)
    dialog.get_content_area().pack_start(grid, True, True, 0)

    id_entry = Gtk.Entry()
    id_entry.set_name("scratchpad-id")
    id_entry.set_text(initial.id if initial else new_scratchpad_id(existing_ids))
    id_entry.set_editable(False)
    _attach(grid, "ID", id_entry, 0)

    title_entry = Gtk.Entry()
    title_entry.set_name("scratchpad-title")
    title_entry.set_text(initial.title if initial else "")
    _attach(grid, "Title", title_entry, 1)

    type_combo = Gtk.ComboBoxText()
    type_combo.set_name("scratchpad-type")
    for value in scratchpad_types():
        type_combo.append(value, value.capitalize())
    type_combo.set_active_id(initial.type if initial else "note")
    _attach(grid, "Type", type_combo, 2)

    status_combo = Gtk.ComboBoxText()
    status_combo.set_name("scratchpad-status")
    for value in scratchpad_states():
        status_combo.append(value, value.capitalize())
    status_combo.set_active_id(initial.status if initial else "inbox")
    _attach(grid, "Status", status_combo, 3)

    tags_entry = Gtk.Entry()
    tags_entry.set_name("scratchpad-tags")
    tags_entry.set_text(", ".join(initial.tags) if initial else "")
    tags_entry.set_placeholder_text("manual, flat, tags")
    _attach(grid, "Tags", tags_entry, 4)

    sections_label = Gtk.Label(label="Linked sections")
    sections_label.set_xalign(0)
    grid.attach(sections_label, 0, 5, 1, 1)
    sections_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    section_checks = []
    selected_targets = set(initial.sections if initial else ())
    for target, label in targets:
        check = Gtk.CheckButton(label=label)
        check.set_name("scratchpad-section")
        check.scratchpad_target = target
        check.set_active(target in selected_targets)
        sections_box.pack_start(check, False, False, 0)
        section_checks.append(check)
    for missing in sorted(selected_targets - {target for target, _label in targets}):
        check = Gtk.CheckButton(label=f"Missing or ambiguous: {missing}")
        check.set_name("scratchpad-section")
        check.scratchpad_target = missing
        check.set_active(True)
        sections_box.pack_start(check, False, False, 0)
        section_checks.append(check)
    if not section_checks:
        unavailable = Gtk.Label(label="No unique {#heading-id} targets in this document.")
        unavailable.set_xalign(0)
        unavailable.set_line_wrap(True)
        sections_box.pack_start(unavailable, False, False, 0)
    section_scroll = Gtk.ScrolledWindow()
    section_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    section_scroll.set_size_request(-1, 130)
    section_scroll.add(sections_box)
    grid.attach(section_scroll, 1, 5, 1, 1)

    body_view = Gtk.TextView()
    body_view.set_name("scratchpad-body")
    body_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    body_view.get_buffer().set_text(initial.body if initial else "")
    body_scroll = Gtk.ScrolledWindow()
    body_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    body_scroll.set_size_request(-1, 250)
    body_scroll.add(body_view)
    grid.attach(Gtk.Label(label="Body", xalign=0), 0, 6, 1, 1)
    grid.attach(body_scroll, 1, 6, 1, 1)

    hint = Gtk.Label(
        label=(
            "Links are explicit and use unique Pandoc heading IDs. "
            "Calamus never infers concepts, tags or relations."
        )
    )
    hint.set_xalign(0)
    hint.set_line_wrap(True)
    grid.attach(hint, 0, 7, 2, 1)

    result = None
    while True:
        dialog.show_all()
        response = run_modal(dialog)
        if response != Gtk.ResponseType.OK:
            break
        try:
            body_buffer = body_view.get_buffer()
            start, end = body_buffer.get_bounds()
            stamp = now_iso()
            result = ScratchpadEntry(
                id=id_entry.get_text(),
                type=type_combo.get_active_id() or "note",
                title=title_entry.get_text(),
                status=status_combo.get_active_id() or "inbox",
                tags=tuple(tags_entry.get_text().split(",")),
                sections=tuple(
                    check.scratchpad_target
                    for check in section_checks
                    if check.get_active()
                ),
                created=initial.created if initial and initial.created else stamp,
                updated=stamp,
                body=body_buffer.get_text(start, end, True),
                extra_fields=initial.extra_fields if initial else (),
            )
        except ValueError as error:
            message = Gtk.MessageDialog(
                transient_for=dialog,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=str(error),
            )
            run_modal(message)
            destroy_modal(message)
            continue
        break
    destroy_modal(dialog)
    return result


def _attach(grid, label: str, widget, row: int) -> None:
    from gi.repository import Gtk
    lab = Gtk.Label(label=label)
    lab.set_xalign(0)
    grid.attach(lab, 0, row, 1, 1)
    grid.attach(widget, 1, row, 1, 1)


def confirm_scratchpad_delete(parent, entry: ScratchpadEntry) -> bool:
    from gi.repository import Gtk
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.NONE,
        text=f'Delete “{entry.title}” permanently?',
    )
    dialog.format_secondary_text(entry.excerpt)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Delete", Gtk.ResponseType.OK)
    dialog.show_all()
    response = run_modal(dialog)
    destroy_modal(dialog)
    return response == Gtk.ResponseType.OK


def resolve_external_scratchpad_change(parent) -> str:
    from gi.repository import Gtk
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text="Scratchpad changed outside Calamus.",
    )
    dialog.format_secondary_text("Reload the external version, overwrite it, or cancel this change.")
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Reload", 10)
    dialog.add_button("Overwrite", 20)
    dialog.show_all()
    response = run_modal(dialog)
    destroy_modal(dialog)
    return {10: "reload", 20: "overwrite"}.get(response, "cancel")


def choose_scratchpad_section(parent, sections: tuple[str, ...]) -> str | None:
    from gi.repository import Gtk
    if not sections:
        return None
    if len(sections) == 1:
        return sections[0]
    dialog = Gtk.Dialog(title="Open Linked Section", transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Open", Gtk.ResponseType.OK)
    combo = Gtk.ComboBoxText()
    for target in sections:
        combo.append(target, target)
    combo.set_active(0)
    combo.set_margin_start(12)
    combo.set_margin_end(12)
    combo.set_margin_top(12)
    combo.set_margin_bottom(12)
    dialog.get_content_area().pack_start(combo, False, False, 0)
    dialog.show_all()
    result = combo.get_active_id() if run_modal(dialog) == Gtk.ResponseType.OK else None
    destroy_modal(dialog)
    return result
