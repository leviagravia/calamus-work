from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
CATALOG = ROOT / "calamus" / "calamus_command_catalog.py"
HANDLERS = ROOT / "calamus" / "calamus_command_handlers.py"
WRITING = ROOT / "calamus" / "calamus_writing.py"
sys.path.insert(0, str(ROOT / "calamus"))

from calamus_command_catalog import build_low_risk_registry, low_risk_command_specs
from calamus_command_context import CommandContext
from calamus_command_handlers import handle_insert_date_time
from calamus_command_layer import CommandLayer
from calamus_writing import current_date_string


EXPECTED_DISPATCH_IDS = [
    "edit.lowercase",
    "edit.uppercase",
    "writing.clean-pdf",
    "writing.insert-date-time",
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


def source_and_app_methods() -> tuple[str, dict[str, str]]:
    source = BIN.read_text(encoding="utf-8")
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
    return source, methods


class InsertDateTimeLayerWiringTests(unittest.TestCase):
    def test_visible_menu_and_shortcut_use_existing_explicit_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "Insert Date/Time\\tCtrl+Alt+D", app.on_insert_datetime)',
            ui,
        )
        self.assertIn('("<Control><Alt>D", app.on_insert_datetime)', ui)
        self.assertEqual(ui.count("app.on_insert_datetime"), 2)

    def test_dispatch_surface_adds_only_insert_date_time(self):
        source = BIN.read_text(encoding="utf-8")
        dispatch_ids = re.findall(
            r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", source, flags=re.S
        )
        self.assertEqual(sorted(dispatch_ids), EXPECTED_DISPATCH_IDS)
        self.assertEqual(dispatch_ids.count("writing.insert-date-time"), 1)

    def test_catalog_promotes_existing_identity_to_pure_handler(self):
        specs = {spec.command_id: spec for spec in low_risk_command_specs()}
        spec = specs["writing.insert-date-time"]
        self.assertIsNotNone(spec.handler)
        self.assertIn("pure-handler", spec.flags)
        self.assertIn("text-insertion", spec.flags)
        self.assertNotIn("metadata-only", spec.flags)
        catalog = CATALOG.read_text(encoding="utf-8")
        self.assertIn('handler=pure_handler_for("writing.insert-date-time")', catalog)

    def test_handler_formats_only_explicit_time(self):
        layer = CommandLayer(build_low_risk_registry())
        now = datetime(2026, 7, 12, 19, 5, 9)
        default = layer.dispatch(
            "writing.insert-date-time",
            CommandContext(source="test", data={"now": now}),
        )
        self.assertTrue(default.success)
        self.assertTrue(default.changed)
        self.assertEqual(default.value, {"text": "2026-07-12 19:05"})

        custom = layer.dispatch(
            "writing.insert-date-time",
            CommandContext(
                source="test",
                data={"now": now, "format": "%d/%m/%Y %H:%M:%S"},
            ),
        )
        self.assertTrue(custom.success)
        self.assertEqual(custom.value, {"text": "12/07/2026 19:05:09"})

    def test_handler_rejects_implicit_or_invalid_time(self):
        layer = CommandLayer(build_low_risk_registry())
        missing = layer.dispatch(
            "writing.insert-date-time", CommandContext(source="test")
        )
        self.assertFalse(missing.success)
        self.assertEqual(missing.message, "Command failed: writing.insert-date-time")

        with self.assertRaisesRegex(TypeError, "now.*datetime"):
            handle_insert_date_time(
                CommandContext(source="test", data={"now": "2026-07-12"})
            )

        bad_format = layer.dispatch(
            "writing.insert-date-time",
            CommandContext(
                source="test", data={"now": datetime(2026, 7, 12), "format": 1}
            ),
        )
        self.assertFalse(bad_format.success)

    def test_date_formatter_is_deterministic_when_now_is_supplied(self):
        now = datetime(2026, 7, 12, 19, 5)
        self.assertEqual(current_date_string(now=now), "2026-07-12 19:05")
        self.assertEqual(
            current_date_string("%Y%m%d-%H%M", now=now), "20260712-1905"
        )
        with self.assertRaisesRegex(TypeError, "now must be a datetime"):
            current_date_string(now="not-a-datetime")
        with self.assertRaisesRegex(TypeError, "fmt must be a string"):
            current_date_string(123, now=now)

    def test_helper_is_compute_only_and_carries_explicit_time(self):
        _source, methods = source_and_app_methods()
        helper = methods["command_layer_insert_date_time_text"]
        self.assertIn('"writing.insert-date-time"', helper)
        self.assertIn('data={"now": now, "format": fmt}', helper)
        self.assertIn('result.value.get("text", "")', helper)
        for forbidden in [
            "datetime.now",
            "get_cursor_offset",
            "buffer_text",
            "command_insert_at",
            "insert_at_cursor",
            "execute_command",
            "get_buffer",
            "Gtk",
            "Gdk",
            "write_text_file",
        ]:
            self.assertNotIn(forbidden, helper)

    def test_entrypoint_acquires_time_then_uses_existing_insert_boundary(self):
        source, methods = source_and_app_methods()
        method = methods["on_insert_datetime"]
        self.assertIn(
            "txt, changed = self.command_layer_insert_date_time_text(datetime.now())",
            method,
        )
        self.assertIn("if not changed:\n            return False", method)
        self.assertIn("cursor = self.get_cursor_offset()", method)
        self.assertIn("command_insert_at(self.buffer_text(), cursor, txt)", method)
        self.assertIn("buf.insert_at_cursor(txt)", method)
        self.assertIn(
            'return self.execute_command("Insert Date/Time", edit, select_range=select)',
            method,
        )
        dispatch_pos = method.index("command_layer_insert_date_time_text")
        plan_pos = method.index("command_insert_at")
        edit_pos = method.index("def edit(buf):")
        execute_pos = method.index("return self.execute_command")
        self.assertLess(dispatch_pos, plan_pos)
        self.assertLess(plan_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)
        self.assertNotIn("current_date_string", method)
        self.assertNotIn("selected_or_all_range", method)
        self.assertNotIn("current_date_string", source.split("class App", 1)[0])

    def test_time_acquisition_formatting_and_mutation_are_separate(self):
        handlers = HANDLERS.read_text(encoding="utf-8")
        tree = ast.parse(handlers)
        function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "handle_insert_date_time"
        )
        segment = ast.get_source_segment(handlers, function)
        self.assertIn('context.get("now")', segment)
        self.assertIn("current_date_string(fmt=fmt, now=now)", segment)
        for forbidden in [
            "datetime.now",
            "Gtk",
            "Gdk",
            "get_buffer",
            "insert_at_cursor",
            "execute_command",
            "open(",
        ]:
            self.assertNotIn(forbidden, segment)

        writing = WRITING.read_text(encoding="utf-8")
        self.assertIn("moment = datetime.now() if now is None else now", writing)
        self.assertIn("return moment.strftime(fmt)", writing)


if __name__ == "__main__":
    unittest.main()
