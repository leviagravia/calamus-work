from pathlib import Path
import ast
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
HANDLERS = ROOT / "calamus" / "calamus_command_handlers.py"
sys.path.insert(0, str(ROOT / "calamus"))

from calamus_command_catalog import build_low_risk_registry
from calamus_command_context import CommandContext
from calamus_command_handlers import handle_sort_lines
from calamus_command_layer import CommandLayer
from calamus_writing import sort_lines


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


class SortLinesDescendingLayerWiringTests(unittest.TestCase):
    def test_visible_menu_and_shortcut_use_one_explicit_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "Sort Alphabetically Z-A\\tCtrl+Alt+Down", app.on_sort_lines_descending)',
            ui,
        )
        self.assertIn('("<Control><Alt>Down", app.on_sort_lines_descending)', ui)
        self.assertEqual(ui.count("app.on_sort_lines_descending"), 2)
        self.assertNotIn(
            'lambda *_: app.apply_text_transform(lambda t: sort_lines(t, reverse=True), "Sort Z-A")',
            ui,
        )

    def test_entrypoint_is_visible_command_specific(self):
        _source, methods = app_methods()
        method = methods["on_sort_lines_descending"]
        self.assertEqual(
            method.strip(),
            'def on_sort_lines_descending(self, *_):\n'
            '        return self.apply_text_transform(lambda t: sort_lines(t, reverse=True), "Sort Z-A")',
        )
        self.assertNotIn("Gtk", method)
        self.assertNotIn("get_buffer", method)

    def test_apply_text_transform_routes_descending_before_mutation(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn('command_name in {"Sort A-Z", "Sort Z-A"}', apply)
        self.assertIn('reverse=(command_name == "Sort Z-A")', apply)
        branch_pos = apply.index("elif use_layer_sort_lines:")
        edit_pos = apply.index("def edit(buf):")
        execute_pos = apply.index("return self.execute_command")
        self.assertLess(branch_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)
        self.assertIn("if not changed:\n                return False", apply)

    def test_shared_helper_carries_reverse_in_command_context(self):
        _source, methods = app_methods()
        helper = methods["command_layer_sort_lines_text"]
        self.assertIn("reverse=False", helper)
        self.assertIn('data={"text": text, "reverse": reverse}', helper)
        self.assertEqual(helper.count('"writing.sort-lines"'), 1)
        for forbidden in [
            "selected_or_all_range",
            "get_buffer",
            "execute_command",
            "begin_user_action",
            "end_user_action",
            ".delete(",
            ".insert(",
        ]:
            self.assertNotIn(forbidden, helper)

    def test_handler_owns_direction_validation_not_gui_mutation(self):
        source = HANDLERS.read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "handle_sort_lines"
        )
        segment = ast.get_source_segment(source, function)
        self.assertIn('reverse = context.get("reverse", False)', segment)
        self.assertIn("isinstance(reverse, bool)", segment)
        self.assertIn("sort_lines(original, reverse=reverse)", segment)
        for forbidden in ["Gtk", "Gdk", "get_buffer", "execute_command", "open("]:
            self.assertNotIn(forbidden, segment)

    def test_layer_descending_dynamic_change_and_noop(self):
        layer = CommandLayer(build_low_risk_registry())
        source = "Alfa\nbeta\nzeta\n"
        changed = layer.dispatch(
            "writing.sort-lines",
            CommandContext(source="test", data={"text": source, "reverse": True}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], "zeta\nbeta\nAlfa\n")
        self.assertEqual(changed.value["text"], sort_lines(source, reverse=True))

        noop_text = "zeta\nbeta\nAlfa\n"
        noop = layer.dispatch(
            "writing.sort-lines",
            CommandContext(source="test", data={"text": noop_text, "reverse": True}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], noop_text)

    def test_layer_descending_matches_existing_semantics_across_edge_cases(self):
        layer = CommandLayer(build_low_risk_registry())
        cases = [
            "",
            "single",
            "a\nb",
            "a\nb\n",
            "Beta\nalfa\nALFA",
            "a\nÈ\nè",
            "1\n2\n10",
            "\n",
            "a\n\nb\n",
            " a\n  b",
        ]
        for text in cases:
            with self.subTest(text=repr(text)):
                expected = sort_lines(text, reverse=True)
                result = layer.dispatch(
                    "writing.sort-lines",
                    CommandContext(source="test", data={"text": text, "reverse": True}),
                )
                self.assertTrue(result.success)
                self.assertEqual(result.value["text"], expected)
                self.assertEqual(result.changed, expected != text)

    def test_invalid_reverse_type_is_structured_failure(self):
        context = CommandContext(
            source="test", data={"text": "b\na", "reverse": "yes"}
        )
        with self.assertRaisesRegex(TypeError, "reverse.*boolean"):
            handle_sort_lines(context)

        layer = CommandLayer(build_low_risk_registry())
        result = layer.dispatch("writing.sort-lines", context)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Command failed: writing.sort-lines")

    def test_ascending_default_remains_unchanged(self):
        layer = CommandLayer(build_low_risk_registry())
        text = "z\na\nb\n"
        implicit = layer.dispatch(
            "writing.sort-lines",
            CommandContext(source="test", data={"text": text}),
        )
        explicit = layer.dispatch(
            "writing.sort-lines",
            CommandContext(source="test", data={"text": text, "reverse": False}),
        )
        self.assertTrue(implicit.success)
        self.assertTrue(explicit.success)
        self.assertEqual(implicit.value, explicit.value)
        self.assertEqual(implicit.value["text"], sort_lines(text, reverse=False))

    def test_selection_mutation_and_lifecycle_remain_owned_by_app(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("start, end = self.selected_or_all_range()", apply)
        self.assertIn("def edit(buf):", apply)
        self.assertIn("buf.delete(it1, it2)", apply)
        self.assertIn("buf.insert(buf.get_iter_at_offset(start), new)", apply)
        self.assertIn(
            "return self.execute_command(command_name, edit, select_range=select)",
            apply,
        )
        helper = methods["command_layer_sort_lines_text"]
        self.assertNotIn("selected_or_all_range", helper)
        self.assertNotIn("execute_command", helper)

    def test_insert_datetime_is_now_an_approved_gui_dispatch(self):
        source = BIN.read_text(encoding="utf-8")
        self.assertIn('"writing.insert-date-time"', source)


if __name__ == "__main__":
    unittest.main()
