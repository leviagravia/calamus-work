"""GTK selection and impact preview for symmetric Related References."""
from __future__ import annotations

from calamus_related_references import (
    RelatedReferencePlan,
    effective_related_keys,
    plan_related_references_update,
)
from calamus_references import ReferenceRecord

from calamus_modal_dialog import destroy_modal, run_modal


def _gtk():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    return Gtk


def _glib():
    from gi.repository import GLib
    return GLib

def run_related_references_dialog(
    parent,
    records: tuple[ReferenceRecord, ...],
    subject_key: str,
) -> RelatedReferencePlan | None:
    Gtk = _gtk()

    subject = next((record for record in records if record.key == subject_key), None)
    if subject is None:
        return None
    dialog = Gtk.Dialog(
        title=f"Related References — {subject.key}",
        transient_for=parent,
        modal=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Review Impact", Gtk.ResponseType.OK)
    dialog.set_default_size(680, 620)

    area = dialog.get_content_area()
    area.set_spacing(8)
    area.set_margin_start(12); area.set_margin_end(12)
    area.set_margin_top(12); area.set_margin_bottom(12)

    heading = Gtk.Label()
    heading.set_xalign(0)
    heading.set_markup(f"<b>{_escape(subject.author_year)} — {_escape(subject.title)}</b>")
    area.pack_start(heading, False, False, 0)

    explanation = Gtk.Label(
        label=(
            "Select the References that are explicitly related to this record. "
            "Calamus writes canonical primary keys and updates both sides of every relation in one atomic references.md save."
        )
    )
    explanation.set_xalign(0); explanation.set_line_wrap(True)
    area.pack_start(explanation, False, False, 0)

    search = Gtk.SearchEntry()
    search.set_placeholder_text("Filter References…")
    area.pack_start(search, False, False, 0)

    current = set(effective_related_keys(records, subject.key))
    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.NONE)
    checks: dict[str, object] = {}
    by_key = {record.key: record for record in records}
    for record in records:
        if record.key == subject.key:
            continue
        row = Gtk.ListBoxRow()
        row.reference_key = record.key
        check = Gtk.CheckButton(
            label=f"{record.key} — {record.author_year} — {record.title}"
        )
        check.set_name(f"related-reference-{record.key}")
        check.set_active(record.key in current)
        check.set_margin_start(4); check.set_margin_end(4)
        check.set_margin_top(3); check.set_margin_bottom(3)
        row.add(check)
        listbox.add(row)
        checks[record.key] = check

    def filter_row(row):
        needle = search.get_text().strip().casefold()
        if not needle:
            return True
        record = by_key[row.reference_key]
        return needle in record.search_text

    listbox.set_filter_func(filter_row)
    search.connect("search-changed", lambda *_: listbox.invalidate_filter())
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)
    scroll.add(listbox)
    area.pack_start(scroll, True, True, 0)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()
    result = None
    while True:
        response = run_modal(dialog)
        if response != Gtk.ResponseType.OK:
            break
        requested = tuple(key for key, check in checks.items() if check.get_active())
        try:
            plan = plan_related_references_update(records, subject.key, requested)
        except (TypeError, ValueError) as error:
            _message(dialog, "Cannot plan Related References", str(error), error=True)
            continue
        if not plan.changed:
            _message(dialog, "No changes", "The Related References selection is unchanged.", error=False)
            break
        if confirm_related_references_impact(dialog, plan):
            result = plan
            break
    destroy_modal(dialog)
    return result


def confirm_related_references_impact(parent, plan: RelatedReferencePlan) -> bool:
    Gtk = _gtk()
    dialog = Gtk.MessageDialog(
        title="Related References Impact",
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text=f"Apply Related References for {plan.subject_key}?",
    )
    added = ", ".join(plan.added) or "none"
    removed = ", ".join(plan.removed) or "none"
    dialog.format_secondary_text(
        "\n".join((
            f"Add: {added}",
            f"Remove: {removed}",
            f"Reference records updated: {len(plan.changed_record_keys)}",
            "",
            "Both sides of each relation will be written together. External changes cancel the operation.",
        ))
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Apply", Gtk.ResponseType.OK)
    response = run_modal(dialog)
    destroy_modal(dialog)
    return response == Gtk.ResponseType.OK


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


def _escape(value: str) -> str:
    GLib = _glib()
    return GLib.markup_escape_text(value or "")
