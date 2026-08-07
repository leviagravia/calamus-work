import ast
import os
import unittest
from tests.w104_command_test_support import guide_has
from pathlib import Path

from tests.w105_menu_test_support import legacy_menu_projection
ROOT = Path(__file__).resolve().parents[1]


class ResearchExportCommandWiringTests(unittest.TestCase):
    def source(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def method(self, name):
        tree = ast.parse(self.source("bin/calamus"))
        node = next(
            item for item in ast.walk(tree)
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name
        )
        return ast.get_source_segment(self.source("bin/calamus"), node)

    def test_research_menu_exposes_one_named_export_command(self):
        ui = legacy_menu_projection()
        self.assertEqual(ui.count('"Export Research Apparatus…"'), 1)
        self.assertIn('app.on_export_research_apparatus', ui)
        self.assertNotIn("Export BibTeX", ui)
        self.assertNotIn("Export Bibliography of All References", ui)

    def test_app_entrypoint_is_thin_and_uses_runtime(self):
        method = self.method("on_export_research_apparatus")
        self.assertIn("self.research_export_runtime.export()", method)
        for forbidden in ("open(", "atomic_write", "Gtk.", "references.md", "source-notes"):
            self.assertNotIn(forbidden, method)

    def test_app_builds_controller_from_existing_research_authorities(self):
        build = self.method("build_research_panel")
        self.assertIn("ResearchExportController(", build)
        self.assertIn("reference_store=self.reference_store", build)
        self.assertIn("document_text_provider=self.buffer_text", build)
        self.assertIn("document_structure_provider=lambda: self.navigation_controller.structure", build)
        self.assertIn("ResearchExportRuntime(", build)

    def test_pure_export_module_has_no_gtk_or_file_mutation(self):
        source = self.source("calamus/calamus_research_export.py")
        for forbidden in ("gi.repository", "Gtk", "open(", "os.replace", "atomic_write_utf8"):
            self.assertNotIn(forbidden, source)

    def test_controller_uses_shared_atomic_writer_and_never_writes_authorities(self):
        source = self.source("calamus/calamus_research_export_controller.py")
        self.assertIn("from calamus_research_file import atomic_write_utf8", source)
        self.assertNotIn("reference_store.save", source)
        self.assertNotIn("source_note_store.save", source)
        self.assertNotIn("MarkdownSourceNoteStore.save", source)

    def test_dialog_uses_explicit_product_step_then_standard_local_save(self):
        source = self.source("calamus/calamus_research_export_dialogs.py")
        self.assertIn("def build_research_export_product_dialog", source)
        self.assertIn('label="Export product:"', source)
        self.assertIn('"Choose Destination…"', source)
        self.assertIn("dialog.show_all()", source)
        self.assertIn("def build_research_export_destination_dialog", source)
        self.assertIn("Gtk.FileChooserAction.SAVE", source)
        self.assertIn("dialog.set_do_overwrite_confirmation(True)", source)
        self.assertIn('markdown_filter.add_pattern("*.md")', source)
        self.assertIn("dialog.set_local_only(True)", source)
        self.assertNotIn("set_extra_widget", source)
        self.assertNotIn("get_extra_widget", source)

    def test_product_and_destination_are_sequential_not_hidden_in_file_chooser(self):
        source = self.source("calamus/calamus_research_export_dialogs.py")
        method_tree = ast.parse(source)
        run_node = next(
            item for item in ast.walk(method_tree)
            if isinstance(item, ast.FunctionDef) and item.name == "run_research_export_dialog"
        )
        method = ast.get_source_segment(source, run_node)
        self.assertIn("run_research_export_product_dialog(parent)", method)
        self.assertIn("run_research_export_destination_dialog(parent, document_path, kind)", method)
        self.assertLess(
            method.index("run_research_export_product_dialog"),
            method.index("run_research_export_destination_dialog"),
        )

    def test_shortcut_registry_marks_command_as_menu_only(self):
        self.assertTrue(guide_has("Research", "Export Research Apparatus", "menu"))


if __name__ == "__main__":
    unittest.main()
