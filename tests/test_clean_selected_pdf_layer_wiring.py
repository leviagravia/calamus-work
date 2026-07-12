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
from calamus_writing import clean_pdf_text


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


class CleanSelectedPdfLayerWiringTests(unittest.TestCase):
    def test_command_is_visible_in_revise_menu_and_not_lambda_wired(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(revisem, "Clean Selected Text from PDF\\tCtrl+Alt+Shift+V", app.on_clean_selected_pdf)', ui)
        self.assertIn('("<Control><Alt><Shift>V", app.on_clean_selected_pdf)', ui)
        self.assertNotIn('app.apply_text_transform(clean_pdf_text, "Clean PDF Text")', ui)

    def test_dispatch_surface_adds_only_clean_pdf(self):
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
                "writing.remove-trailing-spaces",
                "writing.smart-typography",
                "writing.sort-lines",
                "writing.statistics",
    "writing.title-case",
            ],
        )

    def test_clean_pdf_helper_is_compute_only(self):
        _source, methods = app_methods()
        helper = methods["command_layer_clean_pdf_text"]
        self.assertIn('"writing.clean-pdf"', helper)
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
            "Clipboard",
            "wait_for_text",
        ]:
            self.assertNotIn(forbidden, helper)

    def test_apply_text_transform_routes_clean_pdf_through_layer(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("use_layer_clean_pdf", apply)
        self.assertIn('"Clean PDF Text"', apply)
        self.assertIn('"Clean Selected Text from PDF"', apply)
        self.assertIn("transform is clean_pdf_text", apply)
        self.assertIn("command_layer_clean_pdf_text(old)", apply)
        clean_pos = apply.index("elif use_layer_clean_pdf:")
        edit_pos = apply.index("def edit(buf):")
        execute_pos = apply.index("return self.execute_command")
        self.assertLess(clean_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)
        self.assertIn("command_transform_range(current, start, end, lambda _text: new)", apply)

    def test_on_clean_selected_pdf_is_visible_command_entrypoint(self):
        _source, methods = app_methods()
        method = methods["on_clean_selected_pdf"]
        self.assertEqual(
            method.strip(),
            'def on_clean_selected_pdf(self, *_):\n        return self.apply_text_transform(clean_pdf_text, "Clean PDF Text")',
        )

    def test_layer_clean_pdf_dynamic_noop_and_change(self):
        layer = CommandLayer(build_low_risk_registry())
        dirty = "inter-\nrupted text\nkeeps line"
        changed = layer.dispatch(
            "writing.clean-pdf",
            CommandContext(source="test", data={"text": dirty}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], clean_pdf_text(dirty))

        noop_text = "already clean paragraph"
        noop = layer.dispatch(
            "writing.clean-pdf",
            CommandContext(source="test", data={"text": noop_text}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], noop_text)


if __name__ == "__main__":
    unittest.main()
