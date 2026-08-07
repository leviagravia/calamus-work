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
        from calamus_menu_model import TOP_LEVEL_MENU_ORDER
        self.assertNotIn('Favorites',TOP_LEVEL_MENU_ORDER); self.assertNotIn('Favourites',TOP_LEVEL_MENU_ORDER)

    def test_file_owns_a_favorites_submenu_with_normative_spelling(self):
        source=(ROOT/'calamus/calamus_menu_model.py').read_text(encoding='utf-8')
        block=source[source.index('MenuSpec("File"'):source.index('MenuSpec("Edit"')]
        self.assertIn('_m("Favorites"',block); self.assertIn('_d("favourites")',block)

    def test_favorites_occupies_the_current_file_lifecycle_slot(self):
        source=(ROOT/'calamus/calamus_menu_model.py').read_text(encoding='utf-8')
        block=source[source.index('MenuSpec("File"'):source.index('MenuSpec("Edit"')]
        self.assertLess(block.index('file.save-as'),block.index('_m("Favorites"'))
        self.assertLess(block.index('_m("Favorites"'),block.index('file.print-preview'))

    def test_existing_visible_favorite_commands_and_callbacks_are_preserved(self):
        source=(ROOT/'calamus/calamus_menu_model.py').read_text(encoding='utf-8')
        for cid,label in (('file.favourite.add','Add to Favourites'),('file.favourite.edit','Edit Favourites…'),('file.favourite.reload','Reload Favourites')):
            self.assertIn(cid,source); self.assertIn(label,source)

    def test_dynamic_population_still_targets_the_same_owned_submenu(self):
        launcher=(ROOT/'bin/calamus').read_text(encoding='utf-8')
        self.assertIn('adapter.render_dynamic("favourites", favourite_rows(items))',launcher)
        ui=(ROOT/'calamus/calamus_ui.py').read_text(encoding='utf-8')
        self.assertIn('self._dynamic_menus',ui); self.assertIn('render_dynamic',ui)

    def test_w57_does_not_invent_absent_final_commands(self):
        source=(ROOT/'calamus/calamus_menu_model.py').read_text(encoding='utf-8')
        for absent in ('Open Favorite…','Remove Current File from Favorites','Manage Favorites…','Save a Copy…','Revert to Saved','Export as PDF…'):
            self.assertNotIn(absent,source)

    def test_top_level_menu_sequence_has_no_favorites_entry(self):
        from calamus_menu_model import TOP_LEVEL_MENU_ORDER
        self.assertEqual(TOP_LEVEL_MENU_ORDER,('File','Edit','Research','Navigate','Writing','Revise','View','Options','Tools','Help'))


if __name__ == "__main__":
    unittest.main()
