import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
COMMANDS_SOURCE = (ROOT / "calamus" / "calamus_commands.py").read_text(encoding="utf-8")
UI_SOURCE = (ROOT / "calamus" / "calamus_ui.py").read_text(encoding="utf-8")


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


class PastePlainTextWiringTests(unittest.TestCase):
    def test_command_is_visible_and_shortcut_uses_named_entrypoint(self):
        self.assertIn('Paste as Plain Text\\tCtrl+Shift+V', UI_SOURCE)
        self.assertIn('add_item(editm, "Paste as Plain Text\\tCtrl+Shift+V", app.on_paste_plain_text)', UI_SOURCE)
        self.assertIn('("<Control><Shift>V", app.on_paste_plain_text)', UI_SOURCE)

    def test_plain_text_paste_delegates_branching_to_pure_plan(self):
        method = app_method_source("on_paste_plain_text")
        self.assertIn("command_paste_text_plan(", method)
        self.assertIn("self.buffer_text()", method)
        self.assertIn("selection=selection", method)
        self.assertIn("start, end, insertion, _inserted_range =", method)

    def test_clipboard_and_buffer_boundaries_remain_in_app(self):
        method = app_method_source("on_paste_plain_text")
        self.assertIn("Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)", method)
        self.assertIn("clipboard.wait_for_text()", method)
        self.assertIn("b.get_has_selection()", method)
        self.assertIn("b.get_selection_bounds()", method)
        self.assertIn("buf.delete(it1, it2)", method)
        self.assertIn("buf.insert(buf.get_iter_at_offset(start), insertion)", method)
        self.assertIn('"Paste Plain Text"', method)
        self.assertIn("select_range=(caret, caret)", method)

    def test_edit_closure_has_no_selection_or_cursor_branching(self):
        method = app_method_source("on_paste_plain_text")
        edit_body = method[method.index("def edit(buf):"):]
        self.assertNotIn("buf.get_has_selection()", edit_body)
        self.assertNotIn("buf.get_selection_bounds()", edit_body)
        self.assertNotIn("insert_at_cursor", edit_body)
        self.assertNotIn("else:", edit_body)

    def test_caret_is_restored_after_insertion_not_inserted_text_selection(self):
        method = app_method_source("on_paste_plain_text")
        self.assertIn("caret = start + len(insertion)", method)
        self.assertIn("select_range=(caret, caret)", method)
        self.assertNotIn("select_range=_inserted_range", method)

    def test_none_clipboard_text_is_still_a_safe_noop(self):
        method = app_method_source("on_paste_plain_text")
        self.assertIn("if text is None:", method)
        self.assertIn("return", method)
        self.assertLess(method.index("if text is None:"), method.index("command_paste_text_plan("))

    def test_paste_plan_remains_pure(self):
        helper = commands_function_source("paste_text_plan")
        forbidden = (
            "Gtk", "Gdk", "GLib", "TextBuffer", "Clipboard", "wait_for_text",
            "execute_command", "get_selection_bounds", "get_iter_at_offset",
            ".delete(", ".insert(", "set_text(",
        )
        for token in forbidden:
            self.assertNotIn(token, helper)

    def test_normal_paste_and_clean_pdf_paths_are_not_rewired(self):
        normal = app_method_source("on_paste")
        clean = app_method_source("on_paste_clean_pdf")
        self.assertIn("paste_clipboard", normal)
        self.assertNotIn("command_paste_text_plan", normal)
        self.assertIn("command_paste_text_plan", clean)
        self.assertIn("clean_pdf_text(text)", clean)


if __name__ == "__main__":
    unittest.main()
