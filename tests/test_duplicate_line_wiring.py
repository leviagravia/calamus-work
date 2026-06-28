import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
COMMANDS_SOURCE = (ROOT / "calamus" / "calamus_commands.py").read_text(encoding="utf-8")


def app_method_source(name):
    tree = ast.parse(SOURCE)
    lines = SOURCE.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    return "\n".join(lines[child.lineno - 1:child.end_lineno])
    raise AssertionError(f"App.{name} not found")


def commands_function_source(name):
    tree = ast.parse(COMMANDS_SOURCE)
    lines = COMMANDS_SOURCE.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return "\n".join(lines[node.lineno - 1:node.end_lineno])
    raise AssertionError(f"calamus_commands.{name} not found")


class DuplicateLineWiringTests(unittest.TestCase):
    def test_duplicate_command_delegates_plan_to_pure_helper(self):
        method = app_method_source("on_duplicate_line_or_selection")
        self.assertIn("plan = command_duplicate_line_or_selection_plan(", method)
        self.assertIn("self.buffer_text()", method)
        self.assertIn("self.get_cursor_offset()", method)
        self.assertIn("selection=selection", method)

    def test_duplicate_command_still_owns_textbuffer_and_command_boundary(self):
        method = app_method_source("on_duplicate_line_or_selection")
        self.assertIn("b = self.text.get_buffer()", method)
        self.assertIn("b.get_selection_bounds()", method)
        self.assertIn("buf.insert(buf.get_iter_at_offset(insert_pos), insertion)", method)
        self.assertIn("self.execute_command(action_name, edit, select_range=select_range)", method)

    def test_duplicate_command_no_longer_contains_inline_line_algorithm(self):
        method = app_method_source("on_duplicate_line_or_selection")
        forbidden = [
            "current_line_bounds_from_text",
            "text.rfind",
            "text.find",
            "line = text[start:end]",
            "end < len(text)",
            "end+1",
            "new_cursor = insert_pos + len(insertion)",
            "txt = b.get_text",
        ]
        for token in forbidden:
            self.assertNotIn(token, method)

    def test_app_pure_line_bounds_method_removed(self):
        self.assertNotIn("def current_line_bounds_from_text", SOURCE)

    def test_duplicate_helpers_are_pure_boundary(self):
        helper_source = (
            commands_function_source("line_bounds_at_offset")
            + "\n"
            + commands_function_source("duplicate_line_or_selection_plan")
        )
        forbidden = [
            "Gtk",
            "Gdk",
            "GLib",
            "TextBuffer",
            "execute_command",
            "finalize_command_edit",
            "get_selection_bounds",
            "get_iter_at_offset",
            "select_range",
            "scroll_to",
            "open_path",
            "save_file",
            ".delete(",
            ".insert(",
            "set_text(",
        ]
        for token in forbidden:
            self.assertNotIn(token, helper_source)


if __name__ == "__main__":
    unittest.main()
