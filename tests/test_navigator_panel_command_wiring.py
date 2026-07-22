import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"
HOST = ROOT / "calamus" / "calamus_navigator_panel.py"
VIEW = ROOT / "calamus" / "calamus_navigator_panel_view.py"
CHROME = ROOT / "calamus" / "calamus_panel_chrome.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def function_source(path, name):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"{name} not found")


class NavigatorPanelCommandWiringTests(unittest.TestCase):
    def test_modules_are_present_and_provenance_tracked(self):
        for module in ("calamus_navigator_panel", "calamus_navigator_panel_view"):
            self.assertTrue((ROOT / "calamus" / f"{module}.py").exists())
            self.assertIn(f'"{module}"', PROVENANCE.read_text(encoding="utf-8"))

    def test_outer_workspace_paned_contains_existing_editor_right_panel_body(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("self.workspace_paned = Gtk.Paned", source)
        self.assertIn("self.workspace_paned.pack2(self.body_paned, True, True)", source)
        self.assertIn("self.body_paned.pack1(self.editor_box, True, True)", source)
        self.assertIn("RightPanelHost(self.body_paned", source)

    def test_one_w70_controller_is_reused_by_panel(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertEqual(source.count("NavigationController("), 1)
        self.assertIn("build_navigator_panel_view(\n            self.navigation_controller", source)
        self.assertNotIn("build_document_structure", VIEW.read_text(encoding="utf-8"))

    def test_navigate_menu_exposes_checkable_panel_before_commands(self):
        source = function_source(UI, "build_menu")
        block = source[source.index('navigatem = top_menu(app, "Navigate")'):source.index('revisem = top_menu(app, "Revise")')]
        self.assertIn('Gtk.CheckMenuItem(label="Navigator Panel\\tCtrl+Alt+N")', block)
        self.assertLess(block.index("Navigator Panel"), block.index("Go to Line"))
        self.assertIn('ShortcutSpec("Navigate", "Navigator Panel", "Ctrl+Alt+N")', SHORTCUTS.read_text(encoding="utf-8"))
        self.assertIn('("<Control><Alt>N", app.toggle_navigator_panel)', UI.read_text(encoding="utf-8"))

    def test_close_button_delegates_without_layout_mutation(self):
        source = VIEW.read_text(encoding="utf-8")
        chrome = CHROME.read_text(encoding="utf-8")
        self.assertIn('title.set_markup("<b>Navigator</b>")', source)
        self.assertIn("build_compact_close_button", source)
        self.assertIn('name="navigator-close-button"', source)
        self.assertIn('tooltip="Hide Navigator"', source)
        self.assertIn('"window-close-symbolic"', chrome)
        self.assertNotIn(".remove(", source)
        self.assertNotIn("pack1(", source)

    def test_close_button_is_compact_and_keeps_the_canonical_hide_gateway(self):
        source = VIEW.read_text(encoding="utf-8")
        chrome = CHROME.read_text(encoding="utf-8")
        self.assertIn("self._on_hide", source)
        self.assertIn("button.set_size_request(18, 18)", chrome)
        self.assertIn("min-width: 16px", chrome)
        self.assertIn("min-height: 16px", chrome)
        self.assertIn("background: transparent", chrome)
        self.assertIn("box-shadow: none", chrome)
        self.assertIn('button.connect("clicked", lambda *_: on_activate())', chrome)

    def test_host_is_specific_and_owns_attach_remove(self):
        source = HOST.read_text(encoding="utf-8")
        self.assertIn("class NavigatorPanelHost", source)
        self.assertIn("self._paned.pack1(self._widget, False, False)", source)
        self.assertIn("self._paned.remove(self._widget)", source)
        self.assertNotIn("register(", source)
        self.assertNotIn("plugin", source.lower())

    def test_one_visibility_runtime_serves_menu_shortcut_and_x(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("NavigatorPanelRuntime(", source)
        toggle = function_source(LAUNCHER, "toggle_navigator_panel")
        hide = function_source(LAUNCHER, "hide_navigator_panel")
        toggled = function_source(LAUNCHER, "on_navigator_item_toggled")
        self.assertIn("self.navigator_panel_runtime.toggle()", toggle)
        self.assertIn("self.navigator_panel_runtime.hide()", hide)
        self.assertIn("self.navigator_panel_runtime.on_menu_toggled(item)", toggled)
        host_source = HOST.read_text(encoding="utf-8")
        self.assertIn("class NavigatorPanelRuntime", host_source)
        self.assertIn("self._host.show()", host_source)
        self.assertIn("self._host.hide()", host_source)
        self.assertIn("self._sync_menu(target)", host_source)

    def test_buffer_and_cursor_hooks_remain_thin(self):
        changed = function_source(LAUNCHER, "on_changed")
        cursor = function_source(LAUNCHER, "on_cursor_position_notify")
        self.assertIn("self.navigation_controller.invalidate()", changed)
        self.assertIn("self.navigator_panel_view.invalidate()", changed)
        self.assertIn("self.navigator_panel_view.schedule_cursor_sync()", cursor)
        self.assertNotIn("build_document_structure", changed + cursor)

    def test_w71_is_navigation_only(self):
        command_surface = LAUNCHER.read_text(encoding="utf-8") + UI.read_text(encoding="utf-8")
        panel_source = HOST.read_text(encoding="utf-8") + VIEW.read_text(encoding="utf-8")
        for forbidden in ("Move Section", "Rename Header", "Refresh Section List"):
            self.assertNotIn(forbidden, command_surface)
        for forbidden in ("drag-data", "fold", "ReferencesTab"):
            self.assertNotIn(forbidden, panel_source)


if __name__ == "__main__":
    unittest.main()
