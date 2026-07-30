"""Regression for the R5 True GTK cursor-extremes gate."""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "w95-true-gtk-app-gate.py"


class W95R5TrueGtkCursorGateTests(unittest.TestCase):
    def _exercise_source(self) -> str:
        source = GATE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        node = next(
            item for item in tree.body
            if isinstance(item, ast.FunctionDef) and item.name == "exercise_cursor_extremes"
        )
        return ast.get_source_segment(source, node) or ""

    def test_cursor_extremes_use_the_production_insertion_gateway(self):
        source = self._exercise_source()
        self.assertIn("insert_clip_expansion", source)
        self.assertIn("expand_clip_text", source)
        self.assertNotIn("controller.create", source)
        self.assertNotIn("controller.select_id", source)
        self.assertNotIn("clip_collection_runtime.on_insert", source)

    def test_end_to_end_listbox_wiring_remains_covered_separately(self):
        source = GATE.read_text(encoding="utf-8")
        self.assertIn('emit("row-activated", row)', source)
        self.assertIn("row-activated did not use the production insert gateway", source)

    def test_failures_include_expected_and_actual_diagnostics(self):
        source = self._exercise_source()
        self.assertIn("expected={expected_text!r}", source)
        self.assertIn("actual={actual_text!r}", source)
        self.assertIn("expected={expected_caret}", source)
        self.assertIn("actual={actual_caret}", source)


if __name__ == "__main__":
    unittest.main()
