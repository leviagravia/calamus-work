import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
SEARCH_SOURCE = (ROOT / "calamus" / "calamus_search.py").read_text(encoding="utf-8")


def app_method_source(name):
    tree = ast.parse(SOURCE)
    lines = SOURCE.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    return "\n".join(lines[child.lineno - 1:child.end_lineno])
    raise AssertionError(f"App.{name} not found")


class FindTextMatchChoiceWiringTests(unittest.TestCase):
    def test_find_text_delegates_match_choice_to_pure_helper(self):
        method = app_method_source("find_text")
        self.assertIn("chosen = choose_search_match(matches, cursor, backwards=backwards, wrap=wrap)", method)
        self.assertNotIn("for m in reversed(matches)", method)
        self.assertNotIn("for m in matches:", method)
        self.assertNotIn("chosen = matches[-1]", method)
        self.assertNotIn("chosen = matches[0]", method)

    def test_find_text_still_owns_editor_boundary(self):
        method = app_method_source("find_text")
        expected = [
            "self.search_matches(",
            "self.text.get_buffer()",
            "get_has_selection",
            "get_selection_bounds",
            "get_iter_at_mark",
            "self.last_search = needle",
            "self.last_match = (chosen.start(), chosen.end())",
            "self.select_range(chosen.start(), chosen.end())",
        ]
        for token in expected:
            self.assertIn(token, method)

    def test_select_range_still_owns_selection_and_scroll(self):
        method = app_method_source("select_range")
        expected = [
            "self.text.get_buffer()",
            "b.select_range",
            "self.text.scroll_to_iter",
        ]
        for token in expected:
            self.assertIn(token, method)

    def test_search_helper_is_pure_boundary(self):
        forbidden = [
            "Gtk",
            "Gdk",
            "GLib",
            "TextBuffer",
            "select_range",
            "scroll_to",
            "execute_command",
            "finalize_command_edit",
            "open_path",
            "save_file",
            ".delete(",
            ".insert(",
            "set_text(",
        ]
        for token in forbidden:
            self.assertNotIn(token, SEARCH_SOURCE)


if __name__ == "__main__":
    unittest.main()
