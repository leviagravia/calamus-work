import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class W97BibliographyWiringTests(unittest.TestCase):
    def source(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_single_canonical_authority_and_existing_controller_are_reused(self):
        runtime = self.source("calamus/calamus_reference_runtime.py")
        launcher = self.source("bin/calamus")
        self.assertIn("MarkdownReferenceStore", runtime)
        self.assertIn("ReferenceController", runtime)
        self.assertNotIn("sqlite", runtime.casefold())
        self.assertNotIn("json.dump", runtime)
        self.assertEqual(launcher.count("self.reference_store = MarkdownReferenceStore()"), 1)

    def test_research_panel_renames_existing_client_without_second_manager(self):
        launcher = self.source("bin/calamus")
        ui = self.source("calamus/calamus_ui.py")
        self.assertIn('(\"references\", \"Bibliography\"', launcher)
        self.assertIn('add_item(researchm, "Bibliography", app.show_references)', ui)
        self.assertIn('add_item(researchm, "Open Bibliography File", app.on_open_bibliography_file)', ui)
        self.assertEqual(launcher.count('("references", "Bibliography"'), 1)
        self.assertNotIn('("bibliography",', launcher)

    def test_panel_has_core_list_detail_filters_and_actions(self):
        panel = self.source("calamus/calamus_reference_panel.py")
        for text in (
            "Search all bibliography fields",
            "All types", "All tags", "All uses", "All files", "All integrity",
            "Gtk.Paned", "Duplicate", "Show Uses", "Open File", "Reveal", "Refresh",
        ):
            self.assertIn(text, panel)

    def test_runtime_owns_duplicate_safe_delete_file_actions_and_context(self):
        runtime = self.source("calamus/calamus_reference_runtime.py")
        for symbol in (
            "duplicate_reference", "build_delete_impact", "build_bibliography_context",
            "on_duplicate", "on_show_uses", "on_open_file", "on_reveal_file",
            "open_bibliography_file",
        ):
            self.assertIn(symbol, runtime)
        self.assertIn("source_notes_provider", runtime)
        self.assertIn("reference_sets_provider", runtime)
        self.assertIn("document_text_provider", runtime)

    def test_app_remains_composition_only(self):
        text = self.source("bin/calamus")
        tree = ast.parse(text)
        methods = {
            node.name: ast.get_source_segment(text, node) or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        }
        self.assertLessEqual(len(methods["show_references"].splitlines()), 3)
        self.assertLessEqual(len(methods["on_open_bibliography_file"].splitlines()), 6)
        for forbidden in ("BibliographyFilters(", "project_references(", "build_delete_impact("):
            self.assertNotIn(forbidden, text)

    def test_current_development_identity_is_w97_core_on_published_w96_baseline(self):
        version = self.source("calamus/calamus_version.py")
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W97"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Bibliography Manager Core"', version)
        self.assertIn('PUBLISHED_BASELINE = "199459fb023e4862407f7eb60318192f276d3239"', version)


if __name__ == "__main__":
    unittest.main()
