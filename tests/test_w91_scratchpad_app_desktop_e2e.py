"""Real GTK and real-App proofs for W91 Scratchpad Basic."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

from calamus_gtk_test_driver import (
    HAVE_GTK,
    Gtk,
    ModalDriver,
    close_visible_dialogs,
    display_ready,
    named_widget,
    named_widgets,
    pump,
    visible_dialog,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_REAL_GTK = os.environ.get("CALAMUS_W91_RUN_REAL_GTK") == "1"


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w91_app_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _set_isolated_config(root: Path) -> None:
    import calamus_config

    config = root / "config" / "calamus"
    calamus_config.CONFIG_DIR = str(config)
    calamus_config.SETTINGS_FILE = str(config / "settings.json")
    calamus_config.RECENT_FILE = str(config / "recent.json")
    calamus_config.FAVOURITES_FILE = str(config / "favourites.json")


def _text(view) -> str:
    buffer = view.get_buffer()
    start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


@unittest.skipUnless(HAVE_GTK and display_ready(), "real GTK display required")
class W91ScratchpadGtkE2E(unittest.TestCase):
    def tearDown(self):
        close_visible_dialogs()

    def test_real_scratchpad_dialog_is_typed_owned_and_multi_section(self):
        if not RUN_REAL_GTK:
            self.skipTest("set CALAMUS_W91_RUN_REAL_GTK=1")
        from calamus_scratchpad_dialogs import run_scratchpad_dialog

        parent = Gtk.Window()
        result_box = {}

        def complete_dialog():
            dialog = visible_dialog("New Scratchpad Entry")
            if dialog is None:
                return False
            named_widget(dialog, "scratchpad-title", Gtk.Entry).set_text(
                "Tradition as living memory"
            )
            named_widget(dialog, "scratchpad-type", Gtk.ComboBoxText).set_active_id(
                "idea"
            )
            named_widget(dialog, "scratchpad-status", Gtk.ComboBoxText).set_active_id(
                "active"
            )
            named_widget(dialog, "scratchpad-tags", Gtk.Entry).set_text(
                "Tradition, Ecclesiology"
            )
            body = named_widget(dialog, "scratchpad-body", Gtk.TextView)
            body.get_buffer().set_text("Develop this line in the current chapter.")
            checks = named_widgets(dialog, "scratchpad-section", Gtk.CheckButton)
            self.assertEqual(len(checks), 2)
            checks[0].set_active(True)
            checks[1].set_active(True)
            dialog.response(Gtk.ResponseType.OK)
            return True

        driver = ModalDriver([complete_dialog])
        driver.start()
        try:
            result_box["entry"] = run_scratchpad_dialog(
                parent,
                (("#intro", "Introduction"), ("#method", "Method")),
                (),
            )
            driver.assert_complete()
            entry = result_box["entry"]
            self.assertIsNotNone(entry)
            self.assertEqual(entry.type, "idea")
            self.assertEqual(entry.status, "active")
            self.assertEqual(entry.tags, ("Tradition", "Ecclesiology"))
            self.assertEqual(entry.sections, ("#intro", "#method"))
            self.assertEqual(entry.body, "Develop this line in the current chapter.")
            self.assertFalse(visible_dialog("New Scratchpad Entry"))
            print("W91_SCRATCHPAD_TYPED_DIALOG=PASS")
            print("W91_SCRATCHPAD_MULTI_SECTION_DIALOG=PASS")
            print("W91_SCRATCHPAD_MODAL_OWNERSHIP=PASS")
        finally:
            parent.destroy()
            pump()

    def test_real_app_capture_filter_navigate_insert_and_persist(self):
        if not RUN_REAL_GTK:
            self.skipTest("set CALAMUS_W91_RUN_REAL_GTK=1")
        from calamus_scratchpad_store import MarkdownScratchpadStore, scratchpad_path

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = {
                "HOME": str(root),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_CONFIG_HOME": str(root / "config"),
                "XDG_CACHE_HOME": str(root / "cache"),
            }
            with patch.dict(os.environ, environment, clear=False):
                _set_isolated_config(root)
                document = root / "Article.md"
                original = (
                    "# Introduction {#intro}\n"
                    "Selected evidence for the argument.\n\n"
                    "## Method {#method}\n"
                    "Method body.\n"
                )
                document.write_text(original, encoding="utf-8")
                module = _load_app_module()
                win = module.App()
                try:
                    win.show_all()
                    pump()
                    self.assertTrue(win.open_path(str(document)))
                    pump()
                    selected = "Selected evidence for the argument."
                    start = win.buffer_text().index(selected)
                    win.select_range(start, start + len(selected))
                    self.assertEqual(win.current_heading_identifier(), "intro")

                    def complete_capture():
                        dialog = visible_dialog("New Scratchpad Entry")
                        if dialog is None:
                            return False
                        named_widget(dialog, "scratchpad-title", Gtk.Entry).set_text(
                            "Evidence to develop"
                        )
                        named_widget(dialog, "scratchpad-type", Gtk.ComboBoxText).set_active_id(
                            "idea"
                        )
                        named_widget(dialog, "scratchpad-tags", Gtk.Entry).set_text(
                            "evidence, introduction"
                        )
                        checks = named_widgets(
                            dialog, "scratchpad-section", Gtk.CheckButton
                        )
                        active = [
                            check.scratchpad_target
                            for check in checks
                            if check.get_active()
                        ]
                        self.assertEqual(active, ["#intro"])
                        self.assertEqual(
                            _text(named_widget(dialog, "scratchpad-body", Gtk.TextView)),
                            selected,
                        )
                        dialog.response(Gtk.ResponseType.OK)
                        return True

                    driver = ModalDriver([complete_capture])
                    driver.start()
                    self.assertTrue(win.on_capture_selection_in_scratchpad())
                    driver.assert_complete()
                    pump()

                    sidecar = Path(scratchpad_path(str(document)))
                    self.assertTrue(sidecar.is_file())
                    snapshot = MarkdownScratchpadStore(str(sidecar)).load()
                    self.assertFalse(snapshot.diagnostics)
                    self.assertEqual(len(snapshot.entries), 1)
                    entry = snapshot.entries[0]
                    self.assertEqual(entry.type, "idea")
                    self.assertEqual(entry.sections, ("#intro",))
                    self.assertEqual(entry.tags, ("evidence", "introduction"))

                    self.assertTrue(win.show_scratchpad())
                    pump()
                    runtime = win.scratchpad_runtime
                    self.assertEqual(win.research_panel_runtime.active_client, "scratchpad")
                    self.assertTrue(runtime.controller.select_id(entry.id))
                    self.assertTrue(runtime.show_for_current_section())
                    visible = runtime.controller.filtered_entries(
                        section="#intro", status="all"
                    )
                    self.assertEqual(tuple(item.id for item in visible), (entry.id,))
                    self.assertTrue(runtime.controller.select_id(entry.id))
                    self.assertTrue(runtime.on_open_section())
                    self.assertEqual(win.current_heading_identifier(), "intro")

                    before_insert = win.buffer_text()
                    win.set_cursor_offset(len(before_insert))
                    self.assertTrue(runtime.controller.select_id(entry.id))
                    self.assertTrue(runtime.on_insert())
                    self.assertEqual(win.buffer_text(), before_insert + selected)
                    self.assertTrue(win.modified)
                    self.assertTrue(runtime.on_copy())

                    self.assertTrue(runtime.on_archive())
                    archived = next(
                        item for item in runtime.controller.entries if item.id == entry.id
                    )
                    self.assertEqual(archived.status, "archived")
                    runtime.sync_document(force=True)
                    reloaded = next(
                        item for item in runtime.controller.entries if item.id == entry.id
                    )
                    self.assertEqual(reloaded.status, "archived")

                    print("W91_REAL_APP_CAPTURE_SELECTION=PASS")
                    print("W91_REAL_APP_SECTION_LINK_FILTER_NAVIGATION=PASS")
                    print("W91_REAL_APP_INSERT_COMMAND_GATEWAY=PASS")
                    print("W91_REAL_APP_MARKDOWN_PERSISTENCE=PASS")
                    print("W91_REAL_APP_ARCHIVE_RELOAD=PASS")
                finally:
                    win.destroy()
                    pump()


if __name__ == "__main__":
    unittest.main()
