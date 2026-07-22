import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(name):
    text = source(LAUNCHER)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(name)


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
        ui = source(UI)
        self.assertLess(ui.index('top_menu(app, "Edit")'), ui.index('top_menu(app, "Research")'))
        self.assertLess(ui.index('top_menu(app, "Research")'), ui.index('top_menu(app, "Navigate")'))
        self.assertIn('Gtk.CheckMenuItem(label="Research Panel\\tCtrl+Alt+C")', ui)
        self.assertIn('add_item(researchm, "Clip Collection", app.show_clip_collection)', ui)
        self.assertIn('add_item(researchm, "References", app.show_references)', ui)
        self.assertIn('add_item(researchm, "Source Notes", app.show_source_notes)', ui)
        view_block = ui[ui.index('viewm = top_menu(app, "View")'):ui.index('optm = top_menu(app, "Options")')]
        self.assertNotIn("Clip Collection", view_block)

    def test_shortcut_now_targets_research_panel_without_duplication(self):
        ui = source(UI)
        shortcuts = source(SHORTCUTS)
        self.assertIn('("<Control><Alt>C", app.toggle_research_panel)', ui)
        self.assertIn('ShortcutSpec("Research", "Research Panel", "Ctrl+Alt+C")', shortcuts)
        self.assertNotIn('ShortcutSpec("View", "Clip Collection", "Ctrl+Alt+C")', shortcuts)

    def test_app_composes_authorities_but_does_not_own_reference_crud(self):
        launcher = source(LAUNCHER)
        self.assertEqual(launcher.count("RightPanelHost("), 1)
        self.assertIn('self.right_panel_host.register("research", self.research_panel_view.widget)', launcher)
        self.assertIn("ReferencePanelRuntime(self)", launcher)
        for forbidden in ("ReferenceRecord(", "serialize_references_markdown", "os.replace(tmp", "resolve_external_reference_change"):
            self.assertNotIn(forbidden, launcher)
        for method in ("toggle_research_panel", "show_clip_collection", "show_references"):
            self.assertLessEqual(len(method_source(method).splitlines()), 3)

    def test_shell_owns_title_selector_and_close_gateway(self):
        view = source(ROOT / "calamus" / "calamus_research_panel_view.py")
        runtime = source(ROOT / "calamus" / "calamus_research_panel.py")
        self.assertIn('title.set_markup("<b>Research</b>")', view)
        self.assertIn("Gtk.ComboBoxText", view)
        self.assertNotIn("Gtk.StackSwitcher", view)
        self.assertIn('name="research-close-button"', view)
        self.assertIn('self._host.show("research")', runtime)
        self.assertIn("self._host.hide()", runtime)
        self.assertNotIn(".remove(", view)

    def test_three_real_clients_are_registered_without_future_placeholders(self):
        block = method_source("build_research_panel")
        self.assertIn('"clip-collection"', block)
        self.assertIn('"references"', block)
        self.assertIn('"source-notes"', block)
        for future in ("scratchpad", "concepts", '"tags"'):
            self.assertNotIn(future, block)

    def test_w72_does_not_add_future_citation_or_pdf_features(self):
        combined = "\n".join(source(path) for path in (LAUNCHER, UI, ROOT / "calamus" / "calamus_reference_runtime.py"))
        for forbidden in (
            "Quick Cite",
            "Insert Citation",
            "Bibliography Check",
            "BibLaTeX",
            "citeproc",
            "DOI lookup",
            "PDF manager",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
