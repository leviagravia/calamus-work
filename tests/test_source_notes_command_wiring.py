import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
PROVENANCE = ROOT / "scripts" / "prove-source-provenance.sh"
RESEARCH_VIEW = ROOT / "calamus" / "calamus_research_panel_view.py"
STORE = ROOT / "calamus" / "calamus_source_note_store.py"
CONTROLLER = ROOT / "calamus" / "calamus_source_note_controller.py"
RUNTIME = ROOT / "calamus" / "calamus_source_note_runtime.py"
PANEL = ROOT / "calamus" / "calamus_source_note_panel.py"
DIALOGS = ROOT / "calamus" / "calamus_source_note_dialogs.py"
STRUCTURE = ROOT / "calamus" / "calamus_document_structure.py"
NAVIGATION = ROOT / "calamus" / "calamus_navigation_gateway.py"


def source(path):
    return path.read_text(encoding="utf-8")


def method_source(name):
    text = source(LAUNCHER)
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(name)


class SourceNotesCommandWiringTests(unittest.TestCase):
    def test_modules_exist_and_are_provenance_tracked(self):
        modules = (
            "calamus_research_file",
            "calamus_source_notes",
            "calamus_source_note_store",
            "calamus_source_note_controller",
            "calamus_source_note_panel",
            "calamus_source_note_dialogs",
            "calamus_source_note_runtime",
        )
        provenance = source(PROVENANCE)
        for module in modules:
            self.assertTrue((ROOT / "calamus" / f"{module}.py").exists())
            self.assertIn(f'"{module}"', provenance)

    def test_research_menu_and_shell_expose_third_real_client(self):
        ui = source(UI)
        launcher = source(LAUNCHER)
        research_view = source(RESEARCH_VIEW)
        self.assertIn('add_item(researchm, "Source Notes", app.show_source_notes)', ui)
        self.assertIn('"source-notes"', method_source("build_research_panel"))
        self.assertIn('"Source Notes"', method_source("build_research_panel"))
        self.assertIn("SourceNotePanelRuntime(", launcher)
        self.assertIn("Gtk.ComboBoxText", research_view)
        self.assertNotIn("Gtk.StackSwitcher", research_view)

    def test_sidecar_is_document_specific_markdown(self):
        store = source(STORE)
        self.assertIn('return os.path.abspath(os.path.expanduser(document_path.strip())) + ".source-notes.md"', store)
        self.assertIn('"# Calamus Source Notes v1"', store)
        self.assertIn('encoding="utf-8"', store)
        self.assertNotIn("source-notes.json", store)
        self.assertNotIn("sqlite", store.lower())

    def test_controller_owns_persist_first_crud_and_missing_link_diagnostics(self):
        controller = source(CONTROLLER)
        self.assertLess(
            controller.index("result = self._store.save(candidate, self._token)"),
            controller.index("self._notes = candidate"),
        )
        self.assertIn("missing reference link", controller)
        self.assertIn("Reference key is missing", controller)
        self.assertIn("reference_keys_provider", controller)
        self.assertIn("document_structure_provider", controller)
        self.assertIn("missing target", controller)
        self.assertIn("ambiguous target", controller)
        self.assertNotIn("Gtk", controller)

    def test_source_note_targets_reuse_canonical_heading_structure_and_navigation(self):
        launcher = source(LAUNCHER)
        runtime = source(RUNTIME)
        panel = source(PANEL)
        dialogs = source(DIALOGS)
        structure = source(STRUCTURE)
        navigation = source(NAVIGATION)
        store = source(STORE)

        self.assertIn('("Target", "target")', store)
        self.assertIn('document_structure_provider=lambda: self.navigation_controller.structure', launcher)
        self.assertIn('show_target=self.show_heading_target', launcher)
        self.assertIn('navigate_identifier(target)', method_source("show_heading_target"))
        self.assertIn('def headings_for_identifier', structure)
        self.assertIn('def unique_heading_for_identifier', structure)
        self.assertIn('def navigate_identifier', navigation)
        self.assertIn('Open Target', panel)
        self.assertIn('Document Target', dialogs)
        self.assertIn('self.on_open_target', runtime)
        self.assertNotIn('build_document_structure(', runtime)
        self.assertNotIn('build_document_structure(', panel)
        self.assertNotIn('build_document_structure(', dialogs)

    def test_dialog_keeps_generated_source_note_id_stable(self):
        dialogs = source(ROOT / "calamus" / "calamus_source_note_dialogs.py")
        self.assertIn("new_source_note_id(existing_ids)", dialogs)
        self.assertIn("id_entry.set_editable(False)", dialogs)

    def test_unsaved_document_is_fail_closed_and_identity_changes_sync(self):
        controller = source(CONTROLLER)
        runtime = source(RUNTIME)
        self.assertIn("Save the document to use Source Notes.", controller)
        self.assertIn("Save the document before creating Source Notes.", runtime)
        for method in (
            "execute_new_plan",
            "execute_open_plan",
            "execute_save_plan",
            "execute_new_from_template_plan",
        ):
            self.assertIn("sync_source_notes_document", method_source(method))

    def test_app_only_composes_and_exposes_thin_wrappers(self):
        launcher = source(LAUNCHER)
        for forbidden in (
            "SourceNote(",
            "serialize_source_notes_markdown",
            "atomic_write_utf8",
            "MarkdownSourceNoteStore(",
        ):
            self.assertNotIn(forbidden, launcher)
        self.assertLessEqual(len(method_source("show_source_notes").splitlines()), 2)
        self.assertLessEqual(len(method_source("sync_source_notes_document").splitlines()), 3)
        self.assertLessEqual(len(method_source("show_reference_key").splitlines()), 3)
        self.assertLessEqual(len(method_source("show_heading_target").splitlines()), 2)

    def test_w77_keeps_source_notes_free_of_pdf_concept_and_check_features(self):
        combined = "\n".join(
            source(path)
            for path in (
                RUNTIME,
                ROOT / "calamus" / "calamus_source_note_panel.py",
                ROOT / "calamus" / "calamus_source_note_controller.py",
            )
        )
        for forbidden in (
            "Bibliography Check",
            "PDF annotation",
            "Concept Map",
            "Scratchpad",
            "citeproc",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
