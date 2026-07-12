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
from calamus_writing import sort_lines


EXPECTED_DISPATCH_IDS = [
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


class SortLinesAscendingLayerWiringTests(unittest.TestCase):
    def test_visible_menu_and_shortcut_use_one_explicit_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "Sort Alphabetically A-Z\\tCtrl+Alt+Up", app.on_sort_lines_ascending)',
            ui,
        )
        self.assertIn('("<Control><Alt>Up", app.on_sort_lines_ascending)', ui)
        self.assertEqual(ui.count("app.on_sort_lines_ascending"), 2)
        self.assertNotIn(
            'lambda *_: app.apply_text_transform(lambda t: sort_lines(t, reverse=False), "Sort A-Z")',
            ui,
        )

    def test_descending_visible_command_remains_untouched_and_unpromoted(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "Sort Alphabetically Z-A\\tCtrl+Alt+Down", lambda *_: app.apply_text_transform(lambda t: sort_lines(t, reverse=True), "Sort Z-A"))',
            ui,
        )
        self.assertIn(
            '("<Control><Alt>Down", lambda *_: app.apply_text_transform(lambda t: sort_lines(t, reverse=True), "Sort Z-A"))',
            ui,
        )
        source = BIN.read_text(encoding="utf-8")
        self.assertNotIn("on_sort_lines_descending", source)
        self.assertNotIn('command_name == "Sort Z-A"', source)

    def test_dispatch_surface_adds_only_sort_lines(self):
        source = BIN.read_text(encoding="utf-8")
        dispatch_ids = re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", source, flags=re.S)
        self.assertEqual(sorted(dispatch_ids), EXPECTED_DISPATCH_IDS)
        self.assertEqual(dispatch_ids.count("writing.sort-lines"), 1)

    def test_helper_is_compute_only_and_ascending_specific(self):
        _source, methods = app_methods()
        helper = methods["command_layer_sort_lines_ascending_text"]
        self.assertIn('"writing.sort-lines"', helper)
        self.assertIn(
            'CommandContext(app=self, source="gui", data={"text": text})',
            helper,
        )
        self.assertNotIn("reverse", helper)
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

    def test_apply_text_transform_routes_ascending_before_mutation(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("use_layer_sort_lines_ascending", apply)
        self.assertIn('command_name == "Sort A-Z"', apply)
        self.assertIn("command_layer_sort_lines_ascending_text(old)", apply)
        self.assertNotIn('command_name == "Sort Z-A"', apply)
        branch_pos = apply.index("elif use_layer_sort_lines_ascending:")
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
        method = methods["on_sort_lines_ascending"]
        self.assertEqual(
            method.strip(),
            'def on_sort_lines_ascending(self, *_):\n'
            '        return self.apply_text_transform(lambda t: sort_lines(t, reverse=False), "Sort A-Z")',
        )
        apply = methods["apply_text_transform"]
        self.assertIn("start, end = self.selected_or_all_range()", apply)
        self.assertIn(
            "return self.execute_command(command_name, edit, select_range=select)",
            apply,
        )

    def test_layer_dynamic_change_noop_and_existing_semantics(self):
        layer = CommandLayer(build_low_risk_registry())
        source = "zeta\nAlfa\nbeta\n"
        changed = layer.dispatch(
            "writing.sort-lines",
            CommandContext(source="test", data={"text": source}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], sort_lines(source, reverse=False))
        self.assertEqual(changed.value["text"], "Alfa\nbeta\nzeta\n")

        noop_text = "Alfa\nbeta\nzeta\n"
        noop = layer.dispatch(
            "writing.sort-lines",
            CommandContext(source="test", data={"text": noop_text}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], noop_text)

    def test_layer_matches_existing_pure_semantics_across_edge_cases(self):
        layer = CommandLayer(build_low_risk_registry())
        cases = [
            "",
            "single",
            "b\na",
            "b\na\n",
            "Beta\nalfa\nALFA",
            "è\nÈ\na",
            "10\n2\n1",
            "\n",
            "b\n\na\n",
            "  b\n a",
        ]
        for text in cases:
            with self.subTest(text=repr(text)):
                expected = sort_lines(text, reverse=False)
                result = layer.dispatch(
                    "writing.sort-lines",
                    CommandContext(source="test", data={"text": text}),
                )
                self.assertTrue(result.success)
                self.assertEqual(result.value["text"], expected)
                self.assertEqual(result.changed, expected != text)

    def test_algorithm_catalog_and_handler_are_still_pure_boundaries(self):
        writing = (ROOT / "calamus" / "calamus_writing.py").read_text(encoding="utf-8")
        tree = ast.parse(writing)
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "sort_lines"
        )
        segment = ast.get_source_segment(writing, function)
        self.assertIn("sorted(lines, key=key, reverse=reverse)", segment)
        self.assertIn("preserve_final_newline", segment)
        for forbidden in ["Gtk", "Gdk", "open(", "write_text_file", "get_buffer"]:
            self.assertNotIn(forbidden, segment)

    def test_sentence_case_remains_outside_gui_dispatch_surface(self):
        source = BIN.read_text(encoding="utf-8")
        self.assertNotIn('"writing.sentence-case"', source)


if __name__ == "__main__":
    unittest.main()
