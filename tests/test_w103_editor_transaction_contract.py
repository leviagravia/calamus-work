from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "c8ee3d5970a0cb1d05e4c4320a2117fe7e493368"


class W103EditorTransactionContractTests(unittest.TestCase):
    def test_identity_is_exact(self):
        source = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        contract = (ROOT / "docs/canonical/CALAMUS_W103_EDITOR_TRANSACTION_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn(BASELINE, contract)
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W105"', source)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Menu and UI-State Decoupling"', source)
        self.assertIn('PUBLISHED_BASELINE = "92aa832c6b72cb7a81a5a44c656890ec602d9d41"', source)

    def test_transaction_controller_is_gtk_free(self):
        source = (ROOT / "calamus/calamus_editor_transaction.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports))
        forbidden_names = {"Gtk", "Gdk", "Pango", "PangoCairo"}
        referenced = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertTrue(forbidden_names.isdisjoint(referenced))

    def test_app_has_read_only_restoring_projection_and_no_assignment(self):
        tree = ast.parse((ROOT / "bin/calamus").read_text(encoding="utf-8"))
        app = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "App")
        properties = {
            node.name for node in app.body
            if isinstance(node, ast.FunctionDef)
            and any(isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list)
        }
        self.assertIn("restoring_undo", properties)
        violations = []
        for node in ast.walk(app):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign)) else []
            for target in targets:
                for child in ast.walk(target):
                    if (
                        isinstance(child, ast.Attribute)
                        and isinstance(child.value, ast.Name)
                        and child.value.id == "self"
                        and child.attr == "restoring_undo"
                    ):
                        violations.append(node.lineno)
        self.assertEqual(violations, [])

    def test_core_composition_builds_typed_transaction_boundary(self):
        composition = (ROOT / "calamus/calamus_application_composition.py").read_text(encoding="utf-8")
        components = (ROOT / "calamus/calamus_application_components.py").read_text(encoding="utf-8")
        self.assertIn('"editor-transaction"', composition)
        self.assertIn("build_editor_transaction_components", composition)
        self.assertIn("editor_transaction=editor_transaction", composition)
        self.assertIn("class EditorTransactionCompositionInput", components)
        self.assertIn("class EditorTransactionComponents", components)

    def test_app_gateways_delegate_to_transaction_authority(self):
        source = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        for token in (
            "self.editor_transaction.execute_command(",
            "self.editor_transaction.undo()",
            "self.editor_transaction.redo()",
            "self.editor_transaction.restore_history_state(",
            "self.editor_transaction.observe_buffer_change()",
        ):
            self.assertIn(token, source)
        self.assertNotIn("restore_buffer_state(self.text", source)

    def test_editor_mutations_cannot_bypass_transaction_boundary(self):
        source = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        tree = ast.parse(source)
        app = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "App")
        violations = []
        for method in app.body:
            if not isinstance(method, ast.FunctionDef):
                continue
            method_source = ast.get_source_segment(source, method) or ""
            editor_writes = []
            for node in ast.walk(method):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in {"insert", "delete", "set_text", "cut_clipboard", "paste_clipboard"}:
                    continue
                receiver = ast.get_source_segment(source, node.func.value) or ""
                if receiver in {"buf", "buffer"} or receiver == "self.text.get_buffer()":
                    editor_writes.append((node.lineno, node.func.attr, receiver))
            if not editor_writes:
                continue
            if method.name == "_replace_buffer_text_raw":
                if all(attr == "set_text" for _line, attr, _receiver in editor_writes):
                    continue
            if "self.execute_command(" not in method_source:
                violations.append((method.name, editor_writes))
        self.assertEqual(violations, [])
        self.assertIn("self.editor_transaction.cut_clipboard(", source)
        self.assertIn("self.editor_transaction.paste_clipboard(", source)
        self.assertNotIn("self.text.get_buffer().cut_clipboard", source)
        self.assertNotIn("self.text.get_buffer().paste_clipboard", source)

    def test_w104_scope_is_not_implemented(self):
        for rel in (
            "calamus/calamus_editor_transaction.py",
            "calamus/calamus_editor_buffer_adapter.py",
            "calamus/calamus_editor_transaction_composition.py",
        ):
            source = (ROOT / rel).read_text(encoding="utf-8")
            for forbidden in ("CommandRegistry", "Gio.SimpleAction", "accelerator_map", "menu_registry"):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
