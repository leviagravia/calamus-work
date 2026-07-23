import ast
import os
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
UI = (ROOT / "calamus" / "calamus_ui.py").read_text(encoding="utf-8")
REFERENCE_DIALOGS = (ROOT / "calamus" / "calamus_reference_dialogs.py").read_text(encoding="utf-8")
PROVENANCE = (ROOT / "scripts" / "prove-source-provenance.sh").read_text(encoding="utf-8")


class ResearchIntegrityCommandWiringTests(unittest.TestCase):
    def test_modules_exist_and_are_provenance_tracked(self):
        modules = (
            "calamus_reference_integrity",
            "calamus_research_integrity_controller",
            "calamus_research_integrity_dialogs",
            "calamus_research_integrity_runtime",
        )
        for module in modules:
            path = ROOT / "calamus" / f"{module}.py"
            self.assertTrue(path.is_file(), module)
            ast.parse(path.read_text(encoding="utf-8"))
            self.assertIn(f'"{module}"', PROVENANCE)

    def test_research_menu_exposes_only_two_new_on_demand_commands(self):
        rename = 'add_item(researchm, "Rename Reference Key…", app.on_rename_reference_key)'
        check = 'add_item(researchm, "Research Check…", app.on_research_check)'
        self.assertIn(rename, UI)
        self.assertIn(check, UI)
        self.assertLess(UI.index(rename), UI.index(check))
        self.assertNotIn("Rename Reference Key…\\t", UI)
        self.assertNotIn("Research Check…\\t", UI)

    def test_app_composes_authorities_and_keeps_wrappers_thin(self):
        tree = ast.parse(APP)
        app_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "App")
        methods = {node.name: node for node in app_class.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertIn("ResearchIntegrityController", APP)
        self.assertIn("ResearchIntegrityRuntime", APP)
        self.assertIn("reference_store=self.reference_store", APP)
        self.assertIn("reference_key_resolver=self.reference_panel_runtime.resolve_key", APP)
        for name in ("on_rename_reference_key", "on_research_check"):
            method = methods[name]
            self.assertLessEqual(method.end_lineno - method.lineno + 1, 3)
        replacement = ast.get_source_segment(APP, methods["replace_document_for_reference_migration"])
        self.assertIn('self.execute_command("Rename Reference Key", edit)', replacement)
        self.assertNotIn("set_text(", replacement)

    def test_generic_reference_dialog_cannot_edit_key_or_aliases(self):
        self.assertIn("key_entry.set_sensitive(False)", REFERENCE_DIALOGS)
        self.assertIn("Use Research → Rename Reference Key…", REFERENCE_DIALOGS)
        self.assertIn("aliases=record.aliases if record else ()", REFERENCE_DIALOGS)

    def test_transaction_and_check_remain_free_of_forbidden_ownership(self):
        files = (
            ROOT / "calamus" / "calamus_reference_integrity.py",
            ROOT / "calamus" / "calamus_research_integrity_controller.py",
        )
        combined = "\n".join(path.read_text(encoding="utf-8").casefold() for path in files)
        for forbidden in ("sqlite", "citeproc", "biber", "background thread", "pdf manager", "cloud"):
            self.assertNotIn(forbidden, combined)
        controller = files[1].read_text(encoding="utf-8")
        self.assertIn("expected_token", controller)
        self.assertNotIn("force=True", controller)
        self.assertIn("Nothing was written", controller)

    def test_source_note_alias_support_does_not_expand_canonical_options(self):
        source = (ROOT / "calamus" / "calamus_source_note_controller.py").read_text(encoding="utf-8")
        self.assertIn("reference_key_resolver", source)
        self.assertIn("return tuple(dict.fromkeys(self._reference_keys_provider()))", source)
        self.assertIn("self.resolve_reference_key(note.reference_key) is None", source)


if __name__ == "__main__":
    unittest.main()
