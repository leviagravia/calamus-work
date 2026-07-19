import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
APPEARANCE = ROOT / "calamus" / "calamus_appearance.py"


def _method_source(name: str) -> str:
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"method {name!r} not found")


class FontCommandWiringTests(unittest.TestCase):
    def test_visible_font_command_and_shortcut_are_unchanged(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(optm, "Font…\\tCtrl+Shift+F", app.on_font)', ui)
        self.assertIn('("<Control><Shift>F", app.on_font)', ui)

    def test_startup_uses_typed_font_loader(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("font_preference = load_font_preference(self.settings)", launcher)
        self.assertIn("self.font_size = font_preference.size", launcher)
        self.assertIn("self.font_family = font_preference.family", launcher)
        self.assertNotIn('self.settings.get("font_family", "Monospace")', launcher)

    def test_apply_font_is_thin_and_css_left_launcher(self):
        method = _method_source("apply_font")
        self.assertIn("build_application_css", method)
        self.assertIn("install_application_css", method)
        self.assertIn("self.line_numbers.set_visible", method)
        self.assertLess(method.index("install_application_css"), method.index("self.update_line_numbers"))
        self.assertLessEqual(len(method.splitlines()), 25)
        self.assertNotIn("White mode", method)
        self.assertNotIn("background-color", method)
        appearance = APPEARANCE.read_text(encoding="utf-8")
        self.assertIn("White mode", appearance)
        self.assertIn("background-color: #1e1e1e", appearance)


    def test_line_number_typography_and_geometry_use_explicit_runtime_adapters(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        apply_method = _method_source("apply_font")
        update_method = _method_source("update_line_numbers")
        self.assertIn("apply_line_gutter_typography", launcher)
        self.assertIn("measure_line_gutter_width", launcher)
        self.assertIn("apply_line_gutter_typography", apply_method)
        self.assertIn("pango=Pango", apply_method)
        self.assertLess(
            apply_method.index("apply_line_gutter_typography"),
            apply_method.index("self.update_line_numbers"),
        )
        self.assertIn("measure_line_gutter_width", update_method)
        self.assertIn("self.line_numbers", update_method)
        self.assertNotIn("digits * 9", update_method)
        self.assertNotIn("LINE_GUTTER_MAX_WIDTH", launcher)

    def test_font_callback_is_persist_then_apply_gateway(self):
        method = _method_source("on_font")
        self.assertIn("prepare_font_preference_plan", method)
        self.assertIn('"font_family": plan.requested.family', method)
        self.assertIn('"font_size": plan.requested.size', method)
        self.assertIn("self.font_family = plan.requested.family", method)
        self.assertIn("self.font_size = plan.requested.size", method)
        self.assertIn("self.apply_font()", method)
        self.assertIn("return True", method)
        self.assertLess(method.index("self.save_settings"), method.index("self.font_family ="))
        self.assertLess(method.index("self.font_size ="), method.index("self.apply_font"))

    def test_font_callback_has_no_document_or_undo_mutation(self):
        method = _method_source("on_font")
        for forbidden in (
            "current_file",
            "document",
            "get_buffer",
            "history",
            "undo",
            "modified",
            "Recent",
            "Favorite",
            "CommandContext",
            "command_layer",
        ):
            self.assertNotIn(forbidden, method)

    def test_other_options_are_not_recomposed(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('optm = top_menu(app, "Options")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="White Background")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="Dark Mode")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="Line Numbers\\tCtrl+Alt+L")', ui)


if __name__ == "__main__":
    unittest.main()
