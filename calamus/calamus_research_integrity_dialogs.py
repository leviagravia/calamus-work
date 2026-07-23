"""GTK dialogs for controlled reference-key migration and Research Check."""
from __future__ import annotations

from calamus_reference_integrity import ReferenceMigrationPlan, ResearchCheckReport
from calamus_references import ReferenceRecord, is_valid_reference_key
from calamus_research_integrity_controller import IntegrityCommandResult


def run_reference_key_rename_dialog(
    parent,
    records: tuple[ReferenceRecord, ...],
    *,
    initial_key: str | None = None,
) -> tuple[str, str, bool] | None:
    from gi.repository import Gtk

    if not records:
        return None
    dialog = Gtk.Dialog(
        title="Rename Reference Key",
        transient_for=parent,
        modal=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Preview Impact", Gtk.ResponseType.OK)
    dialog.set_default_size(520, -1)

    grid = Gtk.Grid(column_spacing=10, row_spacing=10)
    grid.set_border_width(12)
    dialog.get_content_area().pack_start(grid, True, True, 0)

    current_label = Gtk.Label(label="Reference")
    current_label.set_xalign(0)
    current = Gtk.ComboBoxText()
    active = 0
    for index, record in enumerate(records):
        current.append(record.key, f"{record.key} — {record.author_year} — {record.title}")
        if record.key == initial_key:
            active = index
    current.set_active(active)

    new_label = Gtk.Label(label="New key")
    new_label.set_xalign(0)
    new_entry = Gtk.Entry()
    new_entry.set_activates_default(True)

    preserve = Gtk.CheckButton(label="Preserve the old key as an alias")
    preserve.set_active(True)
    preserve.set_tooltip_text("Keeps old citations resolvable until they are migrated.")

    note = Gtk.Label(
        label=(
            "Calamus will scan the active document, the current Source Notes sidecar "
            "and related-key fields before writing anything."
        )
    )
    note.set_xalign(0)
    note.set_line_wrap(True)

    grid.attach(current_label, 0, 0, 1, 1)
    grid.attach(current, 1, 0, 1, 1)
    grid.attach(new_label, 0, 1, 1, 1)
    grid.attach(new_entry, 1, 1, 1, 1)
    grid.attach(preserve, 1, 2, 1, 1)
    grid.attach(note, 0, 3, 2, 1)

    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()
    result = None
    while True:
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            break
        old_key = current.get_active_id() or ""
        new_key = new_entry.get_text().strip()
        if not is_valid_reference_key(new_key):
            _message(dialog, "Invalid reference key", "Use letters, digits, dot, underscore, colon or hyphen.", error=True)
            continue
        if new_key == old_key:
            _message(dialog, "No key change", "The new key must differ from the current key.", error=True)
            continue
        result = (old_key, new_key, preserve.get_active())
        break
    dialog.destroy()
    return result


def confirm_reference_migration(parent, plan: ReferenceMigrationPlan) -> bool:
    from gi.repository import Gtk

    impact = plan.impact
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text=f"Rename {impact.old_key} to {impact.new_key}?",
    )
    lines = [
        f"Active-document citation occurrences: {impact.citation_occurrences}",
        f"Current Source Notes occurrences: {impact.source_note_occurrences}",
        f"Related-key occurrences: {impact.related_key_occurrences}",
        "Old key preserved as alias: " + ("yes" if impact.preserved_alias else "no"),
        "",
        "The operation will be cancelled if any source changes after this preview.",
    ]
    dialog.format_secondary_text("\n".join(lines))
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Rename Key", Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def show_research_check_report(parent, report: ResearchCheckReport) -> None:
    from gi.repository import Gtk, Pango

    dialog = Gtk.Dialog(title="Research Check", transient_for=parent, modal=True)
    dialog.add_button("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(760, 560)

    summary = Gtk.Label()
    summary.set_xalign(0)
    summary.set_margin_start(10)
    summary.set_margin_end(10)
    summary.set_margin_top(10)
    summary.set_margin_bottom(6)
    summary.set_text(
        f"{report.reference_count} references · {report.citation_count} citations · "
        f"{report.source_note_count} source notes · "
        f"{report.error_count} errors · {report.warning_count} warnings · "
        f"{report.advisory_count} advisories"
    )

    view = Gtk.TextView()
    view.set_editable(False)
    view.set_cursor_visible(False)
    view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    view.modify_font(Pango.FontDescription("Monospace 10"))
    if report.clean:
        text = "Research Check found no issues in the active document and current sidecar."
    else:
        labels = {"error": "ERROR", "warning": "WARNING", "advisory": "ADVISORY"}
        text = "\n\n".join(
            f"[{labels[issue.severity]}] {issue.kind} — {issue.subject}\n{issue.message}"
            for issue in report.issues
        )
    view.get_buffer().set_text(text)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(view)
    area = dialog.get_content_area()
    area.pack_start(summary, False, False, 0)
    area.pack_start(scroll, True, True, 0)
    dialog.show_all()
    dialog.run()
    dialog.destroy()


def show_integrity_result(parent, result: IntegrityCommandResult) -> None:
    if result.succeeded:
        _message(parent, "Reference key renamed", result.message, error=False)
        return
    detail = result.message
    if result.recovery_errors:
        detail += "\n\nManual recovery required:\n- " + "\n- ".join(result.recovery_errors)
    title = {
        "stale": "Migration cancelled safely",
        "recovery-required": "Migration needs manual recovery",
    }.get(result.status, "Reference-key migration failed")
    _message(parent, title, detail, error=True)


def show_integrity_error(parent, title: str, message: str) -> None:
    _message(parent, title, message, error=True)


def _message(parent, title: str, detail: str, *, error: bool) -> None:
    from gi.repository import Gtk

    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(detail)
    dialog.run()
    dialog.destroy()
