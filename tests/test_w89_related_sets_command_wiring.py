from pathlib import Path
import unittest
from tests.w104_command_test_support import guide_has

from calamus_help import load_user_guide, parse_user_guide_sections


ROOT = Path(__file__).resolve().parents[1]


class W89RelatedSetsCommandWiringTests(unittest.TestCase):
    def test_research_menu_and_app_register_reference_sets(self):
        app = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        ui = (ROOT / "calamus/calamus_ui.py").read_text(encoding="utf-8")
        for required in (
            "ReferenceSetRuntime",
            "self.reference_set_runtime",
            '"reference-sets"',
            "def show_reference_sets",
            "refresh_reference_sets=self.reference_set_runtime.reload",
        ):
            self.assertIn(required, app)
        self.assertIn('add_item(researchm, "Reference Sets", app.show_reference_sets)', ui)
        self.assertTrue(guide_has("Research", "Reference Sets", "menu"))

    def test_references_client_exposes_symmetric_related_editor(self):
        panel = (ROOT / "calamus/calamus_reference_panel.py").read_text(encoding="utf-8")
        runtime = (ROOT / "calamus/calamus_reference_runtime.py").read_text(encoding="utf-8")
        controller = (ROOT / "calamus/calamus_reference_controller.py").read_text(encoding="utf-8")
        self.assertIn('"Related References…"', panel)
        self.assertIn("run_related_references_dialog", runtime)
        self.assertIn("def on_related_references", runtime)
        self.assertIn("def replace_records", controller)

    def test_authoring_bridge_has_direct_related_reference_navigation(self):
        model = (ROOT / "calamus/calamus_authoring_bridge.py").read_text(encoding="utf-8")
        controller = (ROOT / "calamus/calamus_authoring_bridge_controller.py").read_text(encoding="utf-8")
        view = (ROOT / "calamus/calamus_authoring_bridge_view.py").read_text(encoding="utf-8")
        self.assertIn('kind="related-reference"', model)
        self.assertIn('navigation_kind="reference"', model)
        self.assertIn("reference_key=record.key", model)
        self.assertIn('if occurrence.navigation_kind == "reference"', controller)
        self.assertIn('mode_selector.append("related", "Related References")', view)

    def test_rename_and_research_check_include_reference_sets_and_related_keys(self):
        integrity = (ROOT / "calamus/calamus_reference_integrity.py").read_text(encoding="utf-8")
        controller = (ROOT / "calamus/calamus_research_integrity_controller.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "calamus/calamus_research_integrity_dialogs.py").read_text(encoding="utf-8")
        for required in (
            "reference_set_occurrences",
            "reference_sets_before",
            "reference_sets_after",
            "related_reference_issues",
            "reference_set_issues",
        ):
            self.assertIn(required, integrity)
        for required in (
            "ReferenceSetStore",
            "reference_set_snapshot",
            "_rollback_reference_sets",
            "refresh_reference_sets",
        ):
            self.assertIn(required, controller)
        self.assertIn("Reference Set memberships", dialogs)
        self.assertIn("Related Keys and Reference Set memberships", dialogs)

    def test_transparent_authorities_and_scope_are_documented(self):
        contract = (ROOT / "docs/canonical/CALAMUS_W89_RELATED_REFERENCES_REFERENCE_SETS_CONTRACT.md").read_text(encoding="utf-8")
        guide = load_user_guide(ROOT)
        for required in (
            "references.md",
            "reference-sets.md",
            "symmetric",
            "static",
            "No database",
            "No graph",
            "No watcher",
            "No dynamic",
        ):
            self.assertIn(required.casefold(), contract.casefold())
        for required in (
            "Related References",
            "Reference Sets",
            "# Calamus Reference Sets v1",
            "deleting a set never deletes any Reference",
        ):
            self.assertIn(required, guide)
        titles = tuple(section.title for section in parse_user_guide_sections(guide))
        self.assertIn("Related References", titles)
        self.assertIn("Reference Sets", titles)
        self.assertNotIn("Core sources", titles)

    def test_bloat_and_forbidden_infrastructure_gate(self):
        ceilings = {
            "bin/calamus": 3300,
            "calamus/calamus_related_references.py": 380,
            "calamus/calamus_related_reference_dialogs.py": 230,
            "calamus/calamus_reference_sets.py": 320,
            "calamus/calamus_reference_set_store.py": 130,
            "calamus/calamus_reference_set_controller.py": 300,
            "calamus/calamus_reference_set_view.py": 240,
            "calamus/calamus_reference_set_dialogs.py": 230,
            "calamus/calamus_reference_set_runtime.py": 170,
        }
        for relative, ceiling in ceilings.items():
            lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(lines), ceiling, relative)

        new_modules = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8").casefold()
            for relative in ceilings
            if relative.startswith("calamus/")
        )
        for forbidden in (
            "sqlite3",
            "watchdog",
            "subprocess",
            "lsp",
            "networkx",
            "json.dump",
            "background index",
        ):
            self.assertNotIn(forbidden, new_modules)

    def test_source_provenance_includes_every_new_runtime_module(self):
        proof = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
        for module in (
            "calamus_dialogs",
            "calamus_version",
            "calamus_modal_dialog",
            "calamus_related_references",
            "calamus_related_reference_dialogs",
            "calamus_reference_sets",
            "calamus_reference_set_store",
            "calamus_reference_set_controller",
            "calamus_reference_set_view",
            "calamus_reference_set_dialogs",
            "calamus_reference_set_runtime",
        ):
            self.assertIn(module, proof)


if __name__ == "__main__":
    unittest.main()
