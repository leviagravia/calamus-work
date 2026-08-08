from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "calamus" / "calamus_ui.py"
MENU_MODEL = ROOT / "calamus" / "calamus_menu_model.py"
LAUNCHER = ROOT / "bin" / "calamus"
GUIDE = ROOT / "share" / "doc" / "calamus" / "USER_GUIDE.md"
VERSION = ROOT / "calamus" / "calamus_version.py"
VIEWPORT_POLICY = ROOT / "calamus" / "calamus_viewport.py"
TYPEWRITER_POLICY = ROOT / "calamus" / "calamus_typewriter.py"
VIEWPORT_RUNTIME = ROOT / "calamus" / "calamus_viewport_runtime.py"
TYPEWRITER_RUNTIME = ROOT / "calamus" / "calamus_typewriter_runtime.py"
HISTORY_RUNTIME = ROOT / "calamus" / "calamus_history_runtime.py"


class W95ExtraWritingMenuTests(unittest.TestCase):
    def test_top_level_order_contains_bounded_writing_menu(self):
        from calamus_menu_model import TOP_LEVEL_MENU_ORDER
        self.assertEqual(TOP_LEVEL_MENU_ORDER, ("File", "Edit", "Research", "Navigate", "Writing", "Revise", "View", "Options", "Tools", "Help"))

    def test_writing_menu_is_exactly_the_authorized_initial_surface(self):
        source=MENU_MODEL.read_text(encoding="utf-8")
        menu=source[source.index('MenuSpec("Writing"'):source.index('MenuSpec("Revise"')]
        for label in ("Typewriter Mode\\tShift+F9", "Insert Date", "Insert Time", "Insert Date and Time\\tCtrl+Alt+D"):
            self.assertIn(label, menu)
        for forbidden in ("Focus Mode", "Distraction-Free Mode", "Word Count", "Statistics"):
            self.assertNotIn(forbidden, menu)
        self.assertEqual(menu.count('_c("writing.insert-'), 3)
        self.assertEqual(menu.count('_k("writing.typewriter-mode"'), 1)

    def test_menu_taxonomy_is_unambiguous_and_duplicate_free(self):
        source=MENU_MODEL.read_text(encoding="utf-8")
        navigate=source[source.index('MenuSpec("Navigate"'):source.index('MenuSpec("Writing"')]
        writing=source[source.index('MenuSpec("Writing"'):source.index('MenuSpec("Revise"')]
        revise=source[source.index('MenuSpec("Revise"'):source.index('MenuSpec("View"')]
        for label in ("Insert Bookmark Here", "Next Bookmark", "Previous Bookmark", "Manage Bookmarks"):
            self.assertIn(label,navigate); self.assertNotIn(label,revise)
        for label in ("Insert Date", "Insert Time", "Insert Date and Time"):
            self.assertIn(label,writing); self.assertNotIn(label,revise)
        for label in ("Paste Clean from PDF", "Clean Selected Text from PDF"):
            self.assertIn(label,revise); self.assertNotIn(label,writing)

    def test_typewriter_is_checked_and_shortcut_is_unique(self):
        source=MENU_MODEL.read_text(encoding="utf-8")
        self.assertIn('writing.typewriter-mode', source)
        self.assertIn('Typewriter Mode\\tShift+F9', source)
        self.assertIn("command_shortcut_bindings()", UI.read_text(encoding="utf-8"))
        from tests.w104_command_test_support import actual_binding_has
        self.assertTrue(actual_binding_has("writing.typewriter-mode", "<Shift>F9"))
        launcher=LAUNCHER.read_text(encoding="utf-8")
        lifecycle=(ROOT/"calamus/calamus_application_lifecycle_app.py").read_text(encoding="utf-8")
        self.assertIn("on_typewriter_item_toggled", launcher)
        self.assertIn("typewriter_shutdown=self.typewriter_runtime.shutdown", launcher)
        self.assertIn('register_final("typewriter", typewriter_shutdown)', lifecycle)


    def test_geometry_policy_is_gtk_free_and_projection_has_one_runtime_writer(self):
        for path in (VIEWPORT_POLICY, TYPEWRITER_POLICY):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("import gi", source)
            self.assertNotIn("from gi.repository", source)
            self.assertNotIn("Gtk.", source)
        viewport = VIEWPORT_RUNTIME.read_text(encoding="utf-8")
        typewriter = TYPEWRITER_RUNTIME.read_text(encoding="utf-8")
        history = HISTORY_RUNTIME.read_text(encoding="utf-8")
        self.assertEqual(viewport.count("._adjustment.set_value("), 1)
        self.assertNotIn(".set_value(", typewriter)
        self.assertNotIn(".set_value(", history)
        combined = "\n".join((viewport, typewriter))
        for forbidden in ("timeout_add", "scroll_to_mark", "scroll_to_iter", "time.sleep"):
            self.assertNotIn(forbidden, combined)
        self.assertIn("Do not queue a resize here", viewport)

    def test_help_and_identity_are_truthful(self):
        guide = GUIDE.read_text(encoding="utf-8")
        self.assertIn("### Writing", guide)
        for label in ("Typewriter Mode", "Insert Date", "Insert Time", "Insert Date and Time"):
            self.assertIn(label, guide)
        self.assertIn("## Typewriter Mode", guide)
        version = VERSION.read_text(encoding="utf-8")
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W108"', version)
        self.assertIn(
            'DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Thin GTK Shell"',
            version,
        )
        self.assertIn("e16cc21b8a900298406ae8cc4776f6f1ec658e93", version)


if __name__ == "__main__":
    unittest.main()
