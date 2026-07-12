from pathlib import Path
import ast
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
sys.path.insert(0, str(ROOT / "calamus"))

from calamus_command_catalog import build_low_risk_registry
from calamus_command_context import CommandContext
from calamus_command_layer import CommandLayer
from calamus_writing import smart_typography


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


class SmartTypographyLayerWiringTests(unittest.TestCase):
    def test_command_is_visible_in_revise_menu_and_not_lambda_wired(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(revisem, "Smart Typography\\tCtrl+Alt+M", app.on_smart_typography)', ui)
        self.assertIn('("<Control><Alt>M", app.on_smart_typography)', ui)
        self.assertNotIn('app.apply_text_transform(smart_typography, "Smart Typography")', ui)

    def test_dispatch_surface_adds_only_smart_typography(self):
        source = BIN.read_text(encoding="utf-8")
        dispatch_ids = re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", source, flags=re.S)
        self.assertEqual(
            sorted(dispatch_ids),
            ["edit.lowercase", "edit.uppercase", "writing.clean-pdf", "writing.insert-date-time", "writing.join-lines", "writing.reflow-paragraph", "writing.remove-extra-spaces", "writing.remove-trailing-spaces", "writing.sentence-case", "writing.smart-typography", "writing.sort-lines", "writing.statistics", "writing.title-case"],
        )

    def test_smart_typography_helper_is_compute_only(self):
        _source, methods = app_methods()
        helper = methods["command_layer_smart_typography_text"]
        self.assertIn('"writing.smart-typography"', helper)
        self.assertIn('CommandContext(app=self, source="gui", data={"text": text})', helper)
        for forbidden in [
            ".delete(",
            ".insert(",
            "set_text(",
            "mark_modified",
            "finalize_command_edit",
            "execute_command",
            "begin_user_action",
            "end_user_action",
        ]:
            self.assertNotIn(forbidden, helper)

    def test_apply_text_transform_routes_smart_typography_through_layer(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("use_layer_smart_typography", apply)
        self.assertIn('command_name == "Smart Typography"', apply)
        self.assertIn("transform is smart_typography", apply)
        self.assertIn("command_layer_smart_typography_text(old)", apply)
        smart_pos = apply.index("elif use_layer_smart_typography:")
        edit_pos = apply.index("def edit(buf):")
        execute_pos = apply.index("return self.execute_command")
        self.assertLess(smart_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)
        self.assertIn("command_transform_range(current, start, end, lambda _text: new)", apply)

    def test_on_smart_typography_is_explicit_visible_command_entrypoint(self):
        _source, methods = app_methods()
        method = methods["on_smart_typography"]
        self.assertEqual(
            method.strip(),
            'def on_smart_typography(self, *_):\n        return self.apply_text_transform(smart_typography, "Smart Typography")',
        )

    def test_layer_smart_typography_dynamic_noop_and_change(self):
        layer = CommandLayer(build_low_risk_registry())
        changed = layer.dispatch(
            "writing.smart-typography",
            CommandContext(source="test", data={"text": '"ciao" -- ok...'}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], "“ciao” — ok…")

        noop = layer.dispatch(
            "writing.smart-typography",
            CommandContext(source="test", data={"text": "“ciao” — ok…"}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], "“ciao” — ok…")

    def test_plain_function_still_available_for_non_layer_tests(self):
        self.assertEqual(smart_typography('"ciao" -- ok...'), "“ciao” — ok…")


if __name__ == "__main__":
    unittest.main()
