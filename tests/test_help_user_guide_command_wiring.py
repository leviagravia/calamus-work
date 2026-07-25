import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "bin/calamus").read_text(encoding="utf-8")
UI = (ROOT / "calamus/calamus_ui.py").read_text(encoding="utf-8")
SHORTCUTS = (ROOT / "calamus/calamus_shortcuts.py").read_text(encoding="utf-8")
PROVENANCE = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")


class UserGuideCommandWiringTests(unittest.TestCase):
    def test_help_menu_exposes_one_user_guide_command(self):
        line = 'add_item(helpm, "User Guide…", app.on_user_guide)'
        self.assertEqual(UI.count(line), 1)
        self.assertIn('ShortcutSpec("Help", "User Guide", "menu")', SHORTCUTS)

    def test_app_gateway_only_loads_and_shows_guide(self):
        tree = ast.parse(APP)
        app_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "App")
        method = next(node for node in app_class.body if isinstance(node, ast.FunctionDef) and node.name == "on_user_guide")
        source = ast.get_source_segment(APP, method)
        self.assertIn("show_user_guide(self, load_user_guide())", source)
        self.assertNotIn("Gtk.", source)
        self.assertLessEqual(method.end_lineno - method.lineno + 1, 3)

    def test_help_modules_and_canonical_file_are_provenance_visible(self):
        for module in ("calamus_help", "calamus_help_dialogs"):
            path = ROOT / "calamus" / f"{module}.py"
            self.assertTrue(path.is_file())
            ast.parse(path.read_text(encoding="utf-8"))
            self.assertIn(f'"{module}"', PROVENANCE)
        guide = ROOT / "share/doc/calamus/USER_GUIDE.md"
        self.assertTrue(guide.is_file())
        self.assertGreater(guide.stat().st_size, 3000)


if __name__ == "__main__":
    unittest.main()
