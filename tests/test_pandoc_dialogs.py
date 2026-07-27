"""Real GTK builder proofs for the owned W90 Pandoc dialogs.

The runner executes each test method in a fresh subprocess.  Builder tests do
not enter a nested modal loop; modal-session behavior has its own dedicated
lane in ``test_modal_dialog_gtk_session``.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from calamus_gtk_test_driver import HAVE_GTK, Gtk, display_ready

if HAVE_GTK:
    from calamus_modal_dialog import ModalSession
    from calamus_pandoc import (
        FORMAT_DOCX,
        FORMAT_PLAIN,
        PRODUCT_BIBLIOGRAPHY,
        PRODUCT_DOCUMENT,
        SCOPE_CITED,
        SCOPE_REFERENCE_SET,
    )
    from calamus_pandoc_controller import PandocPreviewResult
    from calamus_pandoc_dialogs import (
        PandocOptionsWidgets,
        PandocPreviewWidgets,
        PandocProgressWidgets,
        build_pandoc_destination_dialog,
        build_pandoc_options_dialog,
        build_pandoc_preview_dialog,
        build_pandoc_progress_dialog,
    )


def _text(view):
    buffer = view.get_buffer()
    start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


@unittest.skipUnless(HAVE_GTK and display_ready(), "real GTK display required")
class PandocDialogComponentTests(unittest.TestCase):
    def setUp(self):
        self.parent = Gtk.Window()

    def tearDown(self):
        self.parent.hide()
        self.parent.destroy()

    def test_options_builder_has_typed_controls_and_closed_surface(self):
        widgets = build_pandoc_options_dialog(self.parent, ("Core sources", "Patristics"))
        with ModalSession(widgets.dialog):
            self.assertIsInstance(widgets, PandocOptionsWidgets)
            self.assertIs(widgets.dialog.get_transient_for(), self.parent)
            self.assertEqual(widgets.product_combo.get_name(), "calamus-pandoc-product")
            self.assertEqual(widgets.scope_combo.get_name(), "calamus-pandoc-scope")
            self.assertEqual(widgets.set_combo.get_name(), "calamus-pandoc-reference-set")
            self.assertEqual(widgets.format_combo.get_name(), "calamus-pandoc-format")
            self.assertEqual(widgets.csl_chooser.get_name(), "calamus-pandoc-csl")
            self.assertEqual(widgets.product_combo.get_active_id(), PRODUCT_DOCUMENT)
            self.assertEqual(widgets.scope_combo.get_active_id(), SCOPE_CITED)
            self.assertEqual(widgets.format_combo.get_active_id(), "odt")
            self.assertFalse(widgets.set_combo.get_sensitive())
            widgets.scope_combo.set_active_id(SCOPE_REFERENCE_SET)
            self.assertTrue(widgets.set_combo.get_sensitive())
            self.assertEqual(widgets.set_combo.get_active_id(), "Core sources")
            widgets.product_combo.set_active_id(PRODUCT_BIBLIOGRAPHY)
            self.assertEqual(widgets.format_combo.get_active_id(), FORMAT_PLAIN)
            self.assertNotEqual(widgets.format_combo.get_active_id(), "pdf")
            print("W90_PANDOC_OPTIONS_BUILDER=PASS")

    def test_destination_builder_is_local_owned_and_typed(self):
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "paper.md"
            document.write_text("# Paper", encoding="utf-8")
            destination = build_pandoc_destination_dialog(
                self.parent, str(document), PRODUCT_DOCUMENT, FORMAT_DOCX
            )
            with ModalSession(destination):
                self.assertIs(destination.get_transient_for(), self.parent)
                self.assertEqual(destination.get_current_name(), "paper-with-citations.docx")
                self.assertTrue(destination.get_do_overwrite_confirmation())
                self.assertTrue(destination.get_local_only())
                self.assertFalse(destination.get_select_multiple())
                print("W90_PANDOC_DESTINATION_BUILDER=PASS")

    def test_preview_builder_owns_semantic_text(self):
        preview = PandocPreviewResult(
            "previewed",
            "Pandoc: /usr/bin/pandoc\nReferences: 2",
            "Guardini. The Lord.\nRatzinger. Introduction to Christianity.",
        )
        widgets = build_pandoc_preview_dialog(self.parent, None, preview)
        with ModalSession(widgets.dialog):
            self.assertIsInstance(widgets, PandocPreviewWidgets)
            self.assertEqual(widgets.dialog.get_title(), "Pandoc/citeproc — Semantic Preview")
            self.assertEqual(widgets.summary_view.get_name(), "calamus-pandoc-preview-summary")
            self.assertEqual(widgets.preview_view.get_name(), "calamus-pandoc-preview-text")
            self.assertEqual(_text(widgets.summary_view), preview.message)
            self.assertEqual(_text(widgets.preview_view), preview.text)
            print("W90_PANDOC_PREVIEW_BUILDER=PASS")

    def test_progress_builder_owns_spinner_and_status(self):
        progress = build_pandoc_progress_dialog(self.parent, "Exporting with Pandoc/citeproc…")
        with ModalSession(progress.dialog):
            self.assertIsInstance(progress, PandocProgressWidgets)
            self.assertFalse(progress.dialog.get_deletable())
            self.assertEqual(progress.spinner.get_name(), "calamus-pandoc-progress-spinner")
            self.assertEqual(progress.status_label.get_name(), "calamus-pandoc-progress-status")
            print("W90_PANDOC_PROGRESS_BUILDER=PASS")


if __name__ == "__main__":
    unittest.main()
