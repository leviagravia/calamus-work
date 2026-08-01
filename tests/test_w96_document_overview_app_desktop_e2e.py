"""Real GTK/App proof for W96 Document Overview Core Gate C."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("CALAMUS_SOURCE_ROOT", str(ROOT))
os.environ.setdefault("CALAMUS_LIB_DIR", str(ROOT / "calamus"))

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk
    HAVE_GTK = True
except Exception:
    HAVE_GTK = False


def display_ready():
    if not HAVE_GTK:
        return False
    try:
        result = Gtk.init_check()
    except TypeError:
        result = Gtk.init_check(None)
    ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
    return bool(ok and Gdk.Display.get_default() is not None)


def pump():
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def load_launcher():
    loader = importlib.machinery.SourceFileLoader("calamus_w96_gate_b_app", str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@unittest.skipUnless(
    os.environ.get("CALAMUS_W96_RUN_REAL_GTK") == "1",
    "set CALAMUS_W96_RUN_REAL_GTK=1 for the real W96 GTK lane",
)
class W96DocumentOverviewAppDesktopE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not display_ready():
            raise unittest.SkipTest("GTK display unavailable")
        cls.temp_home = tempfile.TemporaryDirectory(prefix="calamus-w96-gate-c-")
        os.environ["HOME"] = cls.temp_home.name
        os.environ["XDG_CONFIG_HOME"] = str(Path(cls.temp_home.name) / ".config")
        os.environ["XDG_DATA_HOME"] = str(Path(cls.temp_home.name) / ".local/share")
        cls.launcher = load_launcher()

    @classmethod
    def tearDownClass(cls):
        cls.temp_home.cleanup()

    def setUp(self):
        self.app = self.launcher.App()
        self.app.show_all()
        self.app.resize(1100, 760)
        filler = "\n".join(f"Background line {index}." for index in range(1, 121))
        self.text = (
            "# Introduction {#intro}\n"
            "See [Go to Method](#method). Alpha [@missing].\n\n"
            "## Background {#background}\n"
            f"{filler}\n\n"
            "## Method {#method}\nBeta.\n"
        )
        self.app.set_buffer(self.text, modified=True)
        self.app.bookmarks[:] = [self.text.index("Beta")]
        pump()

    def tearDown(self):
        if self.app is not None:
            self.app.destroy()
            pump()
            self.app = None

    def navigate_menu(self):
        for item in self.app.menubar.get_children():
            if item.get_label() == "Navigate":
                return item.get_submenu()
        self.fail("Navigate menu missing")

    def test_real_single_instance_categories_refresh_navigation_and_lifecycle(self):
        items = {item.get_label(): item for item in self.navigate_menu().get_children() if hasattr(item, "get_label")}
        self.assertIn("Document Overview", items)
        items["Document Overview"].activate()
        pump()
        runtime = self.app.document_overview_runtime
        first = runtime.window
        self.assertIsNotNone(first)
        self.assertFalse(first.get_modal())
        self.assertEqual("Document Overview", first.get_title())
        self.assertEqual(
            ["Overview", "Structure", "Research", "Integrity", "Statistics"],
            [row.get_child().get_text().split("  (")[0] for row in runtime._view.category_list.get_children()],
        )
        category_rows = dict(runtime._view._category_rows)
        for category_id in ("structure", "research", "integrity", "statistics", "overview"):
            runtime._view.category_list.select_row(category_rows[category_id])
            pump()
            self.assertEqual(category_id, runtime.selected_category)
            self.assertEqual(category_rows, runtime._view._category_rows)
            self.assertIs(category_rows[category_id], runtime._view.category_list.get_selected_row())
            self.assertIs(runtime._view.category_list, category_rows[category_id].get_parent())

        items["Document Overview"].activate()
        pump()
        self.assertIs(first, runtime.window)

        structure_row = runtime._view._category_rows["structure"]
        runtime._view.category_list.select_row(structure_row)
        pump()
        section_row = next(row for row in runtime._rows if row.kind == "section" and row.payload.id == "method")
        runtime._view.item_list.select_row(runtime._view._item_rows[section_row.id])
        runtime._view.primary_button.clicked()
        pump()
        self.assertEqual(self.text.index("## Method"), self.app.get_cursor_offset())
        self.assertIs(self.app.text, self.app.get_focus())
        self.assertTrue(self.app.get_visible())
        self.assertTrue(self.app.get_mapped())
        self.assertFalse(runtime.window.get_visible())
        self.assertFalse(runtime.window.get_mapped())
        print(f"W96_EDITOR_HANDOFF_WM_ACTIVE_OBSERVATION={int(bool(self.app.is_active()))}")

        items["Document Overview"].activate()
        pump()
        self.assertIs(first, runtime.window)
        self.assertTrue(runtime.window.get_visible())
        runtime._view.category_list.select_row(runtime._view._category_rows["structure"])
        pump()
        link_row = next(row for row in runtime._rows if row.kind == "link" and row.payload.identifier == "method")
        runtime._view.item_list.select_row(runtime._view._item_rows[link_row.id])
        link_start = self.text.index("[Go to Method](#method)")
        link_end = link_start + len("[Go to Method](#method)")
        runtime._view.primary_button.clicked()
        pump()
        selection_start, selection_end = self.app.text.get_buffer().get_selection_bounds()
        self.assertEqual((link_start, link_end), (selection_start.get_offset(), selection_end.get_offset()))
        self.assertIs(self.app.text, self.app.get_focus())
        self.assertTrue(self.app.get_visible())
        self.assertTrue(self.app.get_mapped())
        self.assertFalse(runtime.window.get_visible())
        self.assertFalse(runtime.window.get_mapped())
        print(f"W96_EDITOR_HANDOFF_WM_ACTIVE_OBSERVATION={int(bool(self.app.is_active()))}")

        items["Document Overview"].activate()
        pump()
        self.assertIs(first, runtime.window)
        self.assertTrue(runtime.window.get_visible())
        runtime._view.item_list.select_row(runtime._view._item_rows[link_row.id])
        runtime._view.secondary_button.clicked()
        pump()
        method_offset = self.text.index("## Method")
        self.assertEqual(method_offset, self.app.get_cursor_offset())
        self.assertIs(self.app.text, self.app.get_focus())
        self.assertTrue(self.app.get_visible())
        self.assertTrue(self.app.get_mapped())
        self.assertFalse(runtime.window.get_visible())
        self.assertFalse(runtime.window.get_mapped())
        print(f"W96_EDITOR_HANDOFF_WM_ACTIVE_OBSERVATION={int(bool(self.app.is_active()))}")
        method_iter = self.app.text.get_buffer().get_iter_at_offset(method_offset)
        method_rect = self.app.text.get_iter_location(method_iter)
        visible_rect = self.app.text.get_visible_rect()
        self.assertLess(method_rect.y, visible_rect.y + visible_rect.height)
        self.assertGreaterEqual(method_rect.y + method_rect.height, visible_rect.y)

        items["Document Overview"].activate()
        pump()
        self.assertIs(first, runtime.window)
        self.assertTrue(runtime.window.get_visible())

        notices = []
        runtime._show_notice = notices.append
        structure_row = runtime._view._category_rows["structure"]
        runtime._view.category_list.select_row(structure_row)
        pump()
        first_section = next(row for row in runtime._rows if row.kind == "section")
        runtime._view.item_list.select_row(runtime._view._item_rows[first_section.id])
        before_cursor = self.app.get_cursor_offset()
        before = runtime._controller.refresh_count
        selected_before_stale_action = runtime._selected_item_id
        self.app.text.get_buffer().insert_at_cursor("Changed ")
        pump()
        self.assertEqual(before, runtime._controller.refresh_count)
        self.assertEqual(selected_before_stale_action, runtime._selected_item_id)
        self.assertEqual(
            "Document changed. Overview is stale; no refresh has run yet.",
            runtime._view.status.get_text(),
        )
        runtime._view.primary_button.clicked()
        pump()
        self.assertEqual(before + 1, runtime._controller.refresh_count)
        self.assertEqual(before_cursor + len("Changed "), self.app.get_cursor_offset())
        self.assertIsNone(runtime._selected_item_id)
        self.assertTrue(notices)
        self.assertIn("Action blocked", notices[-1])
        self.assertIn("has now been refreshed", notices[-1])
        self.assertIn("Select the item again", notices[-1])
        self.assertTrue(runtime.snapshot.identity.modified)

        runtime.close()
        pump()
        self.assertFalse(runtime.is_open)
        items["Document Overview"].activate()
        pump()
        self.assertTrue(runtime.is_open)
        self.assertIsNot(first, runtime.window)

        self.app.destroy()
        pump()
        self.assertFalse(runtime.is_open)
        self.app = None

        print("W96_REAL_DOCUMENT_OVERVIEW_MENU=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_SINGLE_INSTANCE=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_FIVE_CATEGORIES=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_NAVIGATION=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_EDITOR_HANDOFF=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_STALE_OBSERVABILITY=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_STALE_ACTION_BLOCK=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_REFRESH=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_CLOSE_REOPEN=PASS")
        print("W96_REAL_DOCUMENT_OVERVIEW_NORMAL_CLOSE=PASS")


if __name__ == "__main__":
    unittest.main()
