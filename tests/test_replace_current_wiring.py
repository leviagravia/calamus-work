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


class ReplaceCurrentWiringTests(unittest.TestCase):
    def test_replace_current_delegates_preflight_to_pure_helper(self):
        method = app_method_source("replace_current_match")
        self.assertIn("plan = prepare_current_replacement(", method)
        self.assertIn("self.buffer_text()", method)
        self.assertIn("self.last_match", method)
        self.assertIn("match_case=match_case", method)
        self.assertIn("whole_word=whole_word", method)
        self.assertIn("if plan is None:", method)
        self.assertIn("start, end, replacement, next_match = plan", method)

    def test_replace_current_still_owns_mutation_and_last_match(self):
        method = app_method_source("replace_current_match")
        self.assertIn("self.replace_buffer_range(start, end, replacement)", method)
        self.assertIn("self.last_match = next_match", method)
        self.assertIn("return True", method)

    def test_replace_current_no_longer_contains_inline_validation_logic(self):
        method = app_method_source("replace_current_match")
        forbidden = [
            "current = text[start:end]",
            "current.lower()",
            "needle.lower()",
            "re.match(",
            "before =",
            "after =",
            "start < 0",
            "end > len(text)",
        ]
        for token in forbidden:
            self.assertNotIn(token, method)

    def test_replace_buffer_range_still_owns_execute_command_boundary(self):
        method = app_method_source("replace_buffer_range")
        self.assertIn("buf.delete(it1, it2)", method)
        self.assertIn("buf.insert(buf.get_iter_at_offset(start), replacement)", method)
        self.assertIn('self.execute_command("Replace Selection", edit, select_range=(start, start + len(replacement)))', method)

    def test_search_helper_is_pure_boundary(self):
        forbidden = [
            "Gtk",
            "Gdk",
            "GLib",
            "TextBuffer",
            "execute_command",
            "finalize_command_edit",
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
