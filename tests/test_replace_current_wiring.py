import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
SEARCH_SOURCE = (ROOT / "calamus" / "calamus_search.py").read_text(encoding="utf-8")
GATEWAY_SOURCE = (ROOT / "calamus" / "calamus_search_gateway.py").read_text(encoding="utf-8")
SEARCH_DIALOGS_SOURCE = (ROOT / "calamus" / "calamus_search_dialogs.py").read_text(encoding="utf-8")


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
    def test_replace_current_preflight_is_owned_by_search_controller(self):
        method = app_method_source("replace_current_match")
        self.assertIn("plan = self.search_controller.prepare_current_replacement(replacement)", method)
        self.assertIn("return prepare_current_replacement(", GATEWAY_SOURCE)
        self.assertNotIn("self.buffer_text()", method)
        self.assertNotIn("self.last_match", method)

    def test_replace_current_keeps_document_mutation_in_app_gateway(self):
        method = app_method_source("replace_current_match")
        self.assertIn("start, end, replacement_text, next_match = plan", method)
        self.assertIn("self.replace_buffer_range(start, end, replacement_text)", method)
        self.assertIn("self.search_controller.commit_current_replacement(next_match)", method)
        self.assertIn("return True", method)

    def test_replace_current_has_no_inline_search_validation(self):
        method = app_method_source("replace_current_match")
        for token in (
            "current = text[start:end]",
            "current.lower()",
            "needle.lower()",
            "re.match(",
            "before =",
            "after =",
            "start < 0",
            "end > len(text)",
        ):
            self.assertNotIn(token, method)

    def test_replace_buffer_range_still_owns_execute_command_boundary(self):
        method = app_method_source("replace_buffer_range")
        self.assertIn("buf.delete(it1, it2)", method)
        self.assertIn("buf.insert(buf.get_iter_at_offset(start), replacement)", method)
        self.assertIn('self.execute_command("Replace Selection", edit, select_range=(start, start + len(replacement)))', method)


    def test_visible_replace_command_keeps_replaced_match_selected(self):
        self.assertIn('"Replace", 20', SEARCH_DIALOGS_SOURCE)
        self.assertNotIn('"Replace Current"', SEARCH_DIALOGS_SOURCE)
        tree = ast.parse(SEARCH_DIALOGS_SOURCE)
        do_replace = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "do_replace"
        )
        source = ast.get_source_segment(SEARCH_DIALOGS_SOURCE, do_replace) or ""
        self.assertIn("replace_current(replacement)", source)
        self.assertIn("controller.highlight()", source)
        self.assertNotIn("controller.find()", source)
        self.assertIn("Replaced selected match.", source)

    def test_search_model_is_pure(self):
        for token in (
            "Gtk",
            "Gdk",
            "GLib",
            "TextBuffer",
            "execute_command",
            "replace_buffer_range",
            "scroll_to",
            ".delete(",
            ".insert(",
            "set_text(",
        ):
            self.assertNotIn(token, SEARCH_SOURCE)


if __name__ == "__main__":
    unittest.main()
