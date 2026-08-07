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
        self.assertIn("command_shortcut_bindings()", source)
        self.assertIn("command_shortcut_bindings()", source)
        self.assertIn("command_shortcut_bindings()", source)

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

    def test_bookmarks_keep_callbacks_but_move_to_navigate_in_w95extra(self):
        model=(ROOT/'calamus/calamus_menu_model.py').read_text(encoding='utf-8')
        block=model[model.index('MenuSpec("Navigate"'):model.index('MenuSpec("Writing"')]
        for cid in ('navigate.bookmark.toggle','navigate.bookmark.next','navigate.bookmark.previous','navigate.bookmark.manage'):
            self.assertIn(cid,block)
        revise=model[model.index('MenuSpec("Revise"'):model.index('MenuSpec("View"')]
        self.assertNotIn('navigate.bookmark.toggle',revise)

    def test_recent_files_remains_a_separate_file_submenu(self):
        model=(ROOT/'calamus/calamus_menu_model.py').read_text(encoding='utf-8')
        file_block=model[model.index('MenuSpec("File"'):model.index('MenuSpec("Edit"')]
        self.assertIn('_m("Recent Files", _d("recent-files"))',file_block)
        self.assertIn('_m("Favorites"',file_block)
        self.assertNotEqual(file_block.index('Recent Files'),file_block.index('Favorites'))

    def test_favorites_internal_attribute_names_are_not_cosmetically_churned(self):
        model=(ROOT/'calamus/calamus_menu_model.py').read_text(encoding='utf-8')
        self.assertIn('_d("favourites")',model)
        self.assertNotIn('_d("favorites")',model)
        launcher=LAUNCHER.read_text(encoding='utf-8')
        self.assertIn('populate_favourites_menu',launcher)


if __name__ == "__main__":
    unittest.main()
