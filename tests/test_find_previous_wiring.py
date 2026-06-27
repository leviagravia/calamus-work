import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")


def app_method_source(name):
    tree = ast.parse(SOURCE)
    lines = SOURCE.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    return "\n".join(lines[child.lineno - 1:child.end_lineno])
    raise AssertionError(f"App.{name} not found")


class FindPreviousWiringTests(unittest.TestCase):
    def test_find_previous_reuses_repeat_search_helper(self):
        method = app_method_source("on_find_previous")
        self.assertIn("if not can_repeat_search(self.last_search):", method)
        self.assertIn("self.on_find_replace()", method)
        self.assertIn("self.highlight_all_search(self.last_search)", method)
        self.assertIn("self.find_text(self.last_search, backwards=True)", method)
        self.assertIn('self.info("No previous match found.")', method)

    def test_find_previous_remains_non_mutating_wrapper(self):
        method = app_method_source("on_find_previous")
        forbidden = [
            "execute_command",
            "finalize_command_edit",
            "save_file",
            "open_path",
            ".delete(",
            ".insert(",
            "set_text(",
            "apply_text_transform",
            "replace_all_literal",
        ]
        for token in forbidden:
            self.assertNotIn(token, method)

    def test_find_text_still_owns_editor_search_boundary(self):
        method = app_method_source("find_text")
        expected = [
            "self.search_matches(",
            "self.text.get_buffer()",
            "get_has_selection",
            "get_selection_bounds",
            "get_iter_at_mark",
            "self.last_match",
            "self.select_range",
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

    def test_replace_paths_are_not_wired_to_repeat_search_helper(self):
        for name in ["replace_all_literal", "on_replace_all_dialog", "replace_current_match"]:
            self.assertNotIn("can_repeat_search", app_method_source(name))


if __name__ == "__main__":
    unittest.main()
