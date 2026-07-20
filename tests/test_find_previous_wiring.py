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
    def test_find_previous_reuses_canonical_search_session(self):
        method = app_method_source("on_find_previous")
        self.assertIn("if not self.search_controller.has_query():", method)
        self.assertIn("self.on_find_replace()", method)
        self.assertIn("self.search_controller.repeat(backwards=True)", method)
        self.assertIn('self.info("No previous match found.")', method)
        self.assertNotIn("self.last_search", method)
        self.assertNotIn("self.last_match", method)

    def test_find_previous_remains_non_mutating_wrapper(self):
        method = app_method_source("on_find_previous")
        for token in (
            "execute_command",
            "finalize_command_edit",
            "save_file",
            "open_path",
            ".delete(",
            ".insert(",
            "set_text(",
            "replace_all_literal",
            "get_buffer",
        ):
            self.assertNotIn(token, method)

    def test_find_text_is_a_thin_search_controller_adapter(self):
        method = app_method_source("find_text")
        self.assertIn("return self.search_controller.find(", method)
        self.assertLessEqual(len(method.splitlines()), 8)
        for token in (
            "get_buffer",
            "get_selection_bounds",
            "get_iter_at_mark",
            "choose_search_match",
            "select_range",
            "last_search",
            "last_match",
        ):
            self.assertNotIn(token, method)

    def test_replace_paths_do_not_use_repeat_navigation(self):
        for name in ["replace_all_literal", "on_replace_all_dialog", "replace_current_match"]:
            self.assertNotIn(".repeat(", app_method_source(name))


if __name__ == "__main__":
    unittest.main()
