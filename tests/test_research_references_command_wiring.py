import ast
import unittest
from tests.w104_command_test_support import guide_has
from pathlib import Path

from tests.w105_menu_test_support import legacy_menu_projection
from tests.w107_source_test_support import authoritative_method_source, app_method_source, research_composition_source, workspace_host_source

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(name):
    return authoritative_method_source(name)


class ResearchReferencesCommandWiringTests(unittest.TestCase):
    def test_modules_exist_and_are_provenance_tracked(self):
        modules = (
            "calamus_panel_chrome",
            "calamus_references",
            "calamus_reference_store",
            "calamus_reference_controller",
            "calamus_reference_panel",
            "calamus_reference_dialogs",
            "calamus_reference_runtime",
            "calamus_research_panel",
            "calamus_research_panel_view",
        )
        provenance = source(PROVENANCE)
        for module in modules:
            self.assertTrue((ROOT / "calamus" / f"{module}.py").exists())
            self.assertIn(f'"{module}"', provenance)

    def test_research_is_top_level_between_edit_and_navigate(self):
        ui = legacy_menu_projection()
        self.assertLess(ui.index('top_menu(app, "Edit")'), ui.index('top_menu(app, "Research")'))
        self.assertLess(ui.index('top_menu(app, "Research")'), ui.index('top_menu(app, "Navigate")'))
        self.assertIn('Gtk.CheckMenuItem(label="Research Panel\\tCtrl+Alt+C")', ui)
        self.assertIn('add_item(researchm, "Clip Collection", app.show_clip_collection)', ui)
        self.assertIn('add_item(researchm, "Bibliography", app.show_references)', ui)
        self.assertIn('add_item(researchm, "Source Notes", app.show_source_notes)', ui)
        view_block = ui[ui.index('viewm = top_menu(app, "View")'):ui.index('optm = top_menu(app, "Options")')]
        self.assertNotIn("Clip Collection", view_block)

    def test_shortcut_now_targets_research_panel_without_duplication(self):
        ui = legacy_menu_projection()
        self.assertIn("command_shortcut_bindings()", ui)
        self.assertTrue(guide_has("Research", "Research Panel", "Ctrl+Alt+C"))
        self.assertFalse(guide_has("View", "Clip Collection", "Ctrl+Alt+C"))

    def test_app_composes_authorities_but_does_not_own_reference_crud(self):
        launcher = source(LAUNCHER)
        clip_composition = source(ROOT / "calamus/calamus_clip_composition.py")
        research = research_composition_source()
        self.assertEqual(clip_composition.count("RightPanelHost("), 1)
        self.assertNotIn("RightPanelHost(", launcher)
        self.assertIn('inputs.right_panel_host.register("research", panel_view.widget)', research)
        self.assertIn("ReferencePanelRuntime(", research)
        for forbidden in ("ReferenceRecord(", "serialize_references_markdown", "os.replace(tmp", "resolve_external_reference_change"):
            self.assertNotIn(forbidden, launcher)
        for method in ("toggle_research_panel", "show_clip_collection", "show_references"):
            self.assertLessEqual(len(app_method_source(method).splitlines()), 2)

    def test_shell_owns_title_selector_and_close_gateway(self):
        view = source(ROOT / "calamus" / "calamus_research_panel_view.py")
        runtime = source(ROOT / "calamus" / "calamus_research_panel.py")
        self.assertIn('title.set_markup("<b>Research</b>")', view)
        self.assertIn("ResearchClientSelector", view)
        self.assertIn("Gtk.MenuButton", view)
        self.assertIn("Gtk.Popover", view)
        self.assertIn("Gtk.PositionType.BOTTOM", view)
        self.assertNotIn("Gtk.StackSwitcher", view)
        self.assertIn('name="research-close-button"', view)
        self.assertIn('self._host.show("research")', runtime)
        self.assertIn("self._host.hide()", runtime)
        self.assertNotIn(".remove(", view)

    def test_real_clients_include_scratchpad_and_w94_tags_without_concepts_placeholder(self):
        composition = research_composition_source()
        for client in ('"clip-collection"', '"references"', '"source-notes"', '"scratchpad"', '"tags"'):
            self.assertIn(client, composition)
        self.assertNotIn('"concepts"', composition)

    def test_reference_panel_keeps_crud_and_quick_cite_without_import_export_ownership(self):
        runtime = source(ROOT / "calamus" / "calamus_reference_runtime.py")
        panel = source(ROOT / "calamus" / "calamus_reference_panel.py")
        combined = runtime + "\n" + panel
        self.assertIn("Quick Cite", combined)
        for forbidden in ("BibLaTeX", "parse_bibliography", "export_references", "citeproc", "DOI lookup", "PDF manager"):
            self.assertNotIn(forbidden, combined)
        composition = research_composition_source()
        self.assertIn("BibtexRuntime", composition)
        self.assertIn("reference_store = MarkdownReferenceStore()", composition)


if __name__ == "__main__":
    unittest.main()
