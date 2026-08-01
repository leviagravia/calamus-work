from pathlib import Path
import inspect
import unittest

import calamus_document_dossier
import calamus_document_dossier_controller


ROOT = Path(__file__).resolve().parents[1]


class W96DocumentOverviewProgramTests(unittest.TestCase):
    def test_core_and_full_program_is_frozen_in_canonical_docs(self):
        text = (ROOT / "docs/canonical/CALAMUS_W96_DOCUMENT_OVERVIEW_CORE_FULL_PROGRAM.md").read_text(encoding="utf-8")
        for token in (
            "Document Overview Core",
            "Document Overview Full",
            "Related References",
            "Pertinent Reference Sets",
            "collected-unused",
            "fresh direct reading",
            "Xed, Gedit and GNOME Text Editor",
        ):
            self.assertIn(token, text)

    def test_roadmap_is_exact(self):
        text = (ROOT / "docs/canonical/CALAMUS_W96_DOCUMENT_OVERVIEW_CORE_FULL_PROGRAM.md").read_text(encoding="utf-8")
        ordered = (
            "W96 — Document Overview Core",
            "W97 — Bibliography Manager",
            "W98 — Research Panel Integral Closure",
            "W99 — retrospective GTK-free and lifecycle audit",
            "Scratchpad Full (historical W93, still FROZEN)",
            "Document Overview Full (unassigned W100+ until authorized)",
        )
        positions = [text.index(value) for value in ordered]
        self.assertEqual(positions, sorted(positions))

    def test_core_contract_excludes_storage_and_mutation(self):
        text = (ROOT / "docs/canonical/CALAMUS_W96_DOCUMENT_OVERVIEW_CORE_CONTRACT.md").read_text(encoding="utf-8")
        for token in (
            "no persistent dossier authority",
            "read/navigation actions only",
            "no database, graph, AI/NLP or semantic indexing",
        ):
            self.assertIn(token, text)

    def test_gate_a_modules_are_gtk_free(self):
        source = inspect.getsource(calamus_document_dossier) + inspect.getsource(calamus_document_dossier_controller)
        for token in ("import gi", "from gi", "Gtk.", "Gdk.", "Gio."):
            self.assertNotIn(token, source)

    def test_source_provenance_lists_gate_a_modules(self):
        text = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
        self.assertIn('"calamus_document_dossier"', text)
        self.assertIn('"calamus_document_dossier_controller"', text)


if __name__ == "__main__":
    unittest.main()
