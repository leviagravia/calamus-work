"""Headless regression for the W95 extensionless production-launcher loader."""
from __future__ import annotations

import ast
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "w95-true-gtk-app-gate.py"


class W95TrueGtkGateLoaderTests(unittest.TestCase):
    def test_gate_uses_source_file_loader_for_extensionless_launcher(self):
        source = GATE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        load_launcher = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "load_launcher"
        )
        calls = {
            ast.unparse(node.func)
            for node in ast.walk(load_launcher)
            if isinstance(node, ast.Call)
        }
        self.assertIn("importlib.machinery.SourceFileLoader", calls)
        self.assertIn("importlib.util.spec_from_loader", calls)
        self.assertNotIn("importlib.util.spec_from_file_location", calls)

    def test_source_file_loader_executes_a_file_without_py_suffix(self):
        with tempfile.TemporaryDirectory() as temporary:
            launcher = Path(temporary) / "launcher"
            launcher.write_text("VALUE = 95\n", encoding="utf-8")
            loader = importlib.machinery.SourceFileLoader(
                "w95_extensionless_loader_fixture", str(launcher)
            )
            spec = importlib.util.spec_from_loader(loader.name, loader)
            self.assertIsNotNone(spec)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            self.assertEqual(module.VALUE, 95)

    def test_editor_dialog_exposes_semantic_widget_names(self):
        source = (ROOT / "calamus" / "calamus_clip_dialogs.py").read_text(encoding="utf-8")
        self.assertIn('title_entry.set_name("calamus-clip-title-entry")', source)
        self.assertIn('shortcut_entry.set_name("calamus-clip-shortcut-entry")', source)
        self.assertIn('body.set_name("calamus-clip-body-view")', source)

    def test_gate_locates_editor_fields_semantically_not_by_entry_order(self):
        source = GATE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        exercise = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "exercise_editor_dialog"
        )
        function_source = ast.get_source_segment(source, exercise) or ""
        self.assertIn("find_named", function_source)
        self.assertIn("calamus-clip-title-entry", function_source)
        self.assertIn("calamus-clip-shortcut-entry", function_source)
        self.assertIn("calamus-clip-body-view", function_source)
        self.assertNotIn("entries[0]", function_source)
        self.assertNotIn("entries[1]", function_source)
        self.assertNotIn("text_views[0]", function_source)


if __name__ == "__main__":
    unittest.main()
