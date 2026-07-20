import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
SEARCH_SOURCE = (ROOT / "calamus" / "calamus_search.py").read_text(encoding="utf-8")
GATEWAY_SOURCE = (ROOT / "calamus" / "calamus_search_gateway.py").read_text(encoding="utf-8")
VIEW_SOURCE = (ROOT / "calamus" / "calamus_search_view.py").read_text(encoding="utf-8")


def app_method_source(name):
    tree = ast.parse(LAUNCHER_SOURCE)
    lines = LAUNCHER_SOURCE.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    return "\n".join(lines[child.lineno - 1:child.end_lineno])
    raise AssertionError(f"App.{name} not found")


class FindTextMatchChoiceWiringTests(unittest.TestCase):
    def test_match_choice_moved_to_search_gateway(self):
        self.assertIn("chosen = choose_search_match(", GATEWAY_SOURCE)
        self.assertIn("cursor = self._adapter.cursor_offset(backwards=backwards)", GATEWAY_SOURCE)
        method = app_method_source("find_text")
        self.assertNotIn("choose_search_match", method)
        self.assertNotIn("for match in", method)

    def test_gtk_selection_boundary_moved_out_of_app(self):
        self.assertIn("class SearchViewAdapter", VIEW_SOURCE)
        self.assertIn("buffer.get_has_selection()", VIEW_SOURCE)
        self.assertIn("buffer.get_selection_bounds()", VIEW_SOURCE)
        self.assertIn("buffer.select_range(begin, finish)", VIEW_SOURCE)
        self.assertIn("self._text_view.scroll_to_iter", VIEW_SOURCE)
        method = app_method_source("find_text")
        self.assertNotIn("get_buffer", method)
        self.assertNotIn("scroll_to", method)

    def test_search_model_remains_pure(self):
        for token in (
            "Gtk",
            "Gdk",
            "GLib",
            "TextBuffer",
            "scroll_to",
            "execute_command",
            "open_path",
            "save_file",
            ".delete(",
            ".insert(",
            "set_text(",
        ):
            self.assertNotIn(token, SEARCH_SOURCE)

    def test_gateway_has_no_gtk_import(self):
        self.assertNotIn("from gi.repository", GATEWAY_SOURCE)
        self.assertNotIn("import Gtk", GATEWAY_SOURCE)


if __name__ == "__main__":
    unittest.main()
