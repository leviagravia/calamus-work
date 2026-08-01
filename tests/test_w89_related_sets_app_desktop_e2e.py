"""Real GTK and real App proofs for W89 Related References and Reference Sets.

These tests are intentionally excluded from focused/headless gates.  Each modal
workflow has a bounded driver, semantic widget lookup, and unconditional dialog
cleanup so an assertion cannot strand Gtk.Dialog.run() or the test process.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import textwrap
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

from tests.calamus_gtk_test_driver import (
    HAVE_GTK,
    Gtk,
    ModalDriver,
    close_visible_dialogs,
    dialog_text,
    display_ready,
    named_widget,
    pump,
    visible_dialog,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_REAL_GTK = os.environ.get("CALAMUS_W89_RUN_REAL_GTK") == "1"
# Required lifecycle markers: W89_REAL_LIFECYCLE_DELETE=PASS and W89_REAL_LIFECYCLE_QUIT=PASS.


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w89_app_{uuid.uuid4().hex}"
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


def _records(*, related: bool = False):
    from calamus_references import ReferenceRecord
    from calamus_related_references import with_related_keys

    a = ReferenceRecord(key="a", title="Alpha", authors=("Author, A",), year="2020")
    b = ReferenceRecord(key="b", title="Beta", authors=("Author, B",), year="2021")
    c = ReferenceRecord(key="c", title="Gamma", authors=("Author, C",), year="2022")
    if related:
        a = with_related_keys(a, ("b",))
        b = with_related_keys(b, ("a",))
    return (a, b, c)


def _prepare_references(*, related: bool = False) -> Path:
    from calamus_reference_store import MarkdownReferenceStore

    store = MarkdownReferenceStore()
    snapshot = store.load()
    result = store.save(_records(related=related), snapshot.token)
    if not result.saved:
        raise AssertionError(result.message)
    return Path(store.path)


def _prepare_reference_sets() -> Path:
    from calamus_reference_set_store import MarkdownReferenceSetStore
    from calamus_reference_sets import ReferenceSet

    store = MarkdownReferenceSetStore()
    snapshot = store.load()
    result = store.save(
        (ReferenceSet("Core sources", "Primary works", ("a", "b")),),
        snapshot.token,
    )
    if not result.saved:
        raise AssertionError(result.message)
    return Path(store.path)


def _environment(root: Path) -> dict[str, str]:
    return {
        "HOME": str(root),
        "XDG_DATA_HOME": str(root / "data"),
        "XDG_CONFIG_HOME": str(root / "config"),
    }


def _lifecycle_child_script() -> str:
    return textwrap.dedent(
        r"""
        from __future__ import annotations
        import importlib.machinery
        import importlib.util
        import os
        from pathlib import Path
        import sys
        import uuid

        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        gi.require_version("Pango", "1.0")
        gi.require_version("PangoCairo", "1.0")
        from gi.repository import GLib, Gtk

        root = Path(os.environ["CALAMUS_SOURCE_ROOT"])
        os.environ["CALAMUS_LIB_DIR"] = str(root / "calamus")
        sys.path.insert(0, str(root / "calamus"))
        name = f"calamus_w89_lifecycle_{uuid.uuid4().hex}"
        loader = importlib.machinery.SourceFileLoader(name, str(root / "bin/calamus"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)

        win = module.App()
        win.show_all()
        mode = os.environ["CALAMUS_W89_LIFECYCLE_MODE"]
        timed_out = {"value": False}

        def request_close():
            if mode == "delete":
                win.close()
            elif mode == "quit":
                win.on_quit()
            else:
                raise RuntimeError(f"unknown lifecycle mode: {mode}")
            return False

        def watchdog():
            timed_out["value"] = True
            for window in Gtk.Window.list_toplevels():
                try:
                    window.destroy()
                except Exception:
                    pass
            if Gtk.main_level() > 0:
                Gtk.main_quit()
            return False

        GLib.timeout_add(120, request_close)
        GLib.timeout_add(5000, watchdog)
        Gtk.main()
        if timed_out["value"]:
            raise SystemExit(90)
        visible = [window for window in Gtk.Window.list_toplevels() if window.get_visible()]
        if visible:
            raise SystemExit(91)
        print(f"W89_REAL_LIFECYCLE_{mode.upper()}=PASS")
        """
    )


@unittest.skipUnless(
    HAVE_GTK and RUN_REAL_GTK,
    "W89 real GTK gate disabled or PyGObject unavailable",
)
class W89RealAppDesktopE2E(unittest.TestCase):
    def setUp(self) -> None:
        if not display_ready():
            self.skipTest("GTK display unavailable")

    def test_real_related_dialog_symmetric_write_and_bridge_navigation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, _environment(root), clear=False):
                _set_isolated_config(root)
                references_path = _prepare_references()
                module = _load_app_module()
                win = module.App()
                try:
                    win.show_all()
                    pump()
                    win.reference_panel_runtime.controller.ensure_loaded()
                    self.assertTrue(win.reference_panel_runtime.controller.select_key("a"))

                    def select_relation() -> bool:
                        dialog = visible_dialog("Related References — a")
                        if dialog is None:
                            return False
                        check = named_widget(dialog, "related-reference-b", Gtk.CheckButton)
                        self.assertFalse(check.get_active())
                        check.set_active(True)
                        dialog.response(Gtk.ResponseType.OK)
                        return True

                    def confirm_impact() -> bool:
                        dialog = visible_dialog("Related References Impact")
                        if dialog is None:
                            return False
                        rendered = dialog_text(dialog)
                        self.assertIn("Add: b", rendered)
                        self.assertIn("Reference records updated: 2", rendered)
                        dialog.response(Gtk.ResponseType.OK)
                        return True

                    driver = ModalDriver([select_relation, confirm_impact])
                    driver.start()
                    self.assertTrue(win.reference_panel_runtime.on_related_references())
                    pump()
                    driver.assert_complete()

                    from calamus_reference_store import parse_references_markdown
                    from calamus_related_references import related_keys

                    records, diagnostics = parse_references_markdown(
                        references_path.read_text(encoding="utf-8")
                    )
                    self.assertEqual(diagnostics, ())
                    by_key = {record.key: record for record in records}
                    self.assertEqual(related_keys(by_key["a"]), ("b",))
                    self.assertEqual(related_keys(by_key["b"]), ("a",))
                    print("W89_REAL_RELATED_DIALOG=PASS")
                    print("W89_REAL_SYMMETRIC_REFERENCES_WRITE=PASS")

                    self.assertTrue(win.show_authoring_bridge())
                    bridge = win.authoring_bridge_runtime
                    bridge._view._mode_selector.set_active_id("related")
                    pump()
                    bridge._view._subject_selector.set_active_id("a")
                    pump()
                    occurrence = bridge.controller.visible_occurrences[0]
                    self.assertEqual(occurrence.reference_key, "b")
                    bridge._view.select_occurrence_id(occurrence.id)
                    self.assertTrue(bridge.on_open())
                    self.assertEqual(win.research_panel_runtime.active_client, "references")
                    self.assertEqual(win.reference_panel_runtime.selected_key, "b")
                    print("W89_REAL_RELATED_BRIDGE_NAVIGATION=PASS")
                finally:
                    close_visible_dialogs()
                    win.destroy()
                    pump()

    def test_real_reference_set_dialog_markdown_and_navigation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, _environment(root), clear=False):
                _set_isolated_config(root)
                _prepare_references()
                module = _load_app_module()
                win = module.App()
                try:
                    win.show_all()
                    pump()
                    self.assertTrue(win.show_reference_sets())
                    pump()

                    def create_set() -> bool:
                        dialog = visible_dialog("Add Reference Set")
                        if dialog is None:
                            return False
                        named_widget(dialog, "reference-set-name", Gtk.Entry).set_text(
                            "Core sources"
                        )
                        named_widget(
                            dialog, "reference-set-description", Gtk.Entry
                        ).set_text("Primary works")
                        named_widget(
                            dialog, "reference-set-member-a", Gtk.CheckButton
                        ).set_active(True)
                        named_widget(
                            dialog, "reference-set-member-b", Gtk.CheckButton
                        ).set_active(True)
                        dialog.response(Gtk.ResponseType.OK)
                        return True

                    driver = ModalDriver([create_set])
                    driver.start()
                    self.assertTrue(win.reference_set_runtime.on_add())
                    pump()
                    driver.assert_complete()

                    from calamus_reference_set_store import MarkdownReferenceSetStore

                    snapshot = MarkdownReferenceSetStore().load()
                    self.assertEqual(snapshot.diagnostics, ())
                    self.assertEqual(len(snapshot.sets), 1)
                    self.assertEqual(snapshot.sets[0].name, "Core sources")
                    self.assertEqual(snapshot.sets[0].members, ("a", "b"))
                    self.assertEqual(
                        Path(MarkdownReferenceSetStore().path)
                        .read_text(encoding="utf-8")
                        .splitlines()[2],
                        "## Core sources",
                    )
                    view = win.reference_set_runtime._view
                    self.assertTrue(view.select_member_key("b"))
                    self.assertTrue(win.reference_set_runtime.on_open())
                    self.assertEqual(win.research_panel_runtime.active_client, "references")
                    self.assertEqual(win.reference_panel_runtime.selected_key, "b")
                    print("W89_REAL_REFERENCE_SET_DIALOG=PASS")
                    print("W89_REAL_REFERENCE_SET_MARKDOWN=PASS")
                    print("W89_REAL_REFERENCE_SET_CASE_PRESERVATION=PASS")
                    print("W89_REAL_REFERENCE_SET_NAVIGATION=PASS")
                finally:
                    close_visible_dialogs()
                    win.destroy()
                    pump()


    def test_real_rename_impact_dialog_and_four_authorities(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, _environment(root), clear=False):
                _set_isolated_config(root)
                references_path = _prepare_references(related=True)
                _prepare_reference_sets()
                document = root / "article.md"
                document.write_text(
                    "# Article {#article}\n\nCompare [@b, p. 10].\n",
                    encoding="utf-8",
                )
                module = _load_app_module()
                win = module.App()
                try:
                    win.show_all()
                    pump()
                    self.assertTrue(win.open_path(str(document), silent=True))
                    win.reference_panel_runtime.controller.ensure_loaded()
                    self.assertTrue(win.reference_panel_runtime.controller.select_key("b"))

                    def fill_request() -> bool:
                        dialog = visible_dialog("Rename Reference Key")
                        if dialog is None:
                            return False
                        current = named_widget(
                            dialog, "rename-reference-current-key", Gtk.ComboBoxText
                        )
                        self.assertTrue(current.set_active_id("b"))
                        named_widget(
                            dialog, "rename-reference-new-key", Gtk.Entry
                        ).set_text("b-revised")
                        preserve = named_widget(
                            dialog,
                            "rename-reference-preserve-alias",
                            Gtk.CheckButton,
                        )
                        self.assertTrue(preserve.get_active())
                        dialog.response(Gtk.ResponseType.OK)
                        return True

                    def confirm_impact() -> bool:
                        dialog = visible_dialog("Rename Reference Key Impact")
                        if dialog is None:
                            return False
                        rendered = dialog_text(dialog)
                        self.assertIn("Related-key occurrences: 1", rendered)
                        self.assertIn("Reference Set memberships: 1", rendered)
                        dialog.response(Gtk.ResponseType.OK)
                        return True

                    def close_result() -> bool:
                        dialog = visible_dialog("Reference key renamed")
                        if dialog is None:
                            return False
                        self.assertIn("renamed", dialog_text(dialog).casefold())
                        dialog.response(Gtk.ResponseType.OK)
                        return True

                    driver = ModalDriver(
                        [fill_request, confirm_impact, close_result],
                        timeout_seconds=12.0,
                    )
                    driver.start()
                    self.assertTrue(win.on_rename_reference_key())
                    pump()
                    driver.assert_complete()

                    from calamus_reference_set_store import MarkdownReferenceSetStore
                    from calamus_reference_store import parse_references_markdown
                    from calamus_related_references import related_keys

                    records, diagnostics = parse_references_markdown(
                        references_path.read_text(encoding="utf-8")
                    )
                    self.assertEqual(diagnostics, ())
                    by_key = {record.key: record for record in records}
                    self.assertEqual(by_key["b-revised"].aliases, ("b",))
                    self.assertEqual(related_keys(by_key["a"]), ("b-revised",))
                    self.assertEqual(related_keys(by_key["b-revised"]), ("a",))
                    set_snapshot = MarkdownReferenceSetStore().load()
                    self.assertEqual(set_snapshot.sets[0].members, ("a", "b-revised"))
                    self.assertIn("[@b-revised, p. 10]", win.buffer_text())
                    print("W89_REAL_RENAME_IMPACT_DIALOG=PASS")
                    print("W89_REAL_RENAME_FOUR_AUTHORITIES=PASS")
                finally:
                    close_visible_dialogs()
                    win.destroy()
                    pump()

    def test_real_normal_close_lifecycle_exits_main_loop_and_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for mode in ("delete", "quit"):
                with self.subTest(mode=mode):
                    env = os.environ.copy()
                    env.update(_environment(root / mode))
                    env.update(
                        {
                            "CALAMUS_SOURCE_ROOT": str(ROOT),
                            "CALAMUS_LIB_DIR": str(ROOT / "calamus"),
                            "CALAMUS_W89_LIFECYCLE_MODE": mode,
                            "PYTHONDONTWRITEBYTECODE": "1",
                        }
                    )
                    result = subprocess.run(
                        [sys.executable, "-B", "-c", _lifecycle_child_script()],
                        cwd=ROOT,
                        env=env,
                        text=True,
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                    self.assertEqual(
                        result.returncode,
                        0,
                        msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
                    )
                    marker = f"W89_REAL_LIFECYCLE_{mode.upper()}=PASS"
                    self.assertIn(marker, result.stdout)
                    print(marker)


if __name__ == "__main__":
    unittest.main()
