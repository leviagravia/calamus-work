from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BIN_CALAMUS = ROOT / "bin" / "calamus"


def _source() -> str:
    return BIN_CALAMUS.read_text(encoding="utf-8")


def _app_method(name: str) -> str:
    source = _source()
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == name:
                    return "\n".join(lines[child.lineno - 1 : child.end_lineno])
    raise AssertionError(f"App.{name} not found")


def _dispatch_ids() -> list[str]:
    return re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", _source(), flags=re.S)


class StatisticsLayerWiringTests(unittest.TestCase):
    def test_bin_calamus_imports_command_layer_for_statistics_wiring(self):
        source = _source()
        self.assertIn("from calamus_command_context import CommandContext", source)
        self.assertIn("from calamus_command_layer import CommandLayer", source)
        self.assertIn("from calamus_command_catalog import build_low_risk_registry", source)
        self.assertIn("self.command_layer = CommandLayer(build_low_risk_registry())", source)

    def test_document_statistics_method_uses_layer_read_only(self):
        method = _app_method("on_document_statistics")
        self.assertRegex(method, r'self\.command_layer\.dispatch\(\s*"writing\.statistics"')
        self.assertIn('CommandContext(app=self, source="gui"', method)
        forbidden = [
            ".delete(",
            ".insert(",
            "set_text(",
            "mark_modified",
            "finalize_command_edit",
            "execute_command",
            "begin_user_action",
            "end_user_action",
        ]
        for token in forbidden:
            self.assertNotIn(token, method)

    def test_allowed_command_layer_dispatches_include_smart_typography(self):
        self.assertEqual(sorted(_dispatch_ids()), ["edit.lowercase", "edit.uppercase", "writing.clean-pdf", "writing.insert-date-time", "writing.join-lines", "writing.reflow-paragraph", "writing.remove-extra-spaces", "writing.remove-trailing-spaces", "writing.sentence-case", "writing.smart-typography", "writing.sort-lines", "writing.statistics", "writing.title-case"])

    def test_only_approved_text_transforms_are_wired_to_layer(self):
        source = _source()
        self.assertIn('"edit.uppercase"', source)
        self.assertIn('"writing.insert-date-time"', source)


if __name__ == "__main__":
    unittest.main()
