import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
RENDERER = ROOT / "calamus" / "calamus_appearance.py"
PREFERENCES = ROOT / "calamus" / "calamus_appearance_preferences.py"
GATEWAY = ROOT / "calamus" / "calamus_appearance_gateway.py"


def _method_source(name: str) -> str:
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"method {name!r} not found")


def _module_function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"function {name!r} not found in {path}")


class AppearanceCommandWiringTests(unittest.TestCase):
    def test_visible_commands_remain_in_options_without_cosmetic_recomposition(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('optm = top_menu(app, "Options")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="White Background")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="Dark Mode")', ui)
        self.assertIn('app.appearance_mode == "light"', ui)
        self.assertIn('app.appearance_mode == "dark"', ui)
        self.assertNotIn("Theme Selection", ui)

    def test_startup_has_one_typed_appearance_authority(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("appearance_preference = load_appearance_preference(self.settings)", launcher)
        self.assertIn("self.appearance_mode = appearance_preference.mode", launcher)
        self.assertNotIn('self.white_background = bool(self.settings.get', launcher)
        self.assertNotIn('self.dark_mode = bool(self.settings.get', launcher)
        self.assertNotIn("self.theme_name", launcher)

    def test_dead_legacy_theme_selector_left_the_launcher(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        for name in ("theme_css", "set_theme_name", "on_theme_selection"):
            self.assertNotIn(f"def {name}", launcher)
        self.assertNotIn("Soft Cream", launcher)
        self.assertNotIn("Solarized Dark", launcher)

    def test_settings_write_canonical_state_not_menu_state(self):
        method = _method_source("save_settings")
        self.assertIn("appearance_settings_overrides(self.appearance_mode)", method)
        self.assertNotIn("white_item.get_active", method)
        self.assertNotIn("dark_item.get_active", method)

    def test_request_gateway_left_the_launcher_and_persists_before_render(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotIn("def request_appearance_mode", launcher)
        self.assertNotIn("def sync_appearance_menu_items", launcher)
        gateway = _module_function_source(GATEWAY, "execute_appearance_preference_request")
        self.assertIn("prepare_appearance_preference_plan", gateway)
        self.assertIn("appearance_settings_overrides", gateway)
        self.assertIn("sync_appearance_controls", gateway)
        self.assertLess(gateway.index("host.save_settings"), gateway.index("host.appearance_mode ="))
        self.assertLess(gateway.index("host.appearance_mode ="), gateway.index("host.apply_font"))

    def test_callbacks_are_thin_and_do_not_touch_document_or_undo(self):
        combined = _method_source("on_white_background") + _method_source("on_dark_mode")
        self.assertIn("APPEARANCE_SYSTEM", combined)
        self.assertIn("execute_appearance_preference_request", combined)
        for forbidden in (
            "document",
            "current_file",
            "get_buffer",
            "history",
            "undo",
            "modified",
            "command_layer",
        ):
            self.assertNotIn(forbidden, combined)

    def test_renderer_consumes_one_canonical_mode(self):
        renderer = RENDERER.read_text(encoding="utf-8")
        self.assertIn("appearance_mode: str", renderer)
        self.assertIn("appearance_mode == APPEARANCE_LIGHT", renderer)
        self.assertIn("appearance_mode == APPEARANCE_DARK", renderer)
        self.assertNotIn("white_background: bool", renderer)
        self.assertNotIn("dark_mode: bool", renderer)
        preferences = PREFERENCES.read_text(encoding="utf-8")
        self.assertIn("class AppearancePreference", preferences)
        self.assertIn("class AppearancePreferencePlan", preferences)


if __name__ == "__main__":
    unittest.main()
