import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "calamus" / "calamus_ui.py"
LAUNCHER = ROOT / "bin" / "calamus"


def _function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"function {name!r} not found in {path}")


class FavoritesFileMenuInvariantTests(unittest.TestCase):
    def test_shortcut_bindings_are_unchanged(self):
        source = _function_source(UI, "shortcut_bindings")
        self.assertIn('("<Control><Alt>B", app.on_add_favourite)', source)
        self.assertIn('("<Control><Shift>D", app.on_edit_favourites)', source)
        self.assertIn('("<Control><Alt>R", app.on_reload_favourites)', source)

    def test_domain_callbacks_do_not_depend_on_menu_parentage(self):
        for name in (
            "open_favourite_path",
            "on_add_favourite",
            "apply_favourite_edits",
            "on_edit_favourites",
            "on_reload_favourites",
            "populate_favourites_menu",
        ):
            source = _function_source(LAUNCHER, name)
            self.assertNotIn("filem", source)
            self.assertNotIn("menubar", source)
            self.assertNotIn("top_menu", source)

    def test_bookmarks_are_not_moved_or_rewired_by_w57(self):
        source = _function_source(UI, "build_menu")
        self.assertIn('add_item(revisem, "Insert Bookmark Here\\tCtrl+F2", app.toggle_bookmark)', source)
        self.assertIn('add_item(revisem, "Next Bookmark\\tF2", app.next_bookmark)', source)
        self.assertIn('add_item(revisem, "Previous Bookmark\\tShift+F2", app.previous_bookmark)', source)
        self.assertIn('add_item(revisem, "Manage Bookmarks…", app.on_manage_bookmarks)', source)

    def test_recent_files_remains_a_separate_file_submenu(self):
        source = _function_source(UI, "build_menu")
        self.assertIn('app.recent_item = Gtk.MenuItem(label="Recent Files")', source)
        self.assertIn('app.recent_item.set_submenu(app.recent_menu)', source)
        self.assertIn('filem.append(app.recent_item)', source)
        self.assertNotIn('app.recent_item.set_submenu(favm)', source)

    def test_favorites_internal_attribute_names_are_not_cosmetically_churned(self):
        source = _function_source(UI, "build_menu")
        self.assertIn("app.favourites_item", source)
        self.assertIn("app.favourites_menu", source)
        self.assertNotIn("app.favorites_menu", source)


if __name__ == "__main__":
    unittest.main()
