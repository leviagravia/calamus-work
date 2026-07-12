from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BIN_CALAMUS = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
sys.path.insert(0, str(ROOT / "calamus"))

from calamus_command_catalog import build_low_risk_registry
from calamus_command_context import CommandContext
from calamus_command_layer import CommandLayer


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


def _source() -> str:
    return BIN_CALAMUS.read_text(encoding="utf-8")


def _app_methods() -> dict[str, str]:
    source = _source()
    tree = ast.parse(source)
    lines = source.splitlines()
    methods: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    methods[child.name] = "\n".join(
                        lines[child.lineno - 1 : child.end_lineno]
                    )
    return methods


def _dispatch_ids() -> list[str]:
    return re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", _source(), flags=re.S)


class UppercaseLayerWiringTests(unittest.TestCase):
    def test_visible_menu_and_shortcut_use_one_explicit_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "UPPERCASE (convert selected)\\tCtrl+Alt+U", app.on_uppercase)',
            ui,
        )
        self.assertIn('("<Control><Alt>U", app.on_uppercase)', ui)
        self.assertEqual(ui.count("app.on_uppercase"), 2)
        self.assertNotIn(
            'lambda *_: app.replace_selection(str.upper)',
            ui,
        )

    def test_lowercase_visible_paths_remain_deferred_and_unchanged(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "Lowercase (convert selected)\\tCtrl+Alt+Shift+U", '
            'lambda *_: app.replace_selection(str.lower))',
            ui,
        )
        self.assertIn(
            '("<Control><Alt><Shift>U", lambda *_: app.replace_selection(str.lower))',
            ui,
        )
        self.assertNotIn("app.on_lowercase", ui)

    def test_dispatch_surface_is_unchanged_because_uppercase_id_already_existed(self):
        self.assertEqual(sorted(_dispatch_ids()), EXPECTED_DISPATCH_IDS)
        self.assertEqual(_dispatch_ids().count("edit.uppercase"), 1)

    def test_command_layer_uppercase_helper_is_compute_only(self):
        method = _app_methods()["command_layer_uppercase_text"]
        self.assertIn('self.command_layer.dispatch(\n            "edit.uppercase"', method)
        self.assertIn(
            'CommandContext(app=self, source="gui", data={"text": text})',
            method,
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
            "get_buffer",
            "selected_or_all_range",
            "Clipboard",
            "write_text_file",
        ]:
            self.assertNotIn(forbidden, method)

    def test_replace_selection_preserves_selection_only_policy(self):
        method = _app_methods()["replace_selection"]
        guard_pos = method.index("if not b.get_has_selection():")
        bounds_pos = method.index("s, e = b.get_selection_bounds()")
        dispatch_pos = method.index("self.command_layer_uppercase_text(txt)")
        edit_pos = method.index("def edit(buf):")
        self.assertLess(guard_pos, bounds_pos)
        self.assertLess(bounds_pos, dispatch_pos)
        self.assertLess(dispatch_pos, edit_pos)
        self.assertIn("return False", method[guard_pos:bounds_pos])
        self.assertNotIn("selected_or_all_range", method)
        self.assertNotIn("get_bounds()", method)

    def test_replace_selection_routes_only_uppercase_before_mutation(self):
        method = _app_methods()["replace_selection"]
        self.assertIn('command_name="Replace Selection"', method)
        self.assertIn("use_layer_uppercase", method)
        self.assertIn(
            'command_name in {"Uppercase", "Upper Case", "UPPERCASE"}',
            method,
        )
        self.assertIn("transform is str.upper", method)
        self.assertIn("replacement, changed = self.command_layer_uppercase_text(txt)", method)
        self.assertIn("else:\n            replacement = transform(txt)", method)
        self.assertNotIn("command_layer_lowercase_text", method)
        self.assertNotIn('"edit.lowercase"', method)

        dispatch_pos = method.index("self.command_layer_uppercase_text(txt)")
        plan_pos = method.index("command_replace_range(")
        edit_pos = method.index("def edit(buf):")
        execute_pos = method.index("return self.execute_command")
        self.assertLess(dispatch_pos, plan_pos)
        self.assertLess(plan_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)

    def test_uppercase_noop_guard_precedes_plan_and_mutation(self):
        method = _app_methods()["replace_selection"]
        branch_pos = method.index("if use_layer_uppercase:")
        guard_pos = method.index("if not changed:", branch_pos)
        plan_pos = method.index("command_replace_range(")
        edit_pos = method.index("def edit(buf):")
        self.assertLess(branch_pos, guard_pos)
        self.assertLess(guard_pos, plan_pos)
        self.assertLess(plan_pos, edit_pos)
        self.assertIn("return False", method[guard_pos:plan_pos])

    def test_visible_entrypoint_uses_selection_boundary_and_command_name(self):
        method = _app_methods()["on_uppercase"]
        self.assertEqual(
            method.strip(),
            'def on_uppercase(self, *_):\n'
            '        return self.replace_selection(str.upper, "Uppercase")',
        )
        self.assertNotIn("apply_text_transform", method)
        self.assertNotIn("selected_or_all_range", method)

    def test_generic_replace_selection_users_keep_default_path(self):
        methods = _app_methods()
        replace_selection = methods["replace_selection"]
        character_map = methods["on_character_map"]
        self.assertIn('command_name="Replace Selection"', replace_selection)
        self.assertIn("else:\n            replacement = transform(txt)", replace_selection)
        self.assertIn(
            "return self.execute_command(command_name, edit, select_range=select)",
            replace_selection,
        )
        self.assertIn("self.replace_selection(lambda _old, c=ch: c)", character_map)

    def test_existing_selection_or_document_uppercase_bridge_remains_available(self):
        method = _app_methods()["apply_text_transform"]
        self.assertIn("use_layer_uppercase", method)
        self.assertIn("command_layer_uppercase_text(old)", method)
        self.assertIn("transform is str.upper", method)
        self.assertIn(
            'command_name in {"Uppercase", "Upper Case", "UPPERCASE"}',
            method,
        )
        self.assertIn("return self.execute_command(command_name, edit, select_range=select)", method)

    def test_layer_uppercase_dynamic_unicode_noop_and_change(self):
        layer = CommandLayer(build_low_risk_registry())
        cases = [
            ("abc È già", "ABC È GIÀ", True),
            ("ABC È GIÀ", "ABC È GIÀ", False),
            ("straße", "STRASSE", True),
            ("l'albero\nàéîöü", "L'ALBERO\nÀÉÎÖÜ", True),
            ("123 !?\t", "123 !?\t", False),
            ("", "", False),
        ]
        for original, expected, changed in cases:
            with self.subTest(original=original):
                result = layer.dispatch(
                    "edit.uppercase",
                    CommandContext(source="test", data={"text": original}),
                )
                self.assertTrue(result.success)
                self.assertEqual(result.value["text"], expected)
                self.assertEqual(result.changed, changed)

    def test_insert_datetime_remains_outside_dispatch_surface(self):
        self.assertNotIn('"writing.insert-date-time"', _source())


if __name__ == "__main__":
    unittest.main()
