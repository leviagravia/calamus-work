import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"


def _method_source(name: str) -> str:
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"method {name!r} not found")


class FavoriteReloadCommandWiringTests(unittest.TestCase):
    def test_visible_menu_and_shortcut_remain_unchanged(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(favm, "Reload Favourites\\tCtrl+Alt+R", app.on_reload_favourites)',
            ui,
        )
        self.assertIn('("<Control><Alt>R", app.on_reload_favourites)', ui)

    def test_reload_is_a_compatibility_callback_not_a_new_domain_plan(self):
        method = _method_source("on_reload_favourites")
        self.assertIn("self.populate_favourites_menu()", method)
        self.assertIn("return True", method)
        for forbidden in (
            "prepare_",
            "save_favourites",
            "load_favourite_store",
            "open_favourite_path",
            "open_recent_path",
            "CommandContext",
            "command_layer",
        ):
            self.assertNotIn(forbidden, method)

    def test_menu_population_tracks_owned_dynamic_items_not_fixed_positions(self):
        method = _method_source("populate_favourites_menu")
        self.assertIn('getattr(self, "_favourite_dynamic_items", ())', method)
        self.assertIn("self._favourite_dynamic_items = dynamic_items", method)
        self.assertNotIn("children[4:]", method)
        self.assertNotIn("Keep the first 4 fixed entries", method)

    def test_reload_does_not_mutate_favorites_store_or_document_state(self):
        method = _method_source("on_reload_favourites")
        for forbidden in (
            "save_favourites",
            "save_settings",
            "current_file",
            "document",
            "buffer",
            "history",
            "undo",
            "modified",
            "error(",
            "info(",
        ):
            self.assertNotIn(forbidden, method)

    def test_other_favorite_commands_are_not_rerouted_through_reload(self):
        for name in (
            "open_favourite_path",
            "on_add_favourite",
            "apply_favourite_edits",
            "on_edit_favourites",
        ):
            self.assertNotIn("on_reload_favourites", _method_source(name))


if __name__ == "__main__":
    unittest.main()
