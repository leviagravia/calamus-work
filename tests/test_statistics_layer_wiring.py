import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BIN_CALAMUS = ROOT / "bin" / "calamus"


def app_method_source(method_name):
    source = BIN_CALAMUS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return "\n".join(lines[child.lineno - 1: child.end_lineno])
    raise AssertionError(f"App.{method_name} not found")


class StatisticsLayerWiringTests(unittest.TestCase):
    def test_bin_calamus_imports_command_layer_for_statistics_wiring(self):
        source = BIN_CALAMUS.read_text(encoding="utf-8")

        self.assertIn("from calamus_command_context import CommandContext", source)
        self.assertIn("from calamus_command_layer import CommandLayer", source)
        self.assertIn("from calamus_command_catalog import build_low_risk_registry", source)
        self.assertIn("self.command_layer = CommandLayer(build_low_risk_registry())", source)

    def test_only_statistics_dispatch_is_wired_in_bin_calamus(self):
        source = BIN_CALAMUS.read_text(encoding="utf-8")

        self.assertEqual(source.count(".dispatch("), 1)
        self.assertIn('"writing.statistics"', source)
        self.assertNotIn('"edit.uppercase"', source)
        self.assertNotIn('"edit.lowercase"', source)
        self.assertNotIn('"writing.sort-lines"', source)
        self.assertNotIn('"writing.remove-extra-spaces"', source)
        self.assertNotIn('"writing.remove-trailing-spaces"', source)

    def test_document_statistics_method_uses_layer_read_only(self):
        method = app_method_source("on_document_statistics")

        self.assertIn('self.command_layer.dispatch(', method)
        self.assertIn('"writing.statistics"', method)
        self.assertIn("text_before_statistics = self.buffer_text()", method)
        self.assertIn("stats = result.value", method)

        forbidden = [
            "perform_buffer_edit",
            "replace_selection",
            "command_replace_range",
            "command_insert_at",
            "command_transform_range",
            ".delete(",
            ".insert(",
            "commit_undo",
            "reset_undo",
            "save_file",
            "save_as",
            "write_text_file",
            "read_text_file",
            "self.modified =",
            "set_buffer(",
            "open_path",
            "on_save",
            "on_open",
        ]
        for token in forbidden:
            self.assertNotIn(token, method)

    def test_text_transform_methods_are_not_wired_to_layer_yet(self):
        for method_name in ("apply_text_transform", "on_reflow_paragraph", "on_paste_clean_pdf"):
            method = app_method_source(method_name)
            self.assertNotIn("self.command_layer.dispatch", method)
            self.assertNotIn("CommandContext", method)


if __name__ == "__main__":
    unittest.main()
