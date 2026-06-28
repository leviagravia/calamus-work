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


class ReplaceAllWiringTests(unittest.TestCase):
    def test_replace_all_delegates_plan_to_pure_helper(self):
        method = app_method_source("replace_all_literal")
        self.assertIn("replaced, count = prepare_replace_all_plan(", method)
        self.assertIn("text, old, new, match_case=match_case, whole_word=whole_word", method)
        self.assertNotIn("replace_all_literal_text(", method)

    def test_replace_all_still_owns_buffer_mutation_boundary(self):
        method = app_method_source("replace_all_literal")
        self.assertIn("buf.delete(s, e)", method)
        self.assertIn("buf.insert(buf.get_start_iter(), replaced)", method)
        self.assertIn('self.execute_command("Replace All", edit)', method)
        self.assertIn("self.last_match = None", method)
        self.assertIn("return count", method)

    def test_replace_current_remains_separate(self):
        method = app_method_source("replace_current_match")
        self.assertIn("prepare_current_replacement(", method)
        self.assertNotIn("prepare_replace_all_plan", method)

    def test_search_helpers_are_pure_boundary(self):
        forbidden = [
            "Gtk",
            "Gdk",
            "GLib",
            "TextBuffer",
            "execute_command",
            "finalize_command_edit",
            "replace_entire_buffer",
            "replace_buffer_range",
            "select_range",
            "scroll_to",
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
