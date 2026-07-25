"""Real GTK and real App proofs for W87 BibTeX/BibLaTeX workflows."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import time
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
    name = f"calamus_w87_app_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _dialog_text(dialog) -> str:
    values = []

    def collect(widget):
        if isinstance(widget, Gtk.Label):
            values.append(widget.get_text())
        if isinstance(widget, Gtk.Container):
            for child in widget.get_children():
                collect(child)

    if isinstance(dialog, Gtk.MessageDialog):
        collect(dialog.get_message_area())
    title = dialog.get_title() if hasattr(dialog, "get_title") else ""
    return "\n".join((title or "", *values))


def _visible_dialogs():
    return [
        window for window in Gtk.Window.list_toplevels()
        if isinstance(window, Gtk.Dialog) and window.get_visible()
    ]


class BibtexAppDesktopE2E(unittest.TestCase):
    def test_real_preview_executes_second_row_and_collision_actions_without_freeze(self):
        if not _display_ready():
            self.skipTest("GTK display unavailable")
        from calamus_bibtex import (
            ACTION_IMPORT,
            ACTION_MERGE,
            ACTION_SKIP,
            BIBLATEX,
            build_import_preview,
            export_references,
            parse_bibliography,
        )
        from calamus_bibtex_dialogs import build_bib_export_preview_dialog
        from calamus_bibtex_import_view import build_bib_import_preview_dialog
        from calamus_references import ReferenceRecord

        library = parse_bibliography('''
@comment{not imported}
@book{existing, title={Incoming title}, publisher={Press}}
@online{fresh, title={Fresh title}}
@book{invalid, title={One}, title={Two}}
''', BIBLATEX)
        existing = (ReferenceRecord(key="existing", title="Existing title"),)
        preview = build_import_preview(library, existing)
        widgets = build_bib_import_preview_dialog(None, preview)
        failures = []
        completed = {"value": False}

        def watchdog():
            if completed["value"]:
                return False
            failures.append(TimeoutError("interactive preview did not complete"))
            widgets.dialog.response(Gtk.ResponseType.CANCEL)
            return False

        def interact():
            try:
                self.assertTrue(widgets.dialog.get_visible())
                self.assertEqual(widgets.store.iter_n_children(None), 3)
                self.assertEqual(len(widgets.tree.get_columns()), 5)
                self.assertEqual(widgets.session.unresolved_count, 1)
                self.assertFalse(widgets.review_button.get_sensitive())

                # Exercise the second row first: this exact path froze the retired candidate.
                widgets.tree.get_selection().select_path(Gtk.TreePath.new_from_string("1"))
                widgets.action_buttons[ACTION_SKIP].set_active(True)
                self.assertEqual(widgets.session.action(1), ACTION_SKIP)
                widgets.action_buttons[ACTION_IMPORT].set_active(True)
                self.assertEqual(widgets.session.action(1), ACTION_IMPORT)
                self.assertEqual(widgets.store[1][5], "Import")

                # Resolve the collision through a fixed radio control.
                widgets.tree.get_selection().select_path(Gtk.TreePath.new_from_string("0"))
                self.assertIn("Existing title", widgets.current_summary.get_text())
                self.assertIn("Incoming title", widgets.incoming_summary.get_text())
                widgets.action_buttons[ACTION_MERGE].set_active(True)
                self.assertEqual(widgets.session.action(0), ACTION_MERGE)
                self.assertEqual(widgets.store[0][5], "Merge missing fields")
                self.assertTrue(widgets.review_button.get_sensitive())

                # Invalid input remains locked to Skip.
                widgets.tree.get_selection().select_path(Gtk.TreePath.new_from_string("2"))
                self.assertEqual(widgets.session.action(2), ACTION_SKIP)
                self.assertTrue(all(
                    not button.get_sensitive()
                    for button in widgets.action_buttons.values()
                ))

                decisions = widgets.session.decisions()
                self.assertEqual(
                    tuple((item.index, item.action) for item in decisions),
                    ((0, ACTION_MERGE), (1, ACTION_IMPORT), (2, ACTION_SKIP)),
                )
                completed["value"] = True
                widgets.dialog.response(Gtk.ResponseType.OK)
            except Exception as error:
                failures.append(error)
                completed["value"] = True
                widgets.dialog.response(Gtk.ResponseType.CANCEL)
            return False

        GLib.timeout_add_seconds(5, watchdog)
        GLib.idle_add(interact)
        response = widgets.dialog.run()
        widgets.dialog.destroy()
        _pump()
        if failures:
            raise failures[0]
        self.assertEqual(response, Gtk.ResponseType.OK)

        artifact = export_references(existing, BIBLATEX)
        export_widgets = build_bib_export_preview_dialog(None, artifact)
        failures = []

        def inspect_export():
            try:
                self.assertTrue(export_widgets.dialog.get_visible())
                self.assertIn("1 References", export_widgets.warning_label.get_text())
                start, end = export_widgets.text_view.get_buffer().get_bounds()
                text = export_widgets.text_view.get_buffer().get_text(start, end, True)
                self.assertIn("@book{existing,", text)
            except Exception as error:
                failures.append(error)
            export_widgets.dialog.response(Gtk.ResponseType.CANCEL)
            return False

        GLib.idle_add(inspect_export)
        export_widgets.dialog.run()
        export_widgets.dialog.destroy()
        _pump()
        if failures:
            raise failures[0]
        print("W87_REAL_IMPORT_PREVIEW_DIALOG=PASS")
        print("W87_REAL_SECOND_ROW_ACTION=PASS")
        print("W87_REAL_COLLISION_RADIO_ACTION=PASS")
        print("W87_REAL_UNRESOLVED_GATE=PASS")
        print("W87_REAL_EXPORT_PREVIEW_DIALOG=PASS")

    def test_real_app_uses_real_preview_confirm_and_export_dialogs(self):
        document = os.environ.get("CALAMUS_W87_E2E_DOCUMENT")
        source = os.environ.get("CALAMUS_W87_E2E_IMPORT_SOURCE")
        output = os.environ.get("CALAMUS_W87_E2E_EXPORT_OUTPUT")
        if not document or not source or not output:
            self.skipTest("W87 E2E paths unavailable")
        if not _display_ready():
            self.skipTest("GTK display unavailable")

        from calamus_bibtex import ACTION_IMPORT, ACTION_MERGE, BIBLATEX
        from calamus_reference_store import MarkdownReferenceStore, default_references_path
        import calamus_bibtex_runtime as runtime_module

        document = os.path.abspath(document)
        source = os.path.abspath(source)
        output = os.path.abspath(output)
        doc_before = Path(document).read_bytes()
        source_before = Path(source).read_bytes()

        originals = {
            name: getattr(runtime_module, name)
            for name in (
                "run_bib_file_dialog",
                "run_bib_format_dialog",
                "run_bib_export_destination_dialog",
            )
        }
        runtime_module.run_bib_file_dialog = lambda *_: source
        runtime_module.run_bib_format_dialog = lambda *_args, **_kwargs: BIBLATEX
        runtime_module.run_bib_export_destination_dialog = lambda *_: output

        module = _load_app_module()
        win = module.App()
        failures = []
        try:
            win.show_all()
            _pump()
            self.assertTrue(win.open_path(document))

            import_phase = {"value": "preview"}
            deadline = time.monotonic() + 8.0

            def drive_import():
                try:
                    if time.monotonic() > deadline:
                        raise TimeoutError(f"import dialog phase timed out: {import_phase['value']}")
                    for dialog in _visible_dialogs():
                        title = dialog.get_title() or ""
                        text = _dialog_text(dialog)
                        if import_phase["value"] == "preview" and title == "Import BibTeX/BibLaTeX — Review Entries":
                            widgets = dialog._calamus_bib_import_widgets
                            widgets.tree.get_selection().select_path(Gtk.TreePath.new_from_string("1"))
                            widgets.action_buttons[ACTION_IMPORT].set_active(True)
                            widgets.tree.get_selection().select_path(Gtk.TreePath.new_from_string("0"))
                            widgets.action_buttons[ACTION_MERGE].set_active(True)
                            self.assertTrue(widgets.review_button.get_sensitive())
                            import_phase["value"] = "confirm"
                            dialog.response(Gtk.ResponseType.OK)
                            return True
                        if import_phase["value"] == "confirm" and "Apply BibTeX/BibLaTeX import" in text:
                            self.assertIn("Import: 1", text)
                            self.assertIn("Merge: 1", text)
                            self.assertIn("Skip: 1", text)
                            import_phase["value"] = "result"
                            dialog.response(Gtk.ResponseType.OK)
                            return True
                        if import_phase["value"] == "result" and "import complete" in text.casefold():
                            import_phase["value"] = "done"
                            dialog.response(Gtk.ResponseType.OK)
                            return False
                    return True
                except Exception as error:
                    failures.append(error)
                    for dialog in _visible_dialogs():
                        dialog.response(Gtk.ResponseType.CANCEL)
                    return False

            GLib.timeout_add(20, drive_import)
            self.assertTrue(win.on_import_bibtex_biblatex())
            if failures:
                raise failures[0]
            self.assertEqual(import_phase["value"], "done")

            store = MarkdownReferenceStore(default_references_path())
            records = store.load().records
            keys = tuple(record.key for record in records)
            self.assertIn("existing", keys)
            self.assertIn("fresh", keys)
            self.assertNotIn("invalid", keys)
            existing = next(record for record in records if record.key == "existing")
            self.assertEqual(existing.title, "Existing local title")
            self.assertEqual(existing.doi, "10.1000/incoming")
            self.assertEqual(existing.publisher, "Cambridge University Press")
            references_before_export = Path(store.path).read_bytes()

            export_phase = {"value": "preview"}
            deadline = time.monotonic() + 8.0

            def drive_export():
                try:
                    if time.monotonic() > deadline:
                        raise TimeoutError(f"export dialog phase timed out: {export_phase['value']}")
                    for dialog in _visible_dialogs():
                        title = dialog.get_title() or ""
                        text = _dialog_text(dialog)
                        if export_phase["value"] == "preview" and title == "Export References — Preview":
                            widgets = dialog._calamus_bib_export_widgets
                            start, end = widgets.text_view.get_buffer().get_bounds()
                            preview_text = widgets.text_view.get_buffer().get_text(start, end, True)
                            self.assertIn("@book{existing,", preview_text)
                            self.assertIn("fresh", preview_text)
                            export_phase["value"] = "result"
                            dialog.response(Gtk.ResponseType.OK)
                            return True
                        if export_phase["value"] == "result" and "export complete" in text.casefold():
                            export_phase["value"] = "done"
                            dialog.response(Gtk.ResponseType.OK)
                            return False
                    return True
                except Exception as error:
                    failures.append(error)
                    for dialog in _visible_dialogs():
                        dialog.response(Gtk.ResponseType.CANCEL)
                    return False

            GLib.timeout_add(20, drive_export)
            self.assertTrue(win.on_export_references_bibtex_biblatex())
            if failures:
                raise failures[0]
            self.assertEqual(export_phase["value"], "done")
            self.assertTrue(Path(output).is_file())
            self.assertIn("@book{existing,", Path(output).read_text(encoding="utf-8"))
            self.assertEqual(Path(store.path).read_bytes(), references_before_export)
            self.assertEqual(Path(document).read_bytes(), doc_before)
            self.assertEqual(Path(source).read_bytes(), source_before)
            print("W87_REAL_APP_IMPORT_WITH_REAL_DIALOGS=PASS")
            print("W87_REAL_COLLISION_MERGE=PASS")
            print("W87_REAL_IMPACT_CONFIRMATION=PASS")
            print("W87_REAL_APP_EXPORT_WITH_REAL_PREVIEW=PASS")
            print("W87_DOCUMENT_AND_SOURCE_UNCHANGED=PASS")
        finally:
            for name, value in originals.items():
                setattr(runtime_module, name, value)
            win.destroy()
            _pump()


if __name__ == "__main__":
    unittest.main()
