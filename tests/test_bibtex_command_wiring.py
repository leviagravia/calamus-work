import ast
from pathlib import Path
import unittest
from tests.w104_command_test_support import guide_has

from tests.w105_menu_test_support import legacy_menu_projection
from tests.w107_source_test_support import authoritative_method_source, app_method_source, research_composition_source, workspace_host_source

ROOT = Path(__file__).resolve().parents[1]


class BibtexCommandWiringTests(unittest.TestCase):
    def source(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def method(self, name):
        return authoritative_method_source(name)


    def test_research_menu_exposes_exact_import_and_export_commands(self):
        ui = legacy_menu_projection()
        self.assertEqual(ui.count('"Import BibTeX/BibLaTeX…"'), 1)
        self.assertEqual(ui.count('"Export References as BibTeX/BibLaTeX…"'), 1)
        self.assertIn("app.on_import_bibtex_biblatex", ui)
        self.assertIn("app.on_export_references_bibtex_biblatex", ui)

    def test_w108_binds_bibtex_commands_directly_to_research_runtime(self):
        importer = self.method("on_import_bibtex_biblatex")
        exporter = self.method("on_export_references_bibtex_biblatex")
        launcher = self.source("bin/calamus")
        self.assertIn("self.components.bibtex_runtime.import_references()", importer)
        self.assertIn("self.components.bibtex_runtime.export_references()", exporter)
        self.assertIn("on_import_bibtex_biblatex=research_runtime.on_import_bibtex_biblatex", launcher)
        self.assertIn("on_export_references_bibtex_biblatex=research_runtime.on_export_references_bibtex_biblatex", launcher)
        self.assertNotIn("def on_import_bibtex_biblatex", launcher)
        self.assertNotIn("def on_export_references_bibtex_biblatex", launcher)
        for method in (importer, exporter):
            for forbidden in ("open(", "Gtk.", "atomic_write", "references.md"):
                self.assertNotIn(forbidden, method)

    def test_app_composes_controller_from_existing_reference_authority(self):
        composition = research_composition_source()
        build = app_method_source("build_research_panel")
        self.assertIn("BibtexController(reference_store", composition)
        self.assertIn("refresh_references=reference_panel_runtime.reload", composition)
        self.assertIn("BibtexRuntime(inputs.dialog_parent, bibtex_controller)", composition)
        self.assertIn("build_research_subsystem(", build)
        self.assertNotIn("BibtexController(", build)

    def test_pure_module_has_no_gtk_or_file_io(self):
        source = self.source("calamus/calamus_bibtex.py")
        for forbidden in ("gi.repository", "Gtk", "open(", "os.replace", "atomic_write_utf8"):
            self.assertNotIn(forbidden, source)

    def test_controller_owns_io_and_never_force_overwrites(self):
        source = self.source("calamus/calamus_bibtex_controller.py")
        self.assertIn("FileToken", source)
        self.assertIn("atomic_write_utf8", source)
        self.assertIn("file_token(source_path) != plan.source_token", source)
        self.assertNotIn("force=True", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("pandoc", source.casefold())
        self.assertNotIn("biber", source.casefold())

    def test_import_view_uses_session_static_actions_and_direct_row_projection(self):
        view = self.source("calamus/calamus_bibtex_import_view.py")
        session = self.source("calamus/calamus_bibtex_import_session.py")
        self.assertIn("class BibImportSession", session)
        self.assertNotIn("gi.repository", session)
        self.assertIn('"Choose one action"', view)
        self.assertIn("Gtk.RadioButton", view)
        self.assertIn("row_number_by_index", view)
        self.assertIn("store[row_number][5]", view)
        self.assertIn("session.unresolved_count", view)
        self.assertIn("Current local reference", view)
        self.assertIn("Incoming reference", view)
        self.assertNotIn("Gtk.ComboBoxText", view)
        self.assertNotIn("iter_next", view)
        self.assertNotIn("remove_all", view)

    def test_dialogs_keep_local_file_boundaries_and_reexport_import_view(self):
        source = self.source("calamus/calamus_bibtex_dialogs.py")
        self.assertIn("build_bib_import_preview_dialog", source)
        self.assertIn("run_bib_import_preview_dialog", source)
        self.assertIn("Gtk.FileChooserAction.OPEN", source)
        self.assertIn("Gtk.FileChooserAction.SAVE", source)
        self.assertIn("set_do_overwrite_confirmation(True)", source)
        self.assertIn("set_local_only(True)", source)
        self.assertNotIn("set_extra_widget", source)

    def test_provenance_and_shortcut_registry_include_w87_modules(self):
        provenance = self.source("scripts/prove-source-provenance.sh")
        for module in (
            "calamus_bibtex", "calamus_bibtex_import_session",
            "calamus_bibtex_import_view", "calamus_bibtex_controller",
            "calamus_bibtex_dialogs", "calamus_bibtex_runtime",
        ):
            self.assertIn(f'"{module}"', provenance)
        self.assertTrue(guide_has("Research", "Import BibTeX/BibLaTeX", "menu"))
        self.assertTrue(guide_has("Research", "Export References as BibTeX/BibLaTeX", "menu"))

    def test_user_guide_contains_complete_import_and_export_examples(self):
        guide = self.source("share/doc/calamus/USER_GUIDE.md")
        for required in (
            "## Import BibTeX/BibLaTeX",
            "theology-library.bib",
            "Merge missing fields",
            "Current local reference",
            "Incoming reference",
            "STOP without applying",
            "If the `.bib` source or `references.md` changes after preview",
            "## Export References as BibTeX/BibLaTeX",
            "calamus-references.bib",
            "does not claim byte-for-byte round trip",
        ):
            self.assertIn(required, guide)


if __name__ == "__main__":
    unittest.main()
