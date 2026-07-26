"""Real GTK and real App proofs for W88 Authoring Bridge workflows."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

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
    name = f"calamus_w88_app_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _set_isolated_config(root: Path):
    import calamus_config

    config = root / "config" / "calamus"
    calamus_config.CONFIG_DIR = str(config)
    calamus_config.SETTINGS_FILE = str(config / "settings.json")
    calamus_config.RECENT_FILE = str(config / "recent.json")
    calamus_config.FAVOURITES_FILE = str(config / "favourites.json")


def _prepare_authorities(root: Path):
    from calamus_reference_store import MarkdownReferenceStore
    from calamus_references import ReferenceRecord
    from calamus_source_note_store import serialize_source_notes_markdown, source_notes_path
    from calamus_source_notes import SourceNote

    document = root / "Chapter.md"
    document.write_text(
        "# Introduction {#intro}\n"
        "Selected evidence.\n"
        "Cite [@ref].\n"
        "See [Method](#method).\n"
        "## Method {#method}\n"
        "Method body.\n",
        encoding="utf-8",
    )
    store = MarkdownReferenceStore()
    snapshot = store.load()
    result = store.save(
        (
            ReferenceRecord(
                key="ref",
                title="Reference Title",
                authors=("Doe, Jane",),
                year="2024",
            ),
        ),
        snapshot.token,
    )
    if not result.saved:
        raise AssertionError(result.message)
    sidecar = Path(source_notes_path(str(document)))
    sidecar.write_text(
        serialize_source_notes_markdown(
            (
                SourceNote(
                    id="sn-existing",
                    kind="quote",
                    text="Existing note",
                    reference_key="ref",
                    target="#intro",
                ),
            )
        ),
        encoding="utf-8",
    )
    return document, sidecar


def _selected_text(win):
    buffer = win.text.get_buffer()
    if not buffer.get_has_selection():
        return ""
    start, end = buffer.get_selection_bounds()
    return buffer.get_text(start, end, True)


def _visible_dialog(title):
    return next(
        (
            window
            for window in Gtk.Window.list_toplevels()
            if isinstance(window, Gtk.Dialog)
            and window.get_visible()
            and (window.get_title() or "") == title
        ),
        None,
    )


def _named_widgets(widget, name, widget_type):
    values = []
    if isinstance(widget, widget_type) and widget.get_name() == name:
        values.append(widget)
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            values.extend(_named_widgets(child, name, widget_type))
    return values


def _named_widget(widget, name, widget_type):
    values = _named_widgets(widget, name, widget_type)
    if len(values) != 1:
        raise AssertionError(
            f"expected exactly one {widget_type.__name__} named {name!r}; "
            f"found {len(values)}"
        )
    return values[0]


def _text_view_value(text_view):
    buffer = text_view.get_buffer()
    start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


@unittest.skipUnless(HAVE_GTK, "PyGObject unavailable")
class AuthoringBridgeAppDesktopE2E(unittest.TestCase):
    def test_real_app_bridge_rows_navigate_exact_document_and_source_note(self):
        if not _display_ready():
            self.skipTest("GTK display unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = {
                "HOME": str(root),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_CONFIG_HOME": str(root / "config"),
            }
            with patch.dict(os.environ, environment, clear=False):
                _set_isolated_config(root)
                document, _sidecar = _prepare_authorities(root)
                module = _load_app_module()
                win = module.App()
                try:
                    win.show_all()
                    _pump()
                    self.assertTrue(win.open_path(str(document)))
                    self.assertTrue(win.show_authoring_bridge())
                    _pump()

                    runtime = win.authoring_bridge_runtime
                    controller = runtime.controller
                    view = runtime._view
                    self.assertEqual(controller.mode, "reference")
                    citation = next(
                        item for item in controller.visible_occurrences
                        if item.kind == "citation"
                    )
                    view.select_occurrence_id(citation.id)
                    view._listbox.emit("row-activated", view._rows[citation.id])
                    _pump()
                    self.assertEqual(_selected_text(win), "[@ref]")

                    view._mode_selector.set_active_id("heading")
                    _pump()
                    view._subject_selector.set_active_id("method")
                    _pump()
                    heading_link = next(
                        item for item in controller.visible_occurrences
                        if item.kind == "heading-link"
                    )
                    view.select_occurrence_id(heading_link.id)
                    view._listbox.emit("row-activated", view._rows[heading_link.id])
                    _pump()
                    self.assertEqual(_selected_text(win), "[Method](#method)")

                    win.show_authoring_bridge()
                    view._mode_selector.set_active_id("heading")
                    view._subject_selector.set_active_id("intro")
                    _pump()
                    source_note = next(
                        item for item in controller.visible_occurrences
                        if item.kind == "source-note-target"
                    )
                    view.select_occurrence_id(source_note.id)
                    view._listbox.emit("row-activated", view._rows[source_note.id])
                    _pump()
                    self.assertEqual(win.research_panel_runtime.active_client, "source-notes")
                    self.assertEqual(
                        win.source_note_panel_runtime.controller.selected_note().id,
                        "sn-existing",
                    )
                    print("W88_REAL_APP_DERIVED_REFERENCE_BACKLINK=PASS")
                    print("W88_REAL_APP_DERIVED_HEADING_BACKLINK=PASS")
                    print("W88_REAL_APP_DIRECT_SOURCE_NOTE_NAVIGATION=PASS")
                finally:
                    win.destroy()
                    _pump()

    def test_real_app_selection_to_source_note_and_heading_link_are_wired(self):
        if not _display_ready():
            self.skipTest("GTK display unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = {
                "HOME": str(root),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_CONFIG_HOME": str(root / "config"),
            }
            with patch.dict(os.environ, environment, clear=False):
                _set_isolated_config(root)
                document, sidecar = _prepare_authorities(root)
                original_document = document.read_text(encoding="utf-8")
                module = _load_app_module()
                win = module.App()
                failures = []
                try:
                    win.show_all()
                    _pump()
                    self.assertTrue(win.open_path(str(document)))
                    win.reference_panel_runtime.controller.ensure_loaded()
                    self.assertTrue(win.reference_panel_runtime.controller.select_key("ref"))

                    start = win.buffer_text().index("Selected evidence")
                    end = start + len("Selected evidence")
                    win.select_range(start, end)

                    def accept_source_note():
                        dialog = None
                        try:
                            dialog = _visible_dialog("Add Source Note")
                            self.assertIsNotNone(dialog)
                            self.assertEqual(dialog.get_name(), "calamus-source-note-dialog")
                            text_view = _named_widget(
                                dialog, "source-note-text", Gtk.TextView
                            )
                            kind_combo = _named_widget(
                                dialog, "source-note-kind", Gtk.ComboBoxText
                            )
                            reference_combo = _named_widget(
                                dialog, "source-note-reference", Gtk.ComboBoxText
                            )
                            target_combo = _named_widget(
                                dialog, "source-note-target", Gtk.ComboBoxText
                            )
                            # Simulate the focus transition that can clear the
                            # visible editor selection while a modal dialog runs.
                            win.set_cursor_offset(len(win.buffer_text()))
                            self.assertEqual(_text_view_value(text_view), "Selected evidence")
                            self.assertEqual(kind_combo.get_active_id(), "quote")
                            self.assertEqual(reference_combo.get_active_id(), "ref")
                            self.assertEqual(target_combo.get_active_id(), "#intro")
                            dialog.response(Gtk.ResponseType.OK)
                        except Exception as error:
                            failures.append(error)
                            if dialog is not None:
                                dialog.response(Gtk.ResponseType.CANCEL)
                        return False

                    GLib.idle_add(accept_source_note)
                    created = win.on_create_source_note_from_selection()
                    _pump()
                    if failures:
                        raise failures.pop(0)
                    self.assertTrue(created)
                    from calamus_source_note_store import parse_source_notes_markdown

                    notes, diagnostics = parse_source_notes_markdown(
                        sidecar.read_text(encoding="utf-8")
                    )
                    self.assertEqual(diagnostics, ())
                    self.assertEqual(len(notes), 2)
                    created_note = next(note for note in notes if note.id != "sn-existing")
                    self.assertEqual(created_note.text, "Selected evidence")
                    self.assertEqual(created_note.reference_key, "ref")
                    self.assertEqual(created_note.target, "#intro")
                    self.assertEqual(win.buffer_text(), original_document)

                    replace_start = win.buffer_text().index("Cite")
                    replace_end = replace_start + len("Cite")
                    win.select_range(replace_start, replace_end)
                    failures.clear()

                    def accept_heading_link():
                        dialog = None
                        try:
                            dialog = _visible_dialog("Insert Link to Heading")
                            self.assertIsNotNone(dialog)
                            self.assertEqual(dialog.get_name(), "calamus-heading-link-dialog")
                            combo = _named_widget(
                                dialog, "heading-link-target", Gtk.ComboBoxText
                            )
                            entry = _named_widget(
                                dialog, "heading-link-label", Gtk.Entry
                            )
                            preview = _named_widget(
                                dialog, "heading-link-preview", Gtk.Label
                            )
                            # Move the live cursor after capture: insertion must
                            # still replace the original selected range.
                            win.set_cursor_offset(len(win.buffer_text()))
                            combo.set_active_id("method")
                            entry.set_text("See method")
                            self.assertEqual(
                                preview.get_text(), "[See method](#method)"
                            )
                            dialog.response(Gtk.ResponseType.OK)
                        except Exception as error:
                            failures.append(error)
                            if dialog is not None:
                                dialog.response(Gtk.ResponseType.CANCEL)
                        return False

                    GLib.idle_add(accept_heading_link)
                    self.assertTrue(win.on_insert_link_to_heading())
                    _pump()
                    if failures:
                        raise failures.pop(0)
                    expected = original_document.replace(
                        "Cite", "[See method](#method)", 1
                    )
                    self.assertEqual(win.buffer_text(), expected)
                    undo_result = win.on_undo()
                    self.assertIsNone(undo_result)
                    _pump()
                    self.assertEqual(win.buffer_text(), original_document)
                    print("W88_REAL_APP_SELECTION_SNAPSHOT_BEFORE_DIALOG=PASS")
                    print("W88_REAL_APP_SELECTION_TO_SOURCE_NOTE=PASS")
                    print("W88_REAL_APP_HEADING_LINK_DIALOG=PASS")
                    print("W88_REAL_APP_HEADING_LINK_CAPTURED_RANGE=PASS")
                    print("W88_REAL_APP_HEADING_LINK_UNDO_EFFECT=PASS")
                finally:
                    win.destroy()
                    _pump()



if __name__ == "__main__":
    unittest.main()
