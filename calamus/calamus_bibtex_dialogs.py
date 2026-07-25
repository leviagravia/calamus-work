"""GTK dialogs for W87 BibTeX/BibLaTeX import and export."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from gi.repository import Gtk

from calamus_bibtex import BIBLATEX, BIBTEX, BibExportArtifact
from calamus_bibtex_controller import BibImportPlan, BibImportResult, BibExportResult
from calamus_bibtex_import_view import (
    BibImportPreviewWidgets,
    build_bib_import_preview_dialog,
    run_bib_import_preview_dialog,
)

@dataclass(frozen=True)
class BibExportPreviewWidgets:
    dialog: Gtk.Dialog
    text_view: Gtk.TextView
    warning_label: Gtk.Label
    artifact: BibExportArtifact


def run_bib_file_dialog(parent) -> str | None:
    dialog = Gtk.FileChooserDialog(
        title="Import BibTeX/BibLaTeX",
        transient_for=parent,
        action=Gtk.FileChooserAction.OPEN,
    )
    dialog.set_modal(True)
    dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    dialog.add_button("Open", Gtk.ResponseType.OK)
    dialog.set_local_only(True)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name("BibTeX/BibLaTeX (*.bib)")
    file_filter.add_pattern("*.bib")
    dialog.add_filter(file_filter)
    dialog.set_filter(file_filter)
    response = dialog.run()
    filename = dialog.get_filename() if response == Gtk.ResponseType.OK else None
    dialog.destroy()
    return filename


def build_bib_format_dialog(parent, *, title: str, suggested: str = BIBLATEX):
    dialog = Gtk.Dialog(title=title, transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Continue", Gtk.ResponseType.OK)
    content = dialog.get_content_area()
    content.set_spacing(10)
    content.set_border_width(12)
    label = Gtk.Label(label="Bibliography format:")
    label.set_xalign(0)
    combo = Gtk.ComboBoxText()
    combo.append(BIBLATEX, "BibLaTeX")
    combo.append(BIBTEX, "BibTeX")
    combo.set_active_id(suggested if suggested in (BIBLATEX, BIBTEX) else BIBLATEX)
    explanation = Gtk.Label(
        label=(
            "Choose explicitly. Calamus does not silently reinterpret BibTeX and "
            "BibLaTeX field semantics."
        )
    )
    explanation.set_xalign(0)
    explanation.set_line_wrap(True)
    content.pack_start(label, False, False, 0)
    content.pack_start(combo, False, False, 0)
    content.pack_start(explanation, False, False, 0)
    dialog.show_all()
    return dialog, combo


def run_bib_format_dialog(parent, *, title: str, suggested: str = BIBLATEX) -> str | None:
    dialog, combo = build_bib_format_dialog(parent, title=title, suggested=suggested)
    response = dialog.run()
    value = combo.get_active_id() if response == Gtk.ResponseType.OK else None
    dialog.destroy()
    return value


def confirm_bib_import(parent, plan: BibImportPlan) -> bool:
    projection = plan.projection
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.NONE,
        text="Apply BibTeX/BibLaTeX import to References?",
    )
    details = (
        f"Import: {projection.imported}\n"
        f"Replace: {projection.replaced}\n"
        f"Merge: {projection.merged}\n"
        f"Re-keyed: {projection.rekeyed}\n"
        f"Skip: {projection.skipped}\n\n"
        "Only references.md will be changed. The source .bib file, current document "
        "and Source Notes remain unchanged."
    )
    dialog.format_secondary_text(details)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Apply Import", Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def build_bib_export_preview_dialog(parent, artifact: BibExportArtifact) -> BibExportPreviewWidgets:
    dialog = Gtk.Dialog(title="Export References — Preview", transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Choose Destination…", Gtk.ResponseType.OK)
    dialog.set_default_size(820, 600)
    content = dialog.get_content_area()
    content.set_spacing(8)
    content.set_border_width(10)
    warning_text = (
        f"{artifact.reference_count} References; {len(artifact.warnings)} representability warning(s). "
        "This is a derived canonical export, not a byte-for-byte round trip."
    )
    warning_label = Gtk.Label(label=warning_text)
    warning_label.set_xalign(0)
    warning_label.set_line_wrap(True)
    content.pack_start(warning_label, False, False, 0)
    if artifact.warnings:
        warnings = Gtk.Label(label="\n".join(f"• {item}" for item in artifact.warnings))
        warnings.set_xalign(0)
        warnings.set_line_wrap(True)
        content.pack_start(warnings, False, False, 0)
    text_view = Gtk.TextView()
    text_view.set_editable(False)
    text_view.set_cursor_visible(False)
    text_view.set_monospace(True)
    text_view.set_wrap_mode(Gtk.WrapMode.NONE)
    text_view.get_buffer().set_text(artifact.text)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(text_view)
    content.pack_start(scroll, True, True, 0)
    dialog.show_all()
    widgets = BibExportPreviewWidgets(dialog, text_view, warning_label, artifact)
    dialog._calamus_bib_export_widgets = widgets
    return widgets


def run_bib_export_preview_dialog(parent, artifact: BibExportArtifact) -> bool:
    widgets = build_bib_export_preview_dialog(parent, artifact)
    response = widgets.dialog.run()
    widgets.dialog.destroy()
    return response == Gtk.ResponseType.OK


def run_bib_export_destination_dialog(parent, format: str) -> str | None:
    label = "BibLaTeX" if format == BIBLATEX else "BibTeX"
    dialog = Gtk.FileChooserDialog(
        title=f"Export References as {label}",
        transient_for=parent,
        action=Gtk.FileChooserAction.SAVE,
    )
    dialog.set_modal(True)
    dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    dialog.add_button("Export", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_local_only(True)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name("BibTeX/BibLaTeX (*.bib)")
    file_filter.add_pattern("*.bib")
    dialog.add_filter(file_filter)
    dialog.set_filter(file_filter)
    dialog.set_current_name("calamus-references.bib")
    response = dialog.run()
    filename = dialog.get_filename() if response == Gtk.ResponseType.OK else None
    dialog.destroy()
    if not filename:
        return None
    if Path(filename).suffix.casefold() != ".bib":
        filename += ".bib"
    return filename


def show_bib_error(parent, title: str, message: str) -> None:
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def show_bib_import_result(parent, result: BibImportResult) -> None:
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.INFO if result.succeeded else Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text="BibTeX/BibLaTeX import complete" if result.succeeded else "BibTeX/BibLaTeX import failed",
    )
    dialog.format_secondary_text(result.message)
    dialog.run()
    dialog.destroy()


def show_bib_export_result(parent, result: BibExportResult) -> None:
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.INFO if result.succeeded else Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text="References export complete" if result.succeeded else "References export failed",
    )
    detail = result.message + (f"\n\n{result.path}" if result.path else "")
    dialog.format_secondary_text(detail)
    dialog.run()
    dialog.destroy()
