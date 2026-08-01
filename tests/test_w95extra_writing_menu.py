from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "calamus" / "calamus_ui.py"
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
        source = UI.read_text(encoding="utf-8")
        roots = [node.args[1].value for node in ast.walk(ast.parse(source))
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == "top_menu" and len(node.args) > 1
                 and isinstance(node.args[1], ast.Constant)]
        self.assertIn("Writing", roots)
        self.assertLess(roots.index("Navigate"), roots.index("Writing"))
        self.assertLess(roots.index("Writing"), roots.index("Revise"))

    def test_writing_menu_is_exactly_the_authorized_initial_surface(self):
        source = UI.read_text(encoding="utf-8")
        start = source.index('writingm = top_menu(app, "Writing")')
        end = source.index('revisem = top_menu(app, "Revise")')
        menu = source[start:end]
        for label in (
            "Typewriter Mode\\tShift+F9",
            "Insert Date",
            "Insert Time",
            "Insert Date and Time\\tCtrl+Alt+D",
        ):
            self.assertIn(label, menu)
        for forbidden in ("Focus Mode", "Distraction-Free Mode", "Word Count", "Statistics"):
            self.assertNotIn(forbidden, menu)
        self.assertEqual(menu.count("add_item(writingm"), 3)
        self.assertEqual(menu.count("Gtk.CheckMenuItem"), 1)

    def test_menu_taxonomy_is_unambiguous_and_duplicate_free(self):
        source = UI.read_text(encoding="utf-8")
        navigate = source[source.index('navigatem = top_menu(app, "Navigate")'):source.index('writingm = top_menu(app, "Writing")')]
        writing = source[source.index('writingm = top_menu(app, "Writing")'):source.index('revisem = top_menu(app, "Revise")')]
        revise = source[source.index('revisem = top_menu(app, "Revise")'):source.index('viewm = top_menu(app, "View")')]
        for label in ("Insert Bookmark Here", "Next Bookmark", "Previous Bookmark", "Manage Bookmarks"):
            self.assertIn(label, navigate)
            self.assertNotIn(label, revise)
        for label in ("Insert Date", "Insert Time", "Insert Date and Time"):
            self.assertIn(label, writing)
            self.assertNotIn(label, revise)
        for label in ("Paste Clean from PDF", "Clean Selected Text from PDF"):
            self.assertIn(label, revise)
            self.assertNotIn(label, writing)

    def test_typewriter_is_checked_and_shortcut_is_unique(self):
        source = UI.read_text(encoding="utf-8")
        self.assertIn('app.typewriter_item = Gtk.CheckMenuItem(label="Typewriter Mode\\tShift+F9")', source)
        self.assertIn('("<Shift>F9", app.toggle_typewriter_mode)', source)
        self.assertEqual(source.count("<Shift>F9"), 1)
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("on_typewriter_item_toggled", launcher)
        self.assertIn("typewriter_runtime.shutdown()", launcher)


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
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W96"', version)
        self.assertIn(
            'DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Document Overview Core — Gate C"',
            version,
        )
        self.assertIn("792ca0f76db39525a9052bd61e43fe929988af2e", version)


if __name__ == "__main__":
    unittest.main()
