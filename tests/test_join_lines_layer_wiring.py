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
from calamus_writing import join_lines


EXPECTED_DISPATCH_IDS = [
    "edit.lowercase",
    "edit.uppercase",
    "writing.clean-pdf",
    "writing.join-lines",
    "writing.reflow-paragraph",
    "writing.remove-extra-spaces",
    "writing.remove-trailing-spaces",
    "writing.sentence-case",
    "writing.smart-typography",
    "writing.sort-lines",
    "writing.statistics",
    "writing.title-case",
]


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


class JoinLinesLayerWiringTests(unittest.TestCase):
    def test_menu_and_shortcut_share_explicit_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "Join Lines\\tCtrl+J", app.on_join_lines)',
            ui,
        )
        self.assertIn('("<Control>J", app.on_join_lines)', ui)
        self.assertEqual(ui.count("app.on_join_lines"), 2)
        self.assertNotIn(
            'app.apply_text_transform(join_lines, "Join Lines")',
            ui,
        )

    def test_dispatch_surface_adds_only_join_lines(self):
        source = BIN.read_text(encoding="utf-8")
        dispatch_ids = re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", source, flags=re.S)
        self.assertEqual(sorted(dispatch_ids), EXPECTED_DISPATCH_IDS)

    def test_helper_is_compute_only(self):
        _source, methods = app_methods()
        helper = methods["command_layer_join_lines_text"]
        self.assertIn('"writing.join-lines"', helper)
        self.assertIn(
            'CommandContext(app=self, source="gui", data={"text": text})',
            helper,
        )
        for forbidden in [
            ".delete(",
            ".insert(",
            "set_text(",
            "mark_modified",
            "finalize_command_edit",
            "execute_command",
            "begin_user_action",
            "end_user_action",
            "selected_or_all_range",
            "get_buffer",
            "Clipboard",
        ]:
            self.assertNotIn(forbidden, helper)

    def test_apply_text_transform_routes_command_before_mutation(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("use_layer_join_lines", apply)
        self.assertIn('command_name == "Join Lines"', apply)
        self.assertIn("transform is join_lines", apply)
        self.assertIn("command_layer_join_lines_text(old)", apply)
        branch_pos = apply.index("elif use_layer_join_lines:")
        edit_pos = apply.index("def edit(buf):")
        execute_pos = apply.index("return self.execute_command")
        self.assertLess(branch_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)
        self.assertIn("if not changed:\n                return False", apply)
        self.assertIn(
            "command_transform_range(current, start, end, lambda _text: new)",
            apply,
        )

    def test_visible_entrypoint_preserves_existing_transform_pipeline(self):
        _source, methods = app_methods()
        method = methods["on_join_lines"]
        self.assertEqual(
            method.strip(),
            'def on_join_lines(self, *_):\n'
            '        return self.apply_text_transform(join_lines, "Join Lines")',
        )
        apply = methods["apply_text_transform"]
        self.assertIn("start, end = self.selected_or_all_range()", apply)
        self.assertIn(
            "return self.execute_command(command_name, edit, select_range=select)",
            apply,
        )

    def test_layer_dynamic_change_noop_and_existing_semantics(self):
        layer = CommandLayer(build_low_risk_registry())
        dirty = "inter-\nrotto su due\nrighe\n\naltro paragrafo\n"
        changed = layer.dispatch(
            "writing.join-lines",
            CommandContext(source="test", data={"text": dirty}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], join_lines(dirty))
        self.assertEqual(
            changed.value["text"],
            "interrotto su due righe\n\naltro paragrafo\n",
        )

        noop_text = "riga già unita\n"
        noop = layer.dispatch(
            "writing.join-lines",
            CommandContext(source="test", data={"text": noop_text}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], noop_text)

    def test_layer_matches_existing_pure_semantics_across_edge_cases(self):
        layer = CommandLayer(build_low_risk_registry())
        cases = [
            "",
            "a",
            "a\n",
            "a\nb",
            "a\r\nb\r\n",
            "a-\nb",
            "a-\nB",
            "a\n\nb",
            "a\n   \nb\n",
            "  a  \n  b  ",
            "uno\t\ndue",
            "à-\nè",
            "123-\n456",
            "\n\n",
        ]
        for text in cases:
            with self.subTest(text=repr(text)):
                expected = join_lines(text)
                result = layer.dispatch(
                    "writing.join-lines",
                    CommandContext(source="test", data={"text": text}),
                )
                self.assertTrue(result.success)
                self.assertEqual(result.value["text"], expected)
                self.assertEqual(result.changed, expected != text)

    def test_other_unwired_revise_transforms_remain_outside_dispatch_surface(self):
        source = BIN.read_text(encoding="utf-8")
        for forbidden in [
            '"writing.insert-date-time"',
        ]:
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
