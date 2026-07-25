"""GTK import-decision view for BibTeX/BibLaTeX.

The view projects a GTK-free :class:`BibImportSession`.  Selection only changes
which static decision controls are shown; each action writes directly to the
selected session item and its known display row.  No model scan or dynamic
combo-box rebuilding is used.
"""
from __future__ import annotations

from dataclasses import dataclass

from gi.repository import Gtk

from calamus_bibtex import (
    ACTION_IMPORT,
    ACTION_MERGE,
    ACTION_NEW_KEY,
    ACTION_REPLACE,
    ACTION_SKIP,
    BibImportDecision,
    BibImportPreview,
)
from calamus_bibtex_import_session import BibImportSession
from calamus_references import ReferenceRecord

_ACTION_LABELS = {
    ACTION_IMPORT: "Import",
    ACTION_SKIP: "Skip",
    ACTION_REPLACE: "Replace existing",
    ACTION_MERGE: "Merge missing fields",
    ACTION_NEW_KEY: "Import with new key",
}


@dataclass(frozen=True)
class BibImportPreviewWidgets:
    dialog: Gtk.Dialog
    tree: Gtk.TreeView
    store: Gtk.ListStore
    action_buttons: dict[str, Gtk.RadioButton]
    diagnostics: Gtk.TextView
    session: BibImportSession
    current_summary: Gtk.Label
    incoming_summary: Gtk.Label
    unresolved_label: Gtk.Label
    review_button: Gtk.Button


def _diagnostic_text(preview: BibImportPreview) -> str:
    lines = [
        f"Entries: {len(preview.items)}",
        f"@string blocks consumed: {preview.strings}",
        f"Comments not imported: {preview.comments}",
        f"Preambles not imported: {preview.preambles}",
    ]
    if preview.diagnostics:
        lines.extend(("", "Diagnostics:"))
        for item in preview.diagnostics:
            severity = "BLOCKING" if item.blocking else "warning"
            lines.append(f"Line {item.line}: [{severity}] {item.message}")
    else:
        lines.extend(("", "No parser or mapping diagnostics."))
    return "\n".join(lines)


def _record_summary(record: ReferenceRecord | None, *, missing: str) -> str:
    if record is None:
        return missing
    values = [
        f"Key: {record.key}",
        f"Type: {record.type}",
        f"Title: {record.title}",
        f"Author: {record.primary_author or '—'}",
        f"Year/date: {record.year or '—'}",
    ]
    if record.doi:
        values.append(f"DOI: {record.doi}")
    if record.isbn:
        values.append(f"ISBN: {record.isbn}")
    if record.url:
        values.append(f"URL: {record.url}")
    return "\n".join(values)


def _summary_box(title: str) -> tuple[Gtk.Frame, Gtk.Label]:
    frame = Gtk.Frame(label=title)
    label = Gtk.Label()
    label.set_xalign(0)
    label.set_yalign(0)
    label.set_selectable(True)
    label.set_line_wrap(True)
    label.set_margin_start(8)
    label.set_margin_end(8)
    label.set_margin_top(8)
    label.set_margin_bottom(8)
    frame.add(label)
    return frame, label


def build_bib_import_preview_dialog(
    parent,
    preview: BibImportPreview,
) -> BibImportPreviewWidgets:
    session = BibImportSession(preview)
    dialog = Gtk.Dialog(
        title="Import BibTeX/BibLaTeX — Review Entries",
        transient_for=parent,
        modal=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Review Impact…", Gtk.ResponseType.OK)
    dialog.set_default_size(980, 680)
    review_button = dialog.get_widget_for_response(Gtk.ResponseType.OK)

    content = dialog.get_content_area()
    content.set_spacing(8)
    content.set_border_width(10)

    heading = Gtk.Label()
    heading.set_markup(
        "<b>Review entries, then make an explicit decision for each collision</b>"
    )
    heading.set_xalign(0)
    content.pack_start(heading, False, False, 0)

    unresolved_label = Gtk.Label()
    unresolved_label.set_xalign(0)
    unresolved_label.set_line_wrap(True)
    content.pack_start(unresolved_label, False, False, 0)

    store = Gtk.ListStore(int, str, str, str, str, str)
    row_number_by_index: dict[int, int] = {}
    for row_number, row in enumerate(session.rows()):
        item = row.item
        row_number_by_index[item.index] = row_number
        store.append((
            item.index,
            item.source_key,
            item.record.type if item.record else "invalid",
            item.record.title if item.record else "",
            item.status,
            _ACTION_LABELS.get(row.action, "Choose action…"),
        ))

    tree = Gtk.TreeView(model=store)
    tree.set_headers_visible(True)
    tree.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
    for title, column, width in (
        ("Key", 1, 140),
        ("Type", 2, 130),
        ("Title", 3, 260),
        ("Status", 4, 250),
        ("Decision", 5, 180),
    ):
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", 3)
        view_column = Gtk.TreeViewColumn(title, renderer, text=column)
        view_column.set_min_width(width)
        view_column.set_resizable(True)
        tree.append_column(view_column)

    tree_scroll = Gtk.ScrolledWindow()
    tree_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    tree_scroll.add(tree)

    details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    details.set_size_request(360, -1)
    detail_heading = Gtk.Label()
    detail_heading.set_markup("<b>Decision for selected entry</b>")
    detail_heading.set_xalign(0)
    details.pack_start(detail_heading, False, False, 0)

    current_frame, current_summary = _summary_box("Current local reference")
    incoming_frame, incoming_summary = _summary_box("Incoming reference")
    summaries = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
    summaries.pack1(current_frame, True, False)
    summaries.pack2(incoming_frame, True, False)
    summaries.set_position(150)
    details.pack_start(summaries, True, True, 0)

    actions_frame = Gtk.Frame(label="Choose one action")
    actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    actions_box.set_border_width(8)
    actions_frame.add(actions_box)
    hidden_unresolved = Gtk.RadioButton.new_with_label(None, "Unresolved")
    hidden_unresolved.set_no_show_all(True)
    hidden_unresolved.hide()
    action_buttons: dict[str, Gtk.RadioButton] = {}
    group = hidden_unresolved
    for action in (
        ACTION_IMPORT,
        ACTION_SKIP,
        ACTION_REPLACE,
        ACTION_MERGE,
        ACTION_NEW_KEY,
    ):
        button = Gtk.RadioButton.new_with_label_from_widget(group, _ACTION_LABELS[action])
        action_buttons[action] = button
        actions_box.pack_start(button, False, False, 0)
    details.pack_start(actions_frame, False, False, 0)

    main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
    main_paned.pack1(tree_scroll, True, False)
    main_paned.pack2(details, False, False)
    main_paned.set_position(610)
    content.pack_start(main_paned, True, True, 0)

    diagnostics = Gtk.TextView()
    diagnostics.set_editable(False)
    diagnostics.set_cursor_visible(False)
    diagnostics.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    diagnostics.get_buffer().set_text(_diagnostic_text(preview))
    diagnostics_scroll = Gtk.ScrolledWindow()
    diagnostics_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    diagnostics_scroll.set_size_request(-1, 145)
    diagnostics_scroll.add(diagnostics)
    notebook = Gtk.Notebook()
    notebook.append_page(
        diagnostics_scroll,
        Gtk.Label(label="Diagnostics and non-entry blocks"),
    )
    content.pack_start(notebook, False, True, 0)

    selected_index: int | None = None
    synchronizing = False

    def refresh_gate() -> None:
        count = session.unresolved_count
        if count:
            noun = "collision requires" if count == 1 else "collisions require"
            unresolved_label.set_text(
                f"{count} {noun} an explicit decision before impact review."
            )
        else:
            unresolved_label.set_text(
                "All entries have a decision. Review the exact impact before applying."
            )
        review_button.set_sensitive(session.can_review)

    def sync_selection(index: int | None) -> None:
        nonlocal selected_index, synchronizing
        selected_index = index
        synchronizing = True
        try:
            if index is None:
                current_summary.set_text("No entry selected.")
                incoming_summary.set_text("No entry selected.")
                hidden_unresolved.set_active(True)
                for button in action_buttons.values():
                    button.set_sensitive(False)
                return
            item = session.item(index)
            current_summary.set_text(_record_summary(
                item.existing_record,
                missing="No matched local reference.",
            ))
            incoming_summary.set_text(_record_summary(
                item.record,
                missing="This entry is invalid and cannot be imported.",
            ))
            action = session.action(index)
            if action is None:
                hidden_unresolved.set_active(True)
            else:
                action_buttons[action].set_active(True)
            for name, button in action_buttons.items():
                button.set_sensitive(item.record is not None and name in item.allowed_actions)
        finally:
            synchronizing = False

    def on_selection(selection) -> None:
        model, tree_iter = selection.get_selected()
        sync_selection(None if tree_iter is None else model.get_value(tree_iter, 0))

    def on_action_toggled(button, action: str) -> None:
        if synchronizing or not button.get_active() or selected_index is None:
            return
        row = session.set_action(selected_index, action)
        row_number = row_number_by_index[selected_index]
        store[row_number][5] = _ACTION_LABELS[row.action]
        refresh_gate()

    tree.get_selection().connect("changed", on_selection)
    for action, button in action_buttons.items():
        button.connect("toggled", on_action_toggled, action)

    refresh_gate()
    dialog.show_all()
    hidden_unresolved.hide()
    if len(store):
        tree.get_selection().select_path(Gtk.TreePath.new_from_string("0"))

    widgets = BibImportPreviewWidgets(
        dialog=dialog,
        tree=tree,
        store=store,
        action_buttons=action_buttons,
        diagnostics=diagnostics,
        session=session,
        current_summary=current_summary,
        incoming_summary=incoming_summary,
        unresolved_label=unresolved_label,
        review_button=review_button,
    )
    dialog._calamus_bib_import_widgets = widgets
    return widgets


def run_bib_import_preview_dialog(
    parent,
    preview: BibImportPreview,
) -> tuple[BibImportDecision, ...] | None:
    widgets = build_bib_import_preview_dialog(parent, preview)
    response = widgets.dialog.run()
    decisions = widgets.session.decisions() if response == Gtk.ResponseType.OK else None
    widgets.dialog.destroy()
    return decisions
