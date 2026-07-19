import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
PREFERENCE = ROOT / "calamus" / "calamus_opacity.py"
GATEWAY = ROOT / "calamus" / "calamus_opacity_gateway.py"


def _method_source(name: str) -> str:
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"method {name!r} not found")


def _function_source(path: Path, name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"function {name!r} not found in {path}")


class OpacityCommandWiringTests(unittest.TestCase):
    def test_startup_has_one_typed_opacity_authority(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("opacity_preference = load_opacity_preference(self.settings)", launcher)
        self.assertIn("self.opacity_percent = opacity_preference.percent", launcher)
        self.assertIn("self._opacity_widget_api = Gtk.Widget", launcher)
        self.assertNotIn('clamp_int(self.settings.get("opacity")', launcher)
        self.assertNotIn("self.set_opacity(", launcher)
        self.assertNotIn("self.get_opacity(", launcher)

    def test_settings_write_canonical_state_not_runtime_widget(self):
        method = _method_source("save_settings")
        self.assertIn("opacity_settings_overrides(self.opacity_percent)", method)
        self.assertNotIn("get_opacity", method)
        self.assertNotIn("transparent_item.get_active", method)

    def test_visible_command_and_fixed_values_share_gateway(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('Gtk.CheckMenuItem(label="Transparent Mode\\tCtrl+Shift+T")', ui)
        self.assertIn("app.opacity_percent < 100", ui)
        self.assertIn("app.set_opacity_value(val)", ui)
        setter = _method_source("set_opacity_value")
        self.assertIn("execute_opacity_preference_request", setter)
        self.assertNotIn("save_settings", setter)
        self.assertNotIn("self.set_opacity(", setter)

    def test_transparent_callback_is_thin_and_document_independent(self):
        callback = _method_source("on_transparent_mode")
        self.assertIn("_syncing_opacity_item", callback)
        self.assertIn("execute_transparent_mode_request", callback)
        self.assertIn("execute_transparent_mode_request", callback)
        for forbidden in (
            "document",
            "current_file",
            "get_buffer",
            "history",
            "undo",
            "modified",
            "command_layer",
            "settings.get",
        ):
            self.assertNotIn(forbidden, callback)

    def test_gateway_persists_before_adapter_and_commit(self):
        gateway = _function_source(GATEWAY, "execute_opacity_preference_request")
        self.assertIn("prepare_opacity_preference_plan", gateway)
        self.assertIn("sync_transparent_control", gateway)
        self.assertLess(gateway.index("host.save_settings"), gateway.index("apply_widget_opacity"))
        self.assertLess(gateway.index("apply_widget_opacity"), gateway.index("host.opacity_percent ="))

    def test_adapter_uses_gtk_widget_not_deprecated_window_api(self):
        preference = PREFERENCE.read_text(encoding="utf-8")
        adapter = _function_source(PREFERENCE, "apply_widget_opacity")
        self.assertIn("Gtk.Widget", adapter)
        self.assertIn('getattr(widget_api, "set_opacity"', adapter)
        self.assertIn("setter(widget, preference.fraction)", adapter)
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotIn("Gtk.Window.set_opacity", launcher)
        self.assertNotIn("Gtk.Window.get_opacity", launcher)

    def test_no_menu_recomposition_or_unrelated_command_change(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('optm = top_menu(app, "Options")', ui)
        self.assertIn('add_item(opacity_menu, "Opacity Selection…", app.on_opacity_selection)', ui)
        self.assertIn('Gtk.CheckMenuItem(label="Always on Top\\tCtrl+Shift+A")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="White Background")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="Dark Mode")', ui)


if __name__ == "__main__":
    unittest.main()
