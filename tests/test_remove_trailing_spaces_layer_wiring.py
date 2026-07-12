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
from calamus_writing import remove_trailing_spaces


EXPECTED_DISPATCH_IDS = [
    "edit.lowercase",
    "edit.uppercase",
    "writing.clean-pdf",
    "writing.join-lines",
    "writing.reflow-paragraph",
    "writing.remove-extra-spaces",
    "writing.remove-trailing-spaces",
    "writing.smart-typography",
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


class RemoveTrailingSpacesLayerWiringTests(unittest.TestCase):
    def test_command_is_visible_and_uses_explicit_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "Remove Trailing Spaces", app.on_remove_trailing_spaces)',
            ui,
        )
        self.assertEqual(ui.count("app.on_remove_trailing_spaces"), 1)
        self.assertNotIn(
            'add_item(revisem, "Remove Trailing Spaces", lambda *_: app.apply_text_transform',
            ui,
        )

    def test_dispatch_surface_adds_only_remove_trailing_spaces(self):
        source = BIN.read_text(encoding="utf-8")
        dispatch_ids = re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", source, flags=re.S)
        self.assertEqual(sorted(dispatch_ids), EXPECTED_DISPATCH_IDS)

    def test_helper_is_compute_only(self):
        _source, methods = app_methods()
        helper = methods["command_layer_remove_trailing_spaces_text"]
        self.assertIn('"writing.remove-trailing-spaces"', helper)
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
            "write_text_file",
        ]:
            self.assertNotIn(forbidden, helper)

    def test_apply_text_transform_routes_command_before_mutation(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("use_layer_remove_trailing_spaces", apply)
        self.assertIn('command_name == "Remove Trailing Spaces"', apply)
        self.assertIn("transform is remove_trailing_spaces", apply)
        self.assertIn("command_layer_remove_trailing_spaces_text(old)", apply)
        branch_pos = apply.index("elif use_layer_remove_trailing_spaces:")
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
        method = methods["on_remove_trailing_spaces"]
        self.assertEqual(
            method.strip(),
            'def on_remove_trailing_spaces(self, *_):\n'
            '        return self.apply_text_transform(remove_trailing_spaces, "Remove Trailing Spaces")',
        )
        apply = methods["apply_text_transform"]
        self.assertIn("start, end = self.selected_or_all_range()", apply)
        self.assertIn(
            "return self.execute_command(command_name, edit, select_range=select)",
            apply,
        )

    def test_layer_dynamic_change_noop_and_existing_semantics(self):
        layer = CommandLayer(build_low_risk_registry())
        dirty = "alpha  \n beta\t\nempty   \nclean\n"
        changed = layer.dispatch(
            "writing.remove-trailing-spaces",
            CommandContext(source="test", data={"text": dirty}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], remove_trailing_spaces(dirty))
        self.assertEqual(changed.value["text"], "alpha\n beta\nempty\nclean\n")

        noop_text = "alpha\n beta\nempty\nclean\n"
        noop = layer.dispatch(
            "writing.remove-trailing-spaces",
            CommandContext(source="test", data={"text": noop_text}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], noop_text)

    def test_layer_matches_existing_pure_semantics_across_edge_cases(self):
        layer = CommandLayer(build_low_risk_registry())
        cases = [
            "",
            "   ",
            "\t\t",
            "a",
            " a ",
            "a   b",
            "a\t\tb",
            "a  \n b\t\n",
            "a  \r\nb\t\r\n",
            "a\u00a0\n",
            "\n\n",
            "alpha beta\n",
            "alpha beta   ",
        ]
        for text in cases:
            with self.subTest(text=repr(text)):
                expected = remove_trailing_spaces(text)
                result = layer.dispatch(
                    "writing.remove-trailing-spaces",
                    CommandContext(source="test", data={"text": text}),
                )
                self.assertTrue(result.success)
                self.assertEqual(result.value["text"], expected)
                self.assertEqual(result.changed, expected != text)

    def test_algorithm_and_command_layer_remain_gtk_and_file_free(self):
        writing = (ROOT / "calamus" / "calamus_writing.py").read_text(encoding="utf-8")
        tree = ast.parse(writing)
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "remove_trailing_spaces"
        )
        segment = ast.get_source_segment(writing, function)
        self.assertIn("line.rstrip()", segment)
        self.assertIn("preserve_final_newline(text, out)", segment)
        for forbidden in ["Gtk", "Gdk", "open(", "write_text_file", "get_buffer"]:
            self.assertNotIn(forbidden, segment)

    def test_other_unwired_revise_transforms_remain_outside_dispatch_surface(self):
        source = BIN.read_text(encoding="utf-8")
        for forbidden in [
            '"writing.sort-lines"',
            '"writing.sentence-case"',
        ]:
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
