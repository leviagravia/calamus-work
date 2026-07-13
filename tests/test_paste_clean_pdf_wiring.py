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


class PasteCleanPdfWiringTests(unittest.TestCase):
    def test_command_is_visible_in_revise_menu(self):
        self.assertIn('Paste Clean from PDF\\tCtrl+Alt+V', UI_SOURCE)
        self.assertIn("app.on_paste_clean_pdf", UI_SOURCE)

    def test_paste_clean_pdf_delegates_plan_to_pure_helper(self):
        method = app_method_source("on_paste_clean_pdf")
        self.assertIn("command_paste_text_plan(", method)
        self.assertIn("self.buffer_text()", method)
        self.assertIn("selection=selection", method)
        self.assertIn("start, end, insertion, select_range =", method)

    def test_paste_clean_pdf_still_owns_clipboard_and_buffer_boundary(self):
        method = app_method_source("on_paste_clean_pdf")
        self.assertIn("Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)", method)
        self.assertIn("clipboard.wait_for_text()", method)
        self.assertIn("clean_pdf_text(text)", method)
        self.assertIn("b.get_selection_bounds()", method)
        self.assertIn("buf.delete(it1, it2)", method)
        self.assertIn("buf.insert(buf.get_iter_at_offset(start), insertion)", method)
        self.assertIn('self.execute_command("Paste Clean PDF", edit, select_range=select_range)', method)

    def test_paste_clean_pdf_no_longer_branches_inside_edit_func(self):
        method = app_method_source("on_paste_clean_pdf")
        edit_body_start = method.index("def edit(buf):")
        edit_body = method[edit_body_start:]
        self.assertNotIn("buf.get_has_selection()", edit_body)
        self.assertNotIn("buf.get_selection_bounds()", edit_body)
        self.assertNotIn("else:", edit_body)

    def test_paste_helper_is_pure_boundary(self):
        helper = commands_function_source("paste_text_plan")
        forbidden = [
            "Gtk",
            "Gdk",
            "GLib",
            "TextBuffer",
            "Clipboard",
            "wait_for_text",
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
            self.assertNotIn(token, helper)

    def test_plain_text_paste_now_reuses_the_same_pure_plan_boundary(self):
        method = app_method_source("on_paste_plain_text")
        self.assertIn("command_paste_text_plan", method)
        self.assertIn('"Paste Plain Text"', method)
        self.assertNotIn("clean_pdf_text(text)", method)


if __name__ == "__main__":
    unittest.main()
