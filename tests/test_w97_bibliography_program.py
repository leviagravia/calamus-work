"""Frozen W97 Core/Full architecture and source-boundary contracts."""
from __future__ import annotations

from pathlib import Path
import unittest

from tests.w105_menu_test_support import legacy_menu_projection
ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "docs/canonical/CALAMUS_W97_BIBLIOGRAPHY_MANAGER_CORE_CONTRACT.md"
PROGRAM = ROOT / "docs/canonical/CALAMUS_W97_BIBLIOGRAPHY_MANAGER_CORE_FULL_PROGRAM.md"
AUDIT = ROOT / "docs/canonical/CALAMUS_W97_BIBLIOGRAPHY_MANAGER_MATURE_SOURCE_AUDIT.md"
FAIL_AUDIT = ROOT / "docs/canonical/CALAMUS_W97_BIBLIOGRAPHY_MANAGER_R1_FAIL_LIFECYCLE_AUDIT.md"
EXACT_AUDIT = ROOT / "docs/canonical/CALAMUS_W97_R1_R2_EXACT_PRODUCT_LOG_AND_SEARCH_SIGNAL_AUDIT.md"
REBUILD_AUDIT = ROOT / "docs/canonical/CALAMUS_W97_BIBLIOGRAPHY_SEARCH_MODEL_REBUILD_AUDIT.md"


class W97BibliographyProgramTests(unittest.TestCase):
    def test_core_contract_freezes_single_authority_and_existing_client(self):
        text = CORE.read_text(encoding="utf-8")
        for token in (
            "`references.md` remains the sole canonical bibliography authority",
            "Existing internal Research client ID: `references`",
            "one local-file path",
            "Safe Delete",
            "current visible projection",
            "historical functional gates remain independent",
        ):
            self.assertIn(token, text)

    def test_core_excludes_full_and_forbidden_infrastructure(self):
        text = CORE.read_text(encoding="utf-8")
        for token in (
            "web metadata retrieval",
            "AI",
            "cloud/sync",
            "PDF indexing",
            "automatic duplicate merge",
            "field-by-field merge",
        ):
            self.assertIn(token, text)

    def test_full_is_deferred_and_w98_core_is_allowed(self):
        text = PROGRAM.read_text(encoding="utf-8")
        self.assertIn("Bibliography Manager Full is frozen", text)
        self.assertIn("No Full variant blocks W98", text)
        self.assertIn("Scratchpad Full/W93", text)
        self.assertIn("must not implement any Bibliography Manager Full feature", text)

    def test_mature_audit_has_all_seven_sources_and_decision_matrix(self):
        text = AUDIT.read_text(encoding="utf-8")
        for token in (
            "GNOME Citations", "JabRef", "KBibTeX", "Zotero", "Pandoc",
            "Referencer", "coBib", "ADOPT", "ADAPT", "REJECT", "DEFER",
        ):
            self.assertIn(token, text)


    def test_rebuild_contract_owns_explicit_coalescing_selection_and_wait_oracle(self):
        text = CORE.read_text(encoding="utf-8")
        for token in (
            "SEARCH/MODEL REBUILD CANDIDATE R1",
            "150 ms quiet-period timer",
            "Only the latest query is delivered",
            "bounded wait",
            "selected citation key belongs to `ReferenceController`",
            "not Candidate R3",
        ):
            self.assertIn(token, text)

    def test_exact_failure_correction_is_canonical(self):
        fail = FAIL_AUDIT.read_text(encoding="utf-8")
        exact = EXACT_AUDIT.read_text(encoding="utf-8")
        mature = AUDIT.read_text(encoding="utf-8")
        for token in (
            "CALAMUS-W97-SEARCH-CHANGED-DELAYED-TEST-ORACLE-01",
            "INVALID RUN / FALSE-NEGATIVE TRUE-APP ORACLE",
            "CALAMUS-RUN-PROFILE-ERR-TRAP-INTERCEPTION-01",
            "not Candidate R3",
        ):
            self.assertIn(token, fail)
        self.assertIn("search-changed", exact)
        self.assertIn("Exact-log correction", mature)
        self.assertIn("150 ms GTK3 timer", mature)
        rebuild = REBUILD_AUDIT.read_text(encoding="utf-8")
        self.assertIn("explicit delayed/coalesced search", rebuild)
        self.assertIn("exit-7 self-test", rebuild)

    def test_search_model_source_barriers_are_executable(self):
        panel = (ROOT / "calamus/calamus_reference_panel.py").read_text(encoding="utf-8")
        controller = (ROOT / "calamus/calamus_reference_controller.py").read_text(encoding="utf-8")
        true_app = (ROOT / "tests/test_w97_bibliography_app_desktop_e2e.py").read_text(encoding="utf-8")
        for token in (
            "CoalescedQueryDispatcher",
            'self.search.connect("changed", changed)',
            "search_delivery_count",
            "last_delivered_query",
        ):
            self.assertIn(token, panel)
        for token in (
            "self._selected_key: str | None = None",
            "def sync_selection_from_view",
        ):
            self.assertIn(token, controller)
        for token in (
            "def _until",
            "search-requested",
            "search-delivered",
            "view.last_delivered_query",
        ):
            self.assertIn(token, true_app)
        self.assertNotIn('_marker("search-applied")', true_app)

    def test_domain_projection_is_gtk_free_and_provenance_tracked(self):
        source = (ROOT / "calamus/calamus_bibliography.py").read_text(encoding="utf-8")
        self.assertNotIn("gi.repository", source)
        self.assertNotIn("import gi", source)
        provenance = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
        self.assertIn("calamus_bibliography", provenance)
        self.assertIn("calamus_bibliography_search", provenance)

    def test_simple_export_is_runtime_owned_and_app_is_thin(self):
        runtime = (ROOT / "calamus/calamus_reference_runtime.py").read_text(encoding="utf-8")
        app = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        research_runtime = (ROOT / "calamus/calamus_research_application.py").read_text(encoding="utf-8")
        ui = legacy_menu_projection()
        self.assertIn("def export_visible_bibliography", runtime)
        self.assertIn("atomic_write_utf8", runtime)
        self.assertIn("Export Bibliography as Markdown", ui)
        self.assertIn("Export Bibliography as Text", ui)
        self.assertIn("return self.components.reference_panel_runtime.export_visible_bibliography", research_runtime)
        self.assertIn("self._research_components.runtime.on_export_bibliography_", app)


if __name__ == "__main__":
    unittest.main()
