import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
UI = (ROOT / "calamus" / "calamus_ui.py").read_text(encoding="utf-8")
SHORTCUTS = (ROOT / "calamus" / "calamus_shortcuts.py").read_text(encoding="utf-8")
PROVENANCE = (ROOT / "scripts" / "prove-source-provenance.sh").read_text(encoding="utf-8")


class TagIntegrityCommandWiringTests(unittest.TestCase):
    def test_modules_exist_compile_and_are_provenance_tracked(self):
        for module in (
            "calamus_tag_integrity",
            "calamus_tag_integrity_controller",
            "calamus_tag_integrity_dialogs",
            "calamus_tag_integrity_runtime",
        ):
            path = ROOT / "calamus" / f"{module}.py"
            self.assertTrue(path.is_file())
            ast.parse(path.read_text(encoding="utf-8"))
            self.assertIn(f'"{module}"', PROVENANCE)

    def test_research_menu_exposes_one_menu_only_command(self):
        line = 'add_item(researchm, "Tag Integrity…", app.on_tag_integrity)'
        self.assertEqual(UI.count(line), 1)
        self.assertIn('ShortcutSpec("Research", "Tag Integrity", "menu")', SHORTCUTS)
        self.assertNotIn("Tag Integrity…\\t", UI)

    def test_app_gateway_is_thin_and_composes_existing_authorities(self):
        tree = ast.parse(APP)
        app_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "App")
        methods = {node.name: node for node in app_class.body if isinstance(node, ast.FunctionDef)}
        method = methods["on_tag_integrity"]
        self.assertLessEqual(method.end_lineno - method.lineno + 1, 3)
        self.assertIn("TagIntegrityController", APP)
        self.assertIn("TagIntegrityRuntime", APP)
        self.assertIn("reference_store=self.reference_store", APP)
        self.assertIn("document_path_provider=lambda: self.document.file_path", APP)
        self.assertIn("self.tag_integrity_runtime.manage()", ast.get_source_segment(APP, method))

    def test_pure_projection_has_no_gtk_or_persistence(self):
        pure = (ROOT / "calamus" / "calamus_tag_integrity.py").read_text(encoding="utf-8").casefold()
        for forbidden in (
            "gi.repository", "gtk", "open(", "atomic_write", "sqlite", "json.dump",
            "cloud", "background thread", "zotero", "jabref",
        ):
            self.assertNotIn(forbidden, pure)

    def test_color_is_derived_and_no_third_authority_exists(self):
        combined = "\n".join(
            (ROOT / "calamus" / name).read_text(encoding="utf-8").casefold()
            for name in (
                "calamus_tag_integrity.py",
                "calamus_tag_integrity_controller.py",
                "calamus_tag_integrity_dialogs.py",
                "calamus_tag_integrity_runtime.py",
            )
        )
        self.assertIn("not persisted", combined)
        for forbidden in ("tags.json", "tag-colors.md", "tag registry file", "persistent color", "save_color"):
            self.assertNotIn(forbidden, combined)

    def test_controller_uses_tokens_atomic_stores_and_compensating_rollback(self):
        controller = (ROOT / "calamus" / "calamus_tag_integrity_controller.py").read_text(encoding="utf-8")
        self.assertIn("reference_token", controller)
        self.assertIn("source_note_token", controller)
        self.assertIn("scratchpad_token", controller)
        self.assertIn("_rollback_references", controller)
        self.assertIn("_rollback_after_scratchpad_failure", controller)
        self.assertNotIn("force=True", controller)
        self.assertIn("Nothing was written", controller)


if __name__ == "__main__":
    unittest.main()
