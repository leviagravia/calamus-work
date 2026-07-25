"""GTK dialogs for choosing one W85 Research export and its destination.

The product choice is an ordinary ``Gtk.Dialog``.  The destination is a
separate, standard ``Gtk.FileChooserDialog``.  Keeping these surfaces separate
avoids depending on file-chooser extra-widget presentation, which varies across
GTK integrations and was the cause of the retired W85 candidates.
"""
from __future__ import annotations

import os
from pathlib import Path

from gi.repository import Gtk

from calamus_research_export import (
    ANNOTATED_BIBLIOGRAPHY,
    CITED_BIBLIOGRAPHY,
    FULL_RESEARCH_DOSSIER,
    NOTES_BY_REFERENCE,
    NOTES_DOCUMENT_ORDER,
    research_export_kinds,
    research_export_suffix,
    research_export_title,
)


def suggested_research_export_name(document_path: str, kind: str) -> str:
    stem = Path(document_path).stem if isinstance(document_path, str) else "document"
    stem = stem.strip() or "document"
    return f"{stem}-{research_export_suffix(kind)}.md"


def build_research_export_product_dialog(parent):
    """Build the visible product-selection dialog used before Save As."""
    dialog = Gtk.Dialog(
        title="Export Research Apparatus",
        transient_for=parent,
        modal=True,
    )
    dialog.add_buttons(
        Gtk.STOCK_CANCEL,
        Gtk.ResponseType.CANCEL,
        "Choose Destination…",
        Gtk.ResponseType.OK,
    )
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_resizable(False)

    content = dialog.get_content_area()
    content.set_spacing(10)
    for setter in (
        content.set_margin_start,
        content.set_margin_end,
        content.set_margin_top,
        content.set_margin_bottom,
    ):
        setter(12)

    heading = Gtk.Label()
    heading.set_markup("<b>Choose the Research apparatus to export</b>")
    heading.set_xalign(0)
    content.pack_start(heading, False, False, 0)

    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    label = Gtk.Label(label="Export product:")
    label.set_xalign(0)
    chooser = Gtk.ComboBoxText()
    chooser.set_hexpand(True)
    for kind in research_export_kinds():
        chooser.append(kind, research_export_title(kind))
    chooser.set_active_id(FULL_RESEARCH_DOSSIER)
    label.set_mnemonic_widget(chooser)
    row.pack_start(label, False, False, 0)
    row.pack_start(chooser, True, True, 0)
    content.pack_start(row, False, False, 0)

    explanation = Gtk.Label(
        label=(
            "The next window chooses the local Markdown destination. The export "
            "is derived and does not modify the document, references.md, or the "
            "document-specific Source Notes sidecar."
        )
    )
    explanation.set_xalign(0)
    explanation.set_line_wrap(True)
    explanation.set_max_width_chars(64)
    content.pack_start(explanation, False, False, 0)

    dialog.show_all()
    return dialog, chooser


def run_research_export_product_dialog(parent) -> str | None:
    dialog, chooser = build_research_export_product_dialog(parent)
    response = dialog.run()
    selected = None
    if response == Gtk.ResponseType.OK:
        candidate = chooser.get_active_id()
        if candidate in research_export_kinds():
            selected = candidate
    dialog.destroy()
    return selected


def build_research_export_destination_dialog(parent, document_path: str, kind: str):
    """Build the standard local Save As chooser for one already-chosen product."""
    if kind not in research_export_kinds():
        raise ValueError("Unknown Research export product")

    dialog = Gtk.FileChooserDialog(
        title=f"Export {research_export_title(kind)}",
        action=Gtk.FileChooserAction.SAVE,
    )
    if parent is not None:
        dialog.set_transient_for(parent)
    dialog.set_modal(True)
    dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    dialog.add_button("Export", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_local_only(True)
    dialog.set_select_multiple(False)
    dialog.set_create_folders(False)

    markdown_filter = Gtk.FileFilter()
    markdown_filter.set_name("Markdown (*.md)")
    markdown_filter.add_pattern("*.md")
    dialog.add_filter(markdown_filter)
    dialog.set_filter(markdown_filter)

    if isinstance(document_path, str) and document_path:
        folder = os.path.dirname(os.path.abspath(document_path))
        if os.path.isdir(folder):
            dialog.set_current_folder(folder)
    dialog.set_current_name(suggested_research_export_name(document_path, kind))
    return dialog


def run_research_export_destination_dialog(
    parent,
    document_path: str,
    kind: str,
) -> str | None:
    dialog = build_research_export_destination_dialog(parent, document_path, kind)
    response = dialog.run()
    filename = dialog.get_filename() if response == Gtk.ResponseType.OK else None
    dialog.destroy()
    if not filename:
        return None
    if Path(filename).suffix.casefold() != ".md":
        filename += ".md"
    return filename


def run_research_export_dialog(parent, document_path: str):
    """Choose product first, destination second, returning one export request."""
    kind = run_research_export_product_dialog(parent)
    if kind is None:
        return None
    filename = run_research_export_destination_dialog(parent, document_path, kind)
    if filename is None:
        return None
    return kind, filename
