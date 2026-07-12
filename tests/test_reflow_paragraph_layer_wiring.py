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
from calamus_writing import reflow_paragraph


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


class ReflowParagraphLayerWiringTests(unittest.TestCase):
    def test_command_is_visible_in_revise_menu(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(revisem, "Reflow Paragraph\\tCtrl+Alt+J", app.on_reflow_paragraph)', ui)
        self.assertIn('("<Control><Alt>J", app.on_reflow_paragraph)', ui)

    def test_dispatch_surface_adds_only_reflow_paragraph(self):
        source = BIN.read_text(encoding="utf-8")
        dispatch_ids = re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", source, flags=re.S)
        self.assertEqual(
            sorted(dispatch_ids),
            [
                "edit.lowercase",
                "edit.uppercase",
                "writing.clean-pdf",
                "writing.join-lines",
                "writing.reflow-paragraph",
                "writing.remove-extra-spaces",
                "writing.smart-typography",
                "writing.statistics",
            ],
        )

    def test_reflow_helper_is_compute_only_and_parameterized(self):
        _source, methods = app_methods()
        helper = methods["command_layer_reflow_paragraph_text"]
        self.assertIn('"writing.reflow-paragraph"', helper)
        self.assertIn('CommandContext(app=self, source="gui", data={"text": text, "width": width})', helper)
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

    def test_apply_text_transform_routes_reflow_through_layer(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("use_layer_reflow_paragraph", apply)
        self.assertIn('command_name == "Reflow Paragraph"', apply)
        self.assertIn("command_layer_reflow_paragraph_text(old, width=80)", apply)
        reflow_pos = apply.index("elif use_layer_reflow_paragraph:")
        edit_pos = apply.index("def edit(buf):")
        execute_pos = apply.index("return self.execute_command")
        self.assertLess(reflow_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)
        self.assertIn("command_transform_range(current, start, end, lambda _text: new)", apply)

    def test_on_reflow_paragraph_is_visible_command_entrypoint(self):
        _source, methods = app_methods()
        method = methods["on_reflow_paragraph"]
        self.assertEqual(
            method.strip(),
            'def on_reflow_paragraph(self, *_):\n        return self.apply_text_transform(lambda t: reflow_paragraph(t, width=80), "Reflow Paragraph")',
        )

    def test_layer_reflow_dynamic_width_and_noop(self):
        layer = CommandLayer(build_low_risk_registry())
        text = "alpha beta gamma delta epsilon"
        changed = layer.dispatch(
            "writing.reflow-paragraph",
            CommandContext(source="test", data={"text": text, "width": 12}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], reflow_paragraph(text, width=12))

        noop_text = "short line"
        noop = layer.dispatch(
            "writing.reflow-paragraph",
            CommandContext(source="test", data={"text": noop_text, "width": 80}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], noop_text)


if __name__ == "__main__":
    unittest.main()
