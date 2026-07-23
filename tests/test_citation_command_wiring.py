import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"
PANEL = ROOT / "calamus" / "calamus_reference_panel.py"
RUNTIME = ROOT / "calamus" / "calamus_reference_runtime.py"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(name):
    text = source(LAUNCHER)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(name)


class CitationCommandWiringTests(unittest.TestCase):
    def test_modules_exist_and_are_provenance_tracked(self):
        modules = (
            "calamus_citations",
            "calamus_citation_controller",
            "calamus_citation_dialogs",
        )
        provenance = source(PROVENANCE)
        for module in modules:
            self.assertTrue((ROOT / "calamus" / f"{module}.py").exists())
            self.assertIn(f'"{module}"', provenance)

    def test_research_menu_and_shortcuts_expose_bidirectional_commands(self):
        ui = source(UI)
        shortcuts = source(SHORTCUTS)
        self.assertIn("Quick Cite…", ui)
        self.assertIn("Ctrl+Alt+Q", ui)
        self.assertIn("Open Citation in References", ui)
        self.assertIn("Ctrl+Alt+Shift+Q", ui)
        self.assertIn('("<Control><Alt>Q", app.on_quick_cite)', ui)
        self.assertIn('("<Control><Alt><Shift>Q", app.on_open_citation_in_references)', ui)
        self.assertIn('ShortcutSpec("Research", "Quick Cite", "Ctrl+Alt+Q")', shortcuts)
        self.assertIn(
            'ShortcutSpec("Research", "Open Citation in References", "Ctrl+Alt+Shift+Q")',
            shortcuts,
        )

    def test_app_composes_controller_and_keeps_insertion_in_mutation_gateway(self):
        build = method_source("build_research_panel")
        insert = method_source("insert_citation_text")
        quick = method_source("run_quick_cite")
        open_citation = method_source("on_open_citation_in_references")
        launcher = source(LAUNCHER)

        self.assertIn("CitationController(", build)
        self.assertIn("reference_records_provider=lambda: self.reference_panel_runtime.records", build)
        self.assertIn("show_reference=self.show_reference_key", build)
        self.assertIn('self.execute_command("Quick Cite", edit)', insert)
        self.assertIn("command_insert_at", insert)
        self.assertIn("run_quick_cite_dialog", quick)
        self.assertIn("citation_controller.quick_cite", quick)
        self.assertIn("citation_controller.open_citation", open_citation)
        dialogs = source(ROOT / "calamus" / "calamus_citation_dialogs.py")
        self.assertGreaterEqual(dialogs.count("set_activates_default(True)"), 2)
        self.assertIn("set_default_response(Gtk.ResponseType.OK)", dialogs)
        self.assertNotIn("format_pandoc_citation(", launcher)
        self.assertNotIn("parse_citation_clusters(", launcher)

    def test_reference_panel_quick_cite_uses_same_command(self):
        panel = source(PANEL)
        runtime = source(RUNTIME)
        build = method_source("build_research_panel")
        self.assertIn('("Quick Cite", on_quick_cite)', panel)
        self.assertIn("self._quick_cite(selected.key)", runtime)
        self.assertIn("quick_cite=self.quick_cite_key", build)
        self.assertIn("return self.run_quick_cite(initial_key=key)", method_source("quick_cite_key"))

    def test_open_citation_reuses_existing_reference_selection_gateway(self):
        build = method_source("build_research_panel")
        show = method_source("show_reference_key")
        self.assertIn("show_reference=self.show_reference_key", build)
        self.assertIn('self.research_panel_runtime.show("references")', show)
        self.assertIn("self.reference_panel_runtime.show_key(key)", show)

    def test_w77_does_not_add_citeproc_database_or_pdf_ownership(self):
        combined = "\n".join(
            source(path)
            for path in (
                LAUNCHER,
                UI,
                ROOT / "calamus" / "calamus_citations.py",
                ROOT / "calamus" / "calamus_citation_controller.py",
                ROOT / "calamus" / "calamus_citation_dialogs.py",
            )
        )
        for forbidden in (
            "citeproc",
            "CSL engine",
            "sqlite",
            "PDF manager",
            "DOI lookup",
            "Bibliography Check",
            "Concept Map",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
