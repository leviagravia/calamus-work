from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "17b409a05f356477173b2bdd348a67a4cf01f43c"


class W102DocumentSessionContractTests(unittest.TestCase):
    def test_identity_is_exact(self):
        text = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        for token in (
            'DEVELOPMENT_BUILD_LABEL = "Development build"',
            'DEVELOPMENT_WORK_ITEM = "W102"',
            'DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Document Session Extraction"',
            f'PUBLISHED_BASELINE = "{BASELINE}"',
        ):
            self.assertIn(token, text)

    def test_session_modules_are_provenance_tracked(self):
        provenance = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
        for module in (
            "calamus_document_session",
            "calamus_document_session_controller",
            "calamus_document_session_composition",
        ):
            self.assertIn(f'"{module}"', provenance)

    def test_session_modules_are_gtk_free(self):
        for rel in (
            "calamus/calamus_document_session.py",
            "calamus/calamus_document_session_controller.py",
            "calamus/calamus_document_session_composition.py",
        ):
            source = (ROOT / rel).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports), rel)

    def test_app_has_read_only_session_projections_and_no_assignments(self):
        source = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        tree = ast.parse(source)
        app = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "App")
        properties = {
            node.name for node in app.body
            if isinstance(node, ast.FunctionDef)
            and any(isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list)
        }
        self.assertTrue({"document", "current_file", "modified", "loading"}.issubset(properties))
        forbidden = []
        for node in ast.walk(app):
            targets = []
            if isinstance(node, ast.Assign): targets = node.targets
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)): targets = [node.target]
            for target in targets:
                for child in ast.walk(target):
                    if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
                        if child.value.id == "self" and child.attr in {"current_file", "modified", "loading", "document"}:
                            forbidden.append((child.attr, node.lineno))
        self.assertEqual(forbidden, [])

    def test_true_app_fixtures_use_session_authority_not_read_only_app_projections(self):
        targets = (
            "scripts/w95-true-gtk-app-gate.py",
            "tests/test_w98_research_panel_app_desktop_e2e.py",
            "tests/test_workspace_app_desktop_e2e.py",
        )
        forbidden = {"modified", "current_file", "loading", "document"}
        violations = []
        for rel in targets:
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"), filename=rel)
            for node in ast.walk(tree):
                assignment_targets = []
                if isinstance(node, ast.Assign):
                    assignment_targets = node.targets
                elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                    assignment_targets = [node.target]
                for target in assignment_targets:
                    for child in ast.walk(target):
                        if (
                            isinstance(child, ast.Attribute)
                            and isinstance(child.value, ast.Name)
                            and child.value.id in {"app", "win"}
                            and child.attr in forbidden
                        ):
                            violations.append((rel, child.value.id, child.attr, node.lineno))
        self.assertEqual(violations, [])

    def test_workspace_reads_session_port_not_app_alias(self):
        source = (ROOT / "calamus/calamus_application_composition.py").read_text(encoding="utf-8")
        self.assertIn("current_document_path=document_session.session.current_path", source)
        self.assertNotIn("current_document_path=lambda: app.current_file", source)

    def test_core_build_order_begins_with_document_session(self):
        source = (ROOT / "calamus/calamus_application_composition.py").read_text(encoding="utf-8")
        self.assertLess(source.index('"document-session"'), source.index('"editor-infrastructure"'))
        self.assertIn("document_session=document_session", source)

    def test_transition_entrypoints_delegate_to_controller(self):
        source = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        for token in (
            "self.document_session_controller.execute_new(plan)",
            "self.document_session_controller.open_path(path)",
            "self.document_session_controller.execute_open(plan)",
            "self.document_session_controller.execute_save(plan)",
            "self.document_session.rebind_path(identity.current_file_after)",
            "self.document_session.detach(current_text)",
        ):
            self.assertIn(token, source)

    def test_no_new_persistence_or_feature_scope(self):
        for rel in (
            "calamus/calamus_document_session.py",
            "calamus/calamus_document_session_controller.py",
            "calamus/calamus_document_session_composition.py",
        ):
            source = (ROOT / rel).read_text(encoding="utf-8").lower()
            for forbidden in ("webkit", "sqlite", "autosave", "recovery journal", "tabview"):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
