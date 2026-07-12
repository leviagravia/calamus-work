from pathlib import Path
import ast
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "calamus"
sys.path.insert(0, str(ROOT / "calamus"))

from calamus_command_catalog import build_low_risk_registry
from calamus_command_context import CommandContext
from calamus_command_layer import CommandLayer


def app_methods():
    source = BIN.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    out[child.name] = "\n".join(lines[child.lineno - 1:child.end_lineno])
    return source, out


class LowercaseLayerWiringTests(unittest.TestCase):
    def test_dispatch_surface_includes_smart_typography(self):
        source = BIN.read_text(encoding="utf-8")
        dispatch_ids = re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", source, flags=re.S)
        self.assertEqual(sorted(dispatch_ids), ["edit.lowercase", "edit.uppercase", "writing.clean-pdf", "writing.join-lines", "writing.reflow-paragraph", "writing.remove-extra-spaces", "writing.remove-trailing-spaces", "writing.smart-typography", "writing.sort-lines", "writing.statistics", "writing.title-case"])

    def test_command_layer_lowercase_helper_is_compute_only(self):
        _source, methods = app_methods()
        helper = methods["command_layer_lowercase_text"]
        self.assertIn('"edit.lowercase"', helper)
        self.assertIn('CommandContext(app=self, source="gui", data={"text": text})', helper)
        for forbidden in [
            ".delete(", ".insert(", "set_text(", "mark_modified",
            "finalize_command_edit", "execute_command",
            "begin_user_action", "end_user_action",
        ]:
            self.assertNotIn(forbidden, helper)

    def test_apply_text_transform_has_lowercase_branch_and_preserves_pipeline(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("use_layer_uppercase", apply)
        self.assertIn("use_layer_lowercase", apply)
        self.assertIn("command_layer_uppercase_text(old)", apply)
        self.assertIn("command_layer_lowercase_text(old)", apply)
        self.assertIn("elif use_layer_lowercase:", apply)
        self.assertIn("if not changed:", apply)
        self.assertIn("return False", apply)
        self.assertIn("command_transform_range(current, start, end, lambda _text: new)", apply)
        self.assertIn("return self.execute_command(command_name, edit, select_range=select)", apply)
        self.assertNotIn("replace_selection(", apply)

    def test_existing_mutation_pipeline_remains_owner(self):
        _source, methods = app_methods()
        self.assertIn("finalize_command_edit", methods["execute_command"])
        self.assertIn("mark_modified", methods["finalize_command_edit"])

    def test_forbidden_transforms_not_wired_in_bin(self):
        source = BIN.read_text(encoding="utf-8")
        for forbidden in [
            '"writing.sentence-case"',
        ]:
            self.assertNotIn(forbidden, source)

    def test_lowercase_dynamic_noop_and_change(self):
        layer = CommandLayer(build_low_risk_registry())
        samples = [
            ("abc", "abc", False),
            ("ABC", "abc", True),
            ("AbC 123 ÈÉ", "abc 123 èé", True),
            ("GIÀ MAIUSCOLO", "già maiuscolo", True),
        ]
        for original, expected, expected_changed in samples:
            result = layer.dispatch("edit.lowercase", CommandContext(data={"text": original}))
            self.assertTrue(result.success)
            value = result.value
            transformed = value.get("text") if isinstance(value, dict) else value
            self.assertEqual(transformed, expected)
            self.assertEqual(transformed != original, expected_changed)

    def test_w17_runtime_identity_preserved(self):
        source = BIN.read_text(encoding="utf-8")
        version = (ROOT / "calamus" / "calamus_version.py").read_text(encoding="utf-8")
        self.assertIn('APP_TITLE = "Calamus Copy"', source)
        self.assertIn('RUNTIME_ABOUT_NAME = "Calamus-Working-Copy"', source)
        self.assertIn('APP_VERSION = "1.7.0-rc3-stable4.3"', version)


if __name__ == "__main__":
    unittest.main()
