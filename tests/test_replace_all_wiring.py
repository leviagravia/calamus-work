import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
SEARCH_SOURCE = (ROOT / "calamus" / "calamus_search.py").read_text(encoding="utf-8")
GATEWAY_SOURCE = (ROOT / "calamus" / "calamus_search_gateway.py").read_text(encoding="utf-8")


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
    def test_replace_all_plan_is_owned_by_search_controller(self):
        method = app_method_source("replace_all_literal")
        self.assertIn("replaced, count = self.search_controller.prepare_replace_all(replacement)", method)
        self.assertIn("return prepare_replace_all_plan(", GATEWAY_SOURCE)
        self.assertNotIn("prepare_replace_all_plan", method)

    def test_replace_all_still_uses_canonical_app_mutation_gateway(self):
        method = app_method_source("replace_all_literal")
        self.assertIn("buf.delete(start, end)", method)
        self.assertIn("buf.insert(buf.get_start_iter(), replaced)", method)
        self.assertIn('self.execute_command("Replace All", edit)', method)
        self.assertIn("self.search_controller.clear_current_match()", method)
        self.assertIn("return count", method)

    def test_replace_current_remains_a_separate_plan(self):
        method = app_method_source("replace_current_match")
        self.assertIn("self.search_controller.prepare_current_replacement", method)
        self.assertNotIn("prepare_replace_all", method)

    def test_pure_search_model_does_not_mutate_gtk(self):
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
