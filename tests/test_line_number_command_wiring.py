import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
EDITOR = ROOT / "calamus" / "calamus_editor.py"
APPEARANCE = ROOT / "calamus" / "calamus_appearance.py"
LINE_NUMBERS = ROOT / "calamus" / "calamus_line_numbers.py"
GATEWAY = ROOT / "calamus" / "calamus_line_numbers_gateway.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def _method_source(name: str) -> str:
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"method {name!r} not found")


class LineNumberCommandWiringTests(unittest.TestCase):
    def test_visible_command_and_shortcut_are_unchanged(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('Gtk.CheckMenuItem(label="Line Numbers\\tCtrl+Alt+L")', ui)
        self.assertIn('("<Control><Alt>L", app.toggle_line_numbers)', ui)

    def test_startup_uses_one_typed_line_number_authority(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("line_number_preference = load_line_number_preference(self.settings)", launcher)
        self.assertIn("self.line_numbers_enabled = line_number_preference.enabled", launcher)
        self.assertNotIn('bool(self.settings.get("line_numbers"', launcher)
        self.assertNotIn("self.show_line_numbers", launcher)

    def test_settings_write_canonical_state_not_menu_state(self):
        method = _method_source("save_settings")
        self.assertIn("line_number_settings_overrides(self.line_numbers_enabled)", method)
        self.assertNotIn("line_item.get_active", method)

    def test_callback_is_thin_guarded_and_document_independent(self):
        method = _method_source("on_line_numbers")
        self.assertIn("self._syncing_line_number_item", method)
        self.assertIn("execute_line_number_preference_request", method)
        self.assertLessEqual(len(method.splitlines()), 4)
        for forbidden in (
            "document",
            "get_buffer",
            "history",
            "undo",
            "modified",
            "set_visible",
            "set_text",
            "save_settings",
        ):
            self.assertNotIn(forbidden, method)

    def test_refresh_method_is_a_two_line_compatibility_adapter(self):
        method = _method_source("update_line_numbers")
        self.assertIn("refresh_line_number_gutter(self, force=force)", method)
        self.assertLessEqual(len(method.splitlines()), 2)
        self.assertNotIn("set_text", method)
        self.assertNotIn("measure_line_gutter_width", method)

    def test_editor_builds_viewport_aligned_drawing_gutter(self):
        editor = EDITOR.read_text(encoding="utf-8")
        gutter = LINE_NUMBERS.read_text(encoding="utf-8")
        self.assertIn("line_gutter_widget = Gtk.DrawingArea()", editor)
        self.assertIn('line_gutter_widget.set_name("line-gutter")', editor)
        self.assertIn("line_gutter = LineGutterAdapter(", editor)
        self.assertIn('line_gutter_widget.connect("draw", draw_line_gutter)', editor)
        self.assertIn("Gtk.render_background", editor)
        self.assertIn("Gtk.render_frame", editor)
        self.assertIn("render_layout=Gtk.render_layout", editor)
        self.assertIn("get_line_at_y", gutter)
        self.assertIn("get_line_yrange", gutter)
        self.assertIn("iterator.get_line()", gutter)
        self.assertIn("return editor_box, line_gutter, scroller, text", editor)
        for obsolete in (
            "line_scroller = Gtk.ScrolledWindow()",
            "sync_gutter_scroll",
            "line_numbers = Gtk.Label()",
            'set_name("line-numbers")',
        ):
            self.assertNotIn(obsolete, editor)

        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('win.connect("map-event", _refresh_line_numbers_after_map)', launcher)
        self.assertIn("win.show_all()", launcher)
        self.assertIn("win.update_line_numbers()", launcher)
        self.assertIn("win.update_line_numbers(force=True)", launcher)
        self.assertLess(
            launcher.index('win.connect("map-event", _refresh_line_numbers_after_map)'),
            launcher.index("win.show_all()"),
        )


    def test_bulk_buffer_replacement_refreshes_gutter_outside_loading_guard(self):
        method = _method_source("on_changed")
        self.assertIn("self.update_line_numbers()", method)
        self.assertIn("if not self.loading:", method)
        self.assertLess(
            method.index("self.update_line_numbers()"),
            method.index("if not self.loading:"),
        )

    def test_mapped_startup_forces_realized_gutter_refresh(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        helper = _method_source("_refresh_line_numbers_after_map")
        self.assertIn("win.update_line_numbers(force=True)", helper)
        self.assertIn("return False", helper)
        self.assertIn('win.connect("map-event", _refresh_line_numbers_after_map)', launcher)

    def test_launcher_no_longer_owns_raw_gutter_widgets_or_geometry(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotIn("self.line_numbers.", launcher)
        self.assertNotIn("measure_line_gutter_width", launcher)
        self.assertNotIn("LINE_GUTTER_MIN_WIDTH", launcher)
        self.assertIn("self.line_gutter.apply_typography", launcher)

    def test_gutter_adapter_has_no_gtk_import(self):
        source = LINE_NUMBERS.read_text(encoding="utf-8")
        self.assertNotIn("from gi.repository", source)
        self.assertNotIn("import Gtk", source)
        self.assertIn("class LineGutterAdapter", source)
        self.assertIn("build_line_number_text", source)
        self.assertIn("measure_line_gutter_width", source)

    def test_gateway_is_persist_first_and_has_failure_rollback(self):
        source = GATEWAY.read_text(encoding="utf-8")
        self.assertLess(source.index("host.save_settings(line_number_settings_overrides(requested))"), source.index("host.line_gutter.render(requested, line_count)"))
        self.assertIn("host.save_settings(line_number_settings_overrides(previous))", source)
        self.assertIn("sync_line_number_control", source)
        self.assertNotIn("from gi.repository", source)

    def test_white_and_dark_palettes_style_only_the_drawing_gutter(self):
        css = APPEARANCE.read_text(encoding="utf-8")
        self.assertIn("#line-gutter", css)
        self.assertIn("border-right: 1px solid #d7d7d7", css)
        self.assertIn("border-right: 1px solid #3b3b3b", css)
        self.assertIn("border-right: 1px solid rgba(128, 128, 128, 0.35)", css)
        self.assertIn("background-image: none", css)
        self.assertIn("box-shadow: none", css)
        self.assertNotIn("#line-numbers", css)
        self.assertNotIn("#line-gutter scrollbar", css)
        self.assertNotIn("#line-gutter > border", css)
        self.assertNotIn("border-right: 2px", css)
        self.assertNotIn("border-right: 1px solid #000", css)


    def test_source_provenance_includes_new_line_number_modules(self):
        source = PROVENANCE.read_text(encoding="utf-8")
        self.assertIn('"calamus_line_numbers"', source)
        self.assertIn('"calamus_line_numbers_gateway"', source)

    def test_other_options_are_not_recomposed(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('optm = top_menu(app, "Options")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="White Background")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="Dark Mode")', ui)
        self.assertIn('Gtk.CheckMenuItem(label="Transparent Mode\\tCtrl+Shift+T")', ui)
        self.assertIn('opacity_item = Gtk.MenuItem(label="Opacity")', ui)


if __name__ == "__main__":
    unittest.main()
