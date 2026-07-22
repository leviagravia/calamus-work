import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "calamus" / "calamus_ui.py"


def _build_menu_source() -> str:
    source = UI.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_menu":
            return ast.get_source_segment(source, node) or ""
    raise AssertionError("build_menu not found")


class FavoritesFileMenuWiringTests(unittest.TestCase):
    def test_favorites_is_not_a_top_level_menu_anymore(self):
        source = _build_menu_source()
        self.assertNotIn('top_menu(app, "Favourites")', source)
        self.assertNotIn('top_menu(app, "Favorites")', source)

    def test_file_owns_a_favorites_submenu_with_normative_spelling(self):
        source = _build_menu_source()
        self.assertIn('filem = top_menu(app, "File")', source)
        self.assertIn('app.favourites_item = Gtk.MenuItem(label="Favorites")', source)
        self.assertIn('app.favourites_item.set_submenu(favm)', source)
        self.assertIn('filem.append(app.favourites_item)', source)
        self.assertIn('app.favourites_menu = favm', source)

    def test_favorites_occupies_the_current_file_lifecycle_slot(self):
        source = _build_menu_source()
        save_as = source.index('add_item(filem, "Save As…\\tCtrl+Shift+S", app.on_save_as)')
        favorite = source.index('app.favourites_item = Gtk.MenuItem(label="Favorites")')
        print_preview = source.index('add_item(filem, "Print Preview…\\tCtrl+Shift+P", app.on_print_preview)')
        self.assertLess(save_as, favorite)
        self.assertLess(favorite, print_preview)

    def test_existing_visible_favorite_commands_and_callbacks_are_preserved(self):
        source = _build_menu_source()
        expected = (
            'add_item(favm, "Add to Favourites\\tCtrl+Alt+B", app.on_add_favourite)',
            'add_item(favm, "Edit Favourites…\\tCtrl+Shift+D", app.on_edit_favourites)',
            'add_item(favm, "Reload Favourites\\tCtrl+Alt+R", app.on_reload_favourites)',
        )
        for line in expected:
            self.assertIn(line, source)

    def test_dynamic_population_still_targets_the_same_owned_submenu(self):
        source = _build_menu_source()
        assignment = source.index('app.favourites_menu = favm')
        population = source.index('app.populate_favourites_menu()')
        self.assertLess(assignment, population)

    def test_w57_does_not_invent_absent_final_commands(self):
        source = _build_menu_source()
        for absent in (
            "Open Favorite…",
            "Remove Current File from Favorites",
            "Manage Favorites…",
            "Save a Copy…",
            "Revert to Saved",
            "Export as PDF…",
        ):
            self.assertNotIn(absent, source)

    def test_top_level_menu_sequence_has_no_favorites_entry(self):
        source = _build_menu_source()
        tree = ast.parse(source)
        labels = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "top_menu":
                continue
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                labels.append(node.args[1].value)
        self.assertEqual(labels, ["File", "Edit", "Research", "Navigate", "Revise", "View", "Options", "Tools", "Help"])


if __name__ == "__main__":
    unittest.main()
