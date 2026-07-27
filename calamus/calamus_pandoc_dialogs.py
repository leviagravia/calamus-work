"""Owned GTK 3 dialogs for the W90 Pandoc/citeproc handoff."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from calamus_modal_dialog import ModalSession
from calamus_pandoc import (
    PRODUCT_BIBLIOGRAPHY,
    PRODUCT_DOCUMENT,
    SCOPE_ALL,
    SCOPE_CITED,
    SCOPE_REFERENCE_SET,
    default_format,
    pandoc_format,
    pandoc_formats,
    product_title,
    scope_title,
    suggested_output_name,
)
from calamus_pandoc_controller import (
    PandocExportPlan,
    PandocExportResult,
    PandocPreviewResult,
)


@dataclass(frozen=True)
class PandocOptionsWidgets:
    dialog: Gtk.Dialog
    product_combo: Gtk.ComboBoxText
    scope_combo: Gtk.ComboBoxText
    set_combo: Gtk.ComboBoxText
    format_combo: Gtk.ComboBoxText
    csl_chooser: Gtk.FileChooserButton
    csl_default_button: Gtk.Button
    continue_button: Gtk.Widget


@dataclass(frozen=True)
class PandocPreviewWidgets:
    dialog: Gtk.Dialog
    summary_view: Gtk.TextView
    preview_view: Gtk.TextView


@dataclass(frozen=True)
class PandocProgressWidgets:
    dialog: Gtk.Dialog
    spinner: Gtk.Spinner
    status_label: Gtk.Label


def _named(widget, name: str):
    widget.set_name(name)
    return widget


def build_pandoc_options_dialog(
    parent,
    reference_set_names: tuple[str, ...],
) -> PandocOptionsWidgets:
    dialog = Gtk.Dialog(
        title="Export with Pandoc/citeproc",
        transient_for=parent,
        modal=True,
        destroy_with_parent=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    continue_button = dialog.add_button("Choose Destination…", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_default_size(620, 420)
    content = dialog.get_content_area()
    content.set_border_width(12)
    content.set_spacing(10)

    intro = Gtk.Label(
        label=(
            "Pandoc is an optional external processor. Calamus sends it a derived "
            "BibLaTeX projection; references.md and the document remain authoritative."
        )
    )
    intro.set_xalign(0)
    intro.set_line_wrap(True)
    content.pack_start(intro, False, False, 0)

    grid = Gtk.Grid(column_spacing=12, row_spacing=10)
    grid.set_hexpand(True)
    content.pack_start(grid, False, False, 0)

    def label(text: str, row: int):
        item = Gtk.Label(label=text)
        item.set_xalign(0)
        grid.attach(item, 0, row, 1, 1)

    product_combo = _named(Gtk.ComboBoxText(), "calamus-pandoc-product")
    product_combo.append(PRODUCT_DOCUMENT, product_title(PRODUCT_DOCUMENT))
    product_combo.append(PRODUCT_BIBLIOGRAPHY, product_title(PRODUCT_BIBLIOGRAPHY))
    product_combo.set_active_id(PRODUCT_DOCUMENT)
    label("Product:", 0)
    grid.attach(product_combo, 1, 0, 1, 1)

    scope_combo = _named(Gtk.ComboBoxText(), "calamus-pandoc-scope")
    for scope in (SCOPE_CITED, SCOPE_ALL, SCOPE_REFERENCE_SET):
        scope_combo.append(scope, scope_title(scope))
    scope_combo.set_active_id(SCOPE_CITED)
    label("Reference scope:", 1)
    grid.attach(scope_combo, 1, 1, 1, 1)

    set_combo = _named(Gtk.ComboBoxText(), "calamus-pandoc-reference-set")
    for name in reference_set_names:
        set_combo.append(name, name)
    if reference_set_names:
        set_combo.set_active(0)
    set_combo.set_sensitive(False)
    label("Reference Set:", 2)
    grid.attach(set_combo, 1, 2, 1, 1)

    format_combo = _named(Gtk.ComboBoxText(), "calamus-pandoc-format")
    label("Output format:", 3)
    grid.attach(format_combo, 1, 3, 1, 1)

    csl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    csl_chooser = _named(
        Gtk.FileChooserButton(
            title="Choose a local CSL style",
            action=Gtk.FileChooserAction.OPEN,
        ),
        "calamus-pandoc-csl",
    )
    csl_chooser.set_local_only(True)
    csl_filter = Gtk.FileFilter()
    csl_filter.set_name("Citation Style Language (*.csl)")
    csl_filter.add_pattern("*.csl")
    csl_chooser.add_filter(csl_filter)
    csl_chooser.set_filter(csl_filter)
    csl_default_button = _named(Gtk.Button(label="Use Pandoc Default"), "calamus-pandoc-csl-default")
    csl_box.pack_start(csl_chooser, True, True, 0)
    csl_box.pack_start(csl_default_button, False, False, 0)
    label("Citation style:", 4)
    grid.attach(csl_box, 1, 4, 1, 1)

    note = Gtk.Label(
        label=(
            "Reference Set names are case-sensitive. PDF, templates, filters, custom "
            "arguments and persistent export profiles are outside W90."
        )
    )
    note.set_xalign(0)
    note.set_line_wrap(True)
    content.pack_start(note, False, False, 0)

    def repopulate_formats(*_):
        product = product_combo.get_active_id() or PRODUCT_DOCUMENT
        format_combo.remove_all()
        for descriptor in pandoc_formats(product):
            format_combo.append(descriptor.id, f"{descriptor.label} ({descriptor.extension})")
        format_combo.set_active_id(default_format(product))

    def update_set_state(*_):
        uses_set = scope_combo.get_active_id() == SCOPE_REFERENCE_SET
        set_combo.set_sensitive(uses_set)
        continue_button.set_sensitive(not uses_set or bool(reference_set_names))

    product_combo.connect("changed", repopulate_formats)
    scope_combo.connect("changed", update_set_state)
    csl_default_button.connect("clicked", lambda *_: csl_chooser.unselect_all())
    repopulate_formats()
    update_set_state()
    dialog.show_all()
    set_combo.set_sensitive(False)
    widgets = PandocOptionsWidgets(
        dialog,
        product_combo,
        scope_combo,
        set_combo,
        format_combo,
        csl_chooser,
        csl_default_button,
        continue_button,
    )
    dialog._calamus_pandoc_options_widgets = widgets
    return widgets


def run_pandoc_options_dialog(parent, reference_set_names: tuple[str, ...]):
    widgets = build_pandoc_options_dialog(parent, reference_set_names)
    with ModalSession(widgets.dialog) as session:
        response = session.run()
        if response != Gtk.ResponseType.OK:
            return None
        # Copy the semantic result while the owned widgets still exist.  The
        # session has hidden the window and destroys it only on context exit.
        product = widgets.product_combo.get_active_id()
        scope = widgets.scope_combo.get_active_id()
        format_id = widgets.format_combo.get_active_id()
        set_name = widgets.set_combo.get_active_id() if scope == SCOPE_REFERENCE_SET else ""
        csl_path = widgets.csl_chooser.get_filename() or ""
        if not product or not scope or not format_id:
            return None
        return product, scope, format_id, set_name or "", csl_path


def build_pandoc_destination_dialog(parent, document_path, product: str, format_id: str):
    descriptor = pandoc_format(product, format_id)
    dialog = Gtk.FileChooserDialog(
        title=f"Export {product_title(product)}",
        transient_for=parent,
        action=Gtk.FileChooserAction.SAVE,
    )
    dialog.set_modal(True)
    dialog.set_destroy_with_parent(True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Prepare Preview", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_local_only(True)
    dialog.set_select_multiple(False)
    dialog.set_create_folders(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(f"{descriptor.label} (*{descriptor.extension})")
    file_filter.add_pattern(f"*{descriptor.extension}")
    dialog.add_filter(file_filter)
    dialog.set_filter(file_filter)
    dialog.set_current_name(suggested_output_name(document_path, product, format_id))
    if isinstance(document_path, str) and document_path:
        folder = os.path.dirname(os.path.abspath(document_path))
        if os.path.isdir(folder):
            dialog.set_current_folder(folder)
    return dialog


def run_pandoc_destination_dialog(parent, document_path, product: str, format_id: str) -> str | None:
    descriptor = pandoc_format(product, format_id)
    dialog = build_pandoc_destination_dialog(parent, document_path, product, format_id)
    with ModalSession(dialog) as session:
        response = session.run()
        filename = dialog.get_filename() if response == Gtk.ResponseType.OK else None
    if not filename:
        return None
    if Path(filename).suffix.casefold() != descriptor.extension:
        filename += descriptor.extension
    return filename


def build_pandoc_preview_dialog(
    parent,
    plan: PandocExportPlan,
    preview: PandocPreviewResult,
) -> PandocPreviewWidgets:
    dialog = Gtk.Dialog(
        title="Pandoc/citeproc — Semantic Preview",
        transient_for=parent,
        modal=True,
        destroy_with_parent=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Export", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_default_size(880, 680)
    content = dialog.get_content_area()
    content.set_border_width(10)
    content.set_spacing(8)

    heading = Gtk.Label(
        label=(
            "This plain-text preview is produced by citeproc from the exact frozen plan. "
            "It is semantic, not a visual preview of the selected output format."
        )
    )
    heading.set_xalign(0)
    heading.set_line_wrap(True)
    content.pack_start(heading, False, False, 0)

    summary_view = _named(Gtk.TextView(), "calamus-pandoc-preview-summary")
    summary_view.set_editable(False)
    summary_view.set_cursor_visible(False)
    summary_view.set_monospace(True)
    summary_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    summary_view.get_buffer().set_text(preview.message)
    summary_scroll = Gtk.ScrolledWindow()
    summary_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    summary_scroll.set_min_content_height(190)
    summary_scroll.add(summary_view)
    content.pack_start(summary_scroll, False, True, 0)

    preview_view = _named(Gtk.TextView(), "calamus-pandoc-preview-text")
    preview_view.set_editable(False)
    preview_view.set_cursor_visible(False)
    preview_view.set_monospace(True)
    preview_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    preview_view.get_buffer().set_text(preview.text)
    preview_scroll = Gtk.ScrolledWindow()
    preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    preview_scroll.add(preview_view)
    content.pack_start(preview_scroll, True, True, 0)
    dialog.show_all()
    widgets = PandocPreviewWidgets(dialog, summary_view, preview_view)
    dialog._calamus_pandoc_preview_widgets = widgets
    return widgets


def run_pandoc_preview_dialog(parent, plan: PandocExportPlan, preview: PandocPreviewResult) -> bool:
    widgets = build_pandoc_preview_dialog(parent, plan, preview)
    with ModalSession(widgets.dialog) as session:
        return session.run() == Gtk.ResponseType.OK


def build_pandoc_progress_dialog(parent, title: str) -> PandocProgressWidgets:
    dialog = Gtk.Dialog(
        title=title,
        transient_for=parent,
        modal=True,
        destroy_with_parent=True,
    )
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.set_deletable(False)
    content = dialog.get_content_area()
    content.set_border_width(18)
    content.set_spacing(12)
    spinner = _named(Gtk.Spinner(), "calamus-pandoc-progress-spinner")
    spinner.start()
    status_label = _named(Gtk.Label(label=title), "calamus-pandoc-progress-status")
    status_label.set_xalign(0.5)
    content.pack_start(spinner, False, False, 0)
    content.pack_start(status_label, False, False, 0)
    dialog.show_all()
    widgets = PandocProgressWidgets(dialog, spinner, status_label)
    dialog._calamus_pandoc_progress_widgets = widgets
    return widgets


def show_pandoc_error(parent, message: str) -> None:
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        destroy_with_parent=True,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text="Pandoc/citeproc export failed",
    )
    dialog.format_secondary_text(message)
    with ModalSession(dialog) as session:
        session.run()


def show_pandoc_result(parent, result: PandocExportResult) -> None:
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        destroy_with_parent=True,
        message_type=Gtk.MessageType.INFO if result.succeeded else Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text="Pandoc/citeproc export complete" if result.succeeded else "Pandoc/citeproc export failed",
    )
    detail = result.message + (f"\n\n{result.path}" if result.path else "")
    dialog.format_secondary_text(detail)
    with ModalSession(dialog) as session:
        session.run()
