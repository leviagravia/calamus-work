import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
DIALOGS = ROOT / "calamus" / "calamus_dialogs.py"
SEARCH_DIALOGS = ROOT / "calamus" / "calamus_search_dialogs.py"
SEARCH_GATEWAY = ROOT / "calamus" / "calamus_search_gateway.py"
SEARCH_VIEW = ROOT / "calamus" / "calamus_search_view.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def method_source(name):
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(name)


class SearchCommandWiringTests(unittest.TestCase):
    def test_startup_has_one_search_controller_authority(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn(
            "self.search_controller = SearchController(SearchViewAdapter(self.text, self.search_tag))",
            source,
        )
        self.assertNotIn("self.last_search =", source)
        self.assertNotIn("self.last_match =", source)
        self.assertNotIn("self.search_highlight_source =", source)

    def test_find_all_is_visible_in_edit_menu_without_menu_recomposition(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(editm, "Find All…", app.on_find_all)', ui)
        self.assertIn('editm = top_menu(app, "Edit")', ui)
        self.assertIn('add_item(editm, "Find / Replace…\\tCtrl+F", app.on_find_replace)', ui)
        self.assertLess(
            ui.index('add_item(editm, "Find / Replace…\\tCtrl+F", app.on_find_replace)'),
            ui.index('add_item(editm, "Find All…", app.on_find_all)'),
        )
        self.assertNotIn('top_menu(app, "Search")', ui)

    def test_find_all_callback_is_thin(self):
        method = method_source("on_find_all")
        self.assertIn("run_find_all_dialog(self, self.search_controller)", method)
        self.assertLessEqual(len(method.splitlines()), 2)
        for token in ("get_buffer", "TreeView", "ListStore", "search_matches", "select_range"):
            self.assertNotIn(token, method)

    def test_find_replace_dialog_moved_out_of_generic_dialog_module(self):
        self.assertNotIn("def run_find_replace_dialog", DIALOGS.read_text(encoding="utf-8"))
        dedicated = SEARCH_DIALOGS.read_text(encoding="utf-8")
        self.assertIn("def run_find_replace_dialog", dedicated)
        self.assertIn("def run_find_all_dialog", dedicated)
        self.assertIn('Gtk.TreeView(model=store)', dedicated)
        self.assertIn('Gtk.TreeViewColumn("Line"', dedicated)
        self.assertIn('Gtk.TreeViewColumn("Column"', dedicated)
        self.assertIn('Gtk.TreeViewColumn("Context"', dedicated)
        self.assertIn('tree.connect("row-activated"', dedicated)
        self.assertIn('dialog.get_widget_for_response(20)', dedicated)

    def test_search_gateway_and_view_are_separate_boundaries(self):
        gateway = SEARCH_GATEWAY.read_text(encoding="utf-8")
        view = SEARCH_VIEW.read_text(encoding="utf-8")
        self.assertIn("class SearchController", gateway)
        self.assertIn("class SearchViewAdapter", view)
        self.assertNotIn("from gi.repository", gateway)
        self.assertNotIn("from gi.repository", view)
        self.assertNotIn("Gtk.", gateway)
        self.assertNotIn("Gtk.", view)

    def test_find_all_coordinates_are_owned_by_text_iter_adapter(self):
        gateway = SEARCH_GATEWAY.read_text(encoding="utf-8")
        view = SEARCH_VIEW.read_text(encoding="utf-8")
        self.assertIn("line_column_for_offset", gateway)
        self.assertIn("line_column_for_offset", view)
        self.assertIn("get_iter_at_offset(offset)", view)
        self.assertIn("get_line()", view)
        self.assertIn("get_line_offset()", view)
        self.assertNotIn("text_buffer_line_spans", view)

    def test_search_refresh_scheduler_left_app(self):
        method = method_source("schedule_search_highlight")
        self.assertIn("self.search_controller.schedule_highlight(GLib.timeout_add)", method)
        self.assertLessEqual(len(method.splitlines()), 4)
        self.assertNotIn("GLib.timeout_add(300", method)

    def test_source_provenance_includes_search_modules(self):
        source = PROVENANCE.read_text(encoding="utf-8")
        for module in (
            "calamus_search",
            "calamus_search_gateway",
            "calamus_search_view",
            "calamus_search_dialogs",
        ):
            self.assertIn(f'"{module}"', source)

    def test_search_session_options_are_reused_by_next_and_previous(self):
        next_method = method_source("on_find_next")
        previous_method = method_source("on_find_previous")
        self.assertIn("self.search_controller.repeat()", next_method)
        self.assertIn("self.search_controller.repeat(backwards=True)", previous_method)
        self.assertNotIn("match_case=False", next_method)
        self.assertNotIn("whole_word=False", previous_method)


if __name__ == "__main__":
    unittest.main()
