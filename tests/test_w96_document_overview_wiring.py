from pathlib import Path
import inspect
import re
import unittest

import calamus_document_dossier_app
import calamus_document_overview_model
import calamus_document_overview_runtime
import calamus_document_overview_view

ROOT = Path(__file__).resolve().parents[1]


class W96DocumentOverviewWiringTests(unittest.TestCase):
    def test_navigate_menu_exposes_exact_single_entry_without_shortcut(self):
        source = (ROOT / "calamus/calamus_ui.py").read_text(encoding="utf-8")
        self.assertEqual(1, source.count('add_item(navigatem, "Document Overview", app.on_document_overview)'))
        self.assertNotIn("Document Overview\\t", source)

    def test_app_composes_existing_authorities_and_single_runtime(self):
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        boundary = inspect.getsource(calamus_document_dossier_app)
        for token in (
            "import calamus_document_dossier_app as document_dossier_app",
            "document_dossier_app.build_document_overview(self)",
            "on_document_overview = document_dossier_app.on_document_overview",
            "refresh_document_overview_if_open = document_dossier_app.refresh_document_overview_if_open",
            "document_overview_runtime.shutdown()",
            "document_overview_runtime.mark_stale()",
            'getattr(self, "refresh_document_overview_if_open", lambda: False)()',
        ):
            self.assertIn(token, launcher)
        for token in (
            "DocumentDossierController(",
            "build_document_dossier_inputs(",
            "DocumentOverviewRuntime(",
            "reference_store=app.reference_store",
            "reference_set_store=app.reference_set_store",
            "show_notice=lambda message: app.info(message)",
        ):
            self.assertIn(token, boundary)
        self.assertIn("from calamus_document_overview_view import build_document_overview_view", boundary)
        self.assertNotIn("calamus_document_overview_view", launcher)
        self.assertNotIn("DocumentOverviewStore", launcher + boundary)

    def test_view_is_gtk_only_and_domain_modules_remain_gtk_free(self):
        view = inspect.getsource(calamus_document_overview_view)
        self.assertIn('gi.require_version("Gtk", "3.0")', view)
        domain = inspect.getsource(calamus_document_dossier_app)
        runtime = inspect.getsource(calamus_document_overview_runtime)
        for token in ("import gi", "from gi", "Gtk.", "Gdk.", "Gio."):
            self.assertNotIn(token, domain)
            self.assertNotIn(token, runtime)

    def test_view_has_five_categories_progressive_disclosure_and_no_tabs(self):
        source = inspect.getsource(calamus_document_overview_view)
        model = inspect.getsource(calamus_document_overview_model)
        for token in ("Overview", "Structure", "Research", "Integrity", "Statistics"):
            self.assertIn(token, model)
        self.assertIn("Gtk.Paned", source)
        self.assertIn("Gtk.ListBox", source)
        self.assertNotIn("Gtk.Notebook", source)
        self.assertNotIn("Gtk.StackSwitcher", source)
        self.assertNotIn("Gtk.TextView", source)

    def test_w96_help_is_preserved_and_current_identity_is_w97(self):
        version = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W97"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Bibliography Manager Core"', version)
        self.assertIn('PUBLISHED_BASELINE = "199459fb023e4862407f7eb60318192f276d3239"', version)
        guide = (ROOT / "share/doc/calamus/USER_GUIDE.md").read_text(encoding="utf-8")
        for token in (
            "## Document Overview",
            "Navigate → Document Overview",
            "Overview, Structure, Research, Integrity and Statistics",
            "Related References",
            "pertinent Reference Sets",
            "Refresh",
            "read-only projection",
            "select the",
            "item again",
            "no action is executed from a stale",
        ):
            self.assertIn(token, guide)

    def test_source_provenance_lists_gate_b_modules(self):
        text = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
        for module in (
            "calamus_document_dossier_app",
            "calamus_document_overview_model",
            "calamus_document_overview_view",
            "calamus_document_overview_runtime",
        ):
            self.assertIn(f'"{module}"', text)

    def test_no_forbidden_infrastructure_is_introduced(self):
        source = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "calamus/calamus_document_dossier_app.py",
                "calamus/calamus_document_overview_view.py",
                "calamus/calamus_document_overview_runtime.py",
            )
        ).casefold()
        for token in ("sqlite", "watchdog", "elasticsearch", "faiss", "react", "vue", "bert", "openai"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
