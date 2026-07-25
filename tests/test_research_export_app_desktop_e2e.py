"""Desktop proofs for the unitary W85 product dialog and export gateway."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import unittest
import uuid

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
    HAVE_GTK = True
except Exception:
    HAVE_GTK = False

ROOT = Path(__file__).resolve().parents[1]


def _display_ready():
    if not HAVE_GTK:
        return False
    try:
        result = Gtk.init_check()
    except TypeError:
        result = Gtk.init_check(None)
    ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
    return bool(ok and Gdk.Display.get_default() is not None)


def _pump():
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w85_app_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ResearchExportAppDesktopE2E(unittest.TestCase):

    def test_real_product_dialog_runs_with_five_products_and_dossier_default(self):
        if not _display_ready():
            self.skipTest("GTK display unavailable")

        from calamus_research_export import (
            FULL_RESEARCH_DOSSIER,
            research_export_kinds,
            research_export_title,
        )
        from calamus_research_export_dialogs import build_research_export_product_dialog

        dialog, chooser = build_research_export_product_dialog(None)
        failures = []

        def inspect_and_cancel():
            try:
                self.assertTrue(dialog.get_visible())
                self.assertTrue(chooser.get_visible())
                self.assertEqual(chooser.get_model().iter_n_children(None), 5)
                self.assertEqual(chooser.get_active_id(), FULL_RESEARCH_DOSSIER)
                self.assertEqual(
                    chooser.get_active_text(),
                    research_export_title(FULL_RESEARCH_DOSSIER),
                )
                for kind in research_export_kinds():
                    chooser.set_active_id(kind)
                    self.assertEqual(chooser.get_active_id(), kind)
                    self.assertEqual(chooser.get_active_text(), research_export_title(kind))
                button = dialog.get_widget_for_response(Gtk.ResponseType.OK)
                self.assertEqual(button.get_label(), "Choose Destination…")
            except Exception as error:  # surface callback failures after run exits
                failures.append(error)
            dialog.response(Gtk.ResponseType.CANCEL)
            return False

        GLib.idle_add(inspect_and_cancel)
        response = dialog.run()
        dialog.destroy()
        _pump()
        if failures:
            raise failures[0]
        self.assertEqual(response, Gtk.ResponseType.CANCEL)
        print("W85_REAL_PRODUCT_DIALOG_RUN=PASS")
        print("W85_REAL_PRODUCT_DIALOG_FIVE_CHOICES=PASS")
        print("W85_REAL_PRODUCT_DIALOG_DOSSIER_DEFAULT=PASS")

    def test_real_destination_dialog_runs_with_product_specific_markdown_name(self):
        document = os.environ.get("CALAMUS_W85_E2E_DOCUMENT")
        if not document:
            self.skipTest("W85 E2E document unavailable")
        if not _display_ready():
            self.skipTest("GTK display unavailable")

        from calamus_research_export import FULL_RESEARCH_DOSSIER
        from calamus_research_export_dialogs import build_research_export_destination_dialog

        document = os.path.abspath(document)
        dialog = build_research_export_destination_dialog(
            None,
            document,
            FULL_RESEARCH_DOSSIER,
        )
        failures = []

        def inspect_and_cancel():
            try:
                self.assertTrue(dialog.get_visible())
                self.assertEqual(dialog.get_action(), Gtk.FileChooserAction.SAVE)
                self.assertTrue(dialog.get_local_only())
                self.assertTrue(dialog.get_do_overwrite_confirmation())
                self.assertFalse(dialog.get_select_multiple())
                self.assertFalse(dialog.get_create_folders())
                self.assertEqual(
                    dialog.get_current_name(),
                    "W85_Research_Sample-research-dossier.md",
                )
                self.assertEqual(dialog.get_filter().get_name(), "Markdown (*.md)")
            except Exception as error:
                failures.append(error)
            dialog.response(Gtk.ResponseType.CANCEL)
            return False

        GLib.idle_add(inspect_and_cancel)
        response = dialog.run()
        dialog.destroy()
        _pump()
        if failures:
            raise failures[0]
        self.assertEqual(response, Gtk.ResponseType.CANCEL)
        print("W85_REAL_DESTINATION_DIALOG_RUN=PASS")
        print("W85_REAL_DESTINATION_MARKDOWN_NAME=PASS")

    def test_real_app_exports_dossier_without_mutating_authorities(self):
        document = os.environ.get("CALAMUS_W85_E2E_DOCUMENT")
        output = os.environ.get("CALAMUS_W85_E2E_OUTPUT")
        if not document or not output:
            self.skipTest("W85 E2E paths unavailable")
        if not _display_ready():
            self.skipTest("GTK display unavailable")

        from calamus_research_export import FULL_RESEARCH_DOSSIER
        from calamus_reference_store import default_references_path
        from calamus_source_note_store import source_notes_path

        document = os.path.abspath(document)
        output = os.path.abspath(output)
        references = default_references_path()
        sidecar = source_notes_path(document)
        protected = {
            document: Path(document).read_bytes(),
            references: Path(references).read_bytes(),
            sidecar: Path(sidecar).read_bytes(),
        }

        module = _load_app_module()
        win = module.App()
        try:
            win.show_all()
            _pump()
            self.assertTrue(win.open_path(document))
            win.research_export_runtime._chooser = lambda *_: (
                FULL_RESEARCH_DOSSIER,
                output,
            )
            messages = []
            win.research_export_runtime._show_info = messages.append
            win.research_export_runtime._show_error = lambda message: self.fail(message)

            self.assertTrue(win.on_export_research_apparatus())
            self.assertTrue(Path(output).is_file())
            exported = Path(output).read_text(encoding="utf-8")
            self.assertIn("# Complete Research Dossier", exported)
            self.assertIn("Evidence in the introduction", exported)
            self.assertIn("ratzinger1968", exported)
            self.assertTrue(messages)
            for path, content in protected.items():
                self.assertEqual(Path(path).read_bytes(), content)
            print("W85_REAL_APP_RESEARCH_EXPORT=PASS")
            print("W85_RESEARCH_AUTHORITIES_UNCHANGED=PASS")
            print("W85_ATOMIC_MARKDOWN_OUTPUT=PASS")
        finally:
            win.destroy()
            _pump()


if __name__ == "__main__":
    unittest.main()
