"""Real GTK and real App proofs for W86 Tag Integrity."""
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
    name = f"calamus_w86_app_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class TagIntegrityAppDesktopE2E(unittest.TestCase):
    def test_real_dialog_shows_inventory_scope_swatch_and_four_operations(self):
        if not _display_ready():
            self.skipTest("GTK display unavailable")

        from calamus_references import ReferenceRecord
        from calamus_source_notes import SourceNote
        from calamus_tag_integrity import TAG_SCOPE_BOTH, build_tag_inventory
        from calamus_tag_integrity_dialogs import build_tag_integrity_dialog

        inventory = build_tag_inventory(
            (
                ReferenceRecord(key="r1", title="One", tags=("Faith",)),
                ReferenceRecord(key="r2", title="Two", tags=("faith", "method")),
            ),
            (SourceNote(id="sn-1", kind="comment", text="Note", tags=(" FAITH ",)),),
        )
        widgets = build_tag_integrity_dialog(None, inventory)
        dialog = widgets.dialog
        failures = []

        def inspect_and_close():
            try:
                self.assertTrue(dialog.get_visible())
                self.assertTrue(widgets.scope.get_visible())
                self.assertEqual(widgets.scope.get_model().iter_n_children(None), 3)
                self.assertEqual(widgets.scope.get_active_id(), TAG_SCOPE_BOTH)
                self.assertTrue(widgets.tree.get_visible())
                self.assertEqual(widgets.store.iter_n_children(None), 2)
                self.assertEqual(len(widgets.tree.get_columns()), 5)
                iterator = widgets.store.get_iter_first()
                self.assertRegex(widgets.store.get_value(iterator, 0), r"^#[0-9A-F]{6}$")
                expected_buttons = (
                    (Gtk.ResponseType.CLOSE, "Close"),
                    (101, "Show Uses"),
                    (102, "Rename / Merge…"),
                    (103, "Remove Everywhere…"),
                    (104, "Normalize All…"),
                )
                for response_id, label in expected_buttons:
                    button = dialog.get_widget_for_response(response_id)
                    self.assertIsInstance(button, Gtk.Button)
                    self.assertTrue(button.get_visible())
                    self.assertEqual(button.get_label(), label)
            except Exception as error:
                failures.append(error)
            dialog.response(Gtk.ResponseType.CLOSE)
            return False

        GLib.idle_add(inspect_and_close)
        response = dialog.run()
        dialog.destroy()
        _pump()
        if failures:
            raise failures[0]
        self.assertEqual(response, Gtk.ResponseType.CLOSE)
        print("W86_REAL_TAG_DIALOG=PASS")
        print("W86_REAL_TAG_SCOPE_CHOICES=PASS")
        print("W86_REAL_DERIVED_SWATCH=PASS")

    def test_real_app_renames_tags_across_two_markdown_authorities(self):
        document = os.environ.get("CALAMUS_W86_E2E_DOCUMENT")
        if not document:
            self.skipTest("W86 E2E document unavailable")
        if not _display_ready():
            self.skipTest("GTK display unavailable")

        from calamus_reference_store import MarkdownReferenceStore, default_references_path
        from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
        from calamus_tag_integrity import TAG_ACTION_RENAME_MERGE, TAG_SCOPE_BOTH
        from calamus_tag_integrity_dialogs import TagIntegrityRequest
        import calamus_tag_integrity_runtime as runtime_module

        document = os.path.abspath(document)
        references = default_references_path()
        sidecar = source_notes_path(document)
        doc_before = Path(document).read_bytes()

        original_dialog = runtime_module.run_tag_integrity_dialog
        original_confirm = runtime_module.confirm_tag_mutation
        original_result = runtime_module.show_tag_result
        original_error = runtime_module.show_tag_error
        runtime_module.run_tag_integrity_dialog = lambda *_: TagIntegrityRequest(
            TAG_ACTION_RENAME_MERGE,
            TAG_SCOPE_BOTH,
            "Faith",
            "doctrine",
        )
        runtime_module.confirm_tag_mutation = lambda *_: True
        results = []
        runtime_module.show_tag_result = lambda _parent, result: results.append(result)
        runtime_module.show_tag_error = lambda _parent, title, message: self.fail(f"{title}: {message}")

        module = _load_app_module()
        win = module.App()
        try:
            win.show_all()
            _pump()
            self.assertTrue(win.open_path(document))
            self.assertTrue(win.on_tag_integrity())
            self.assertTrue(results and results[-1].succeeded)
            records = MarkdownReferenceStore(references).load().records
            notes = MarkdownSourceNoteStore(sidecar).load().notes
            self.assertTrue(records)
            self.assertTrue(notes)
            self.assertTrue(all("Faith" not in record.tags and "faith" not in record.tags for record in records))
            self.assertEqual(
                records[0].tags,
                ("doctrine", "Church  History", "Café", "temporary", "reference-only"),
            )
            self.assertEqual(
                records[1].tags,
                ("doctrine", "Church History", "Cafe\u0301", "temporary"),
            )
            self.assertEqual(
                notes[0].tags,
                ("doctrine", "church history", "CAFÉ", "temporary", "reference-only"),
            )
            self.assertEqual(Path(document).read_bytes(), doc_before)
            print("W86_REAL_APP_TAG_TRANSACTION=PASS")
            print("W86_REAL_TWO_MARKDOWN_AUTHORITIES=PASS")
            print("W86_ACTIVE_DOCUMENT_UNCHANGED=PASS")
        finally:
            runtime_module.run_tag_integrity_dialog = original_dialog
            runtime_module.confirm_tag_mutation = original_confirm
            runtime_module.show_tag_result = original_result
            runtime_module.show_tag_error = original_error
            win.destroy()
            _pump()


if __name__ == "__main__":
    unittest.main()
