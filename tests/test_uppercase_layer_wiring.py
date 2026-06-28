from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from calamus_command_catalog import build_low_risk_registry
from calamus_command_context import CommandContext
from calamus_command_layer import CommandLayer


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


class UppercaseLayerWiringTests(unittest.TestCase):
    def test_dispatch_surface_includes_smart_typography(self):
        self.assertEqual(sorted(_dispatch_ids()), ["edit.lowercase", "edit.uppercase", "writing.smart-typography", "writing.statistics"])

    def test_apply_text_transform_is_uppercase_bridge_only(self):
        method = _app_method("apply_text_transform")
        self.assertIn("command_layer_uppercase_text(old)", method)
        self.assertIn("transform is str.upper", method)
        self.assertIn('command_name in {"Uppercase", "Upper Case", "UPPERCASE"}', method)
        self.assertNotIn("command_layer_transform_text", method)
        self.assertNotIn('"edit.lowercase"', method)
        self.assertNotIn('"writing.sort-lines"', method)
        self.assertNotIn('"writing.clean-pdf"', method)

    def test_command_layer_uppercase_helper_is_compute_only(self):
        method = _app_method("command_layer_uppercase_text")
        self.assertIn('self.command_layer.dispatch(\n            "edit.uppercase"', method)
        self.assertIn('CommandContext(app=self, source="gui", data={"text": text})', method)
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

    def test_noop_guard_before_mutation(self):
        method = _app_method("apply_text_transform")
        guard_pos = method.index("if not changed:")
        edit_pos = method.index("def edit(buf):")
        execute_pos = method.index("return self.execute_command")
        self.assertLess(guard_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)
        self.assertIn("return False", method)

    def test_existing_mutation_pipeline_remains_owner(self):
        method = _app_method("apply_text_transform")
        self.assertIn("command_transform_range(current, start, end", method)
        self.assertIn("return self.execute_command(command_name, edit, select_range=select)", method)
        self.assertNotIn("replace_selection(", method)

    def test_layer_uppercase_dynamic_noop_and_change(self):
        layer = CommandLayer(build_low_risk_registry())
        changed = layer.dispatch(
            "edit.uppercase",
            CommandContext(source="test", data={"text": "abc È già"}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], "ABC È GIÀ")

        noop = layer.dispatch(
            "edit.uppercase",
            CommandContext(source="test", data={"text": "ABC È GIÀ"}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], "ABC È GIÀ")

    def test_forbidden_transforms_not_wired_in_bin(self):
        source = _source()
        forbidden = [
            '"writing.remove-extra-spaces"',
            '"writing.remove-trailing-spaces"',
            '"writing.sort-lines"',
            '"writing.reflow-paragraph"',
            '"writing.join-lines"',
            '"writing.clean-pdf"',
        ]
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
