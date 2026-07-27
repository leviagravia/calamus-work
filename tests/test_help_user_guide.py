import os
from pathlib import Path
import tempfile
import unittest

from calamus_help import load_user_guide, parse_user_guide_sections, user_guide_candidates


ROOT = Path(__file__).resolve().parents[1]


class UserGuidePureTests(unittest.TestCase):
    def test_canonical_guide_contains_research_workflow_and_practical_examples(self):
        text = load_user_guide(ROOT)
        for required in (
            "A practical Research workflow",
            "Research → References",
            "Research → Source Notes",
            "Research → Quick Cite…",
            "Research → Research Check…",
            "Research → Tag Integrity…",
            "Research → Export Research Apparatus…",
            "Chapter-01.md.source-notes.md",
            "Only the logical variants of `Faith` become `doctrine`",
        ):
            self.assertIn(required, text)

    def test_research_learning_path_explains_authorities_and_recovery(self):
        text = load_user_guide(ROOT)
        for required in (
            "The five objects you must distinguish",
            "Start here: from a blank editor to a finished short academic article",
            "Source Note types: Quote, Paraphrase and Comment",
            "Understanding every Source Note field",
            "Worked scenario: building one section from several sources",
            "Common mistakes and how to recover",
            "Research habits that scale",
            "Research glossary",
            "A Reference is not a citation",
            "Backlinks are never stored",
            "Undo does not change Source Notes",
        ):
            self.assertIn(required, text)
        self.assertGreater(len(text), 50000)


    def test_blank_editor_tutorial_is_complete_and_actionable(self):
        text = load_user_guide(ROOT)
        for required in (
            "Stage 1 — Save the empty document before doing research work",
            "**one H1** for the title of the whole article",
            "**H2** for Introduction, the three main sections and Conclusion",
            "**H3** for the subsections inside each main section",
            "# Tradition and Renewal in Parish Life",
            "## 1. Historical background {#historical-background}",
            "## 2. Theological principles {#theological-principles}",
            "## 3. Pastoral discernment {#pastoral-discernment}",
            "Stage 4 — Register each source once in References",
            "Stage 5 — Build a small research notebook before drafting",
            "Stage 7 — Insert a simple citation with a page locator",
            "[@ratzinger1968, p. 42]",
            "[@newman1870, pp. 55-57; @ratzinger1968, p. 42]",
            "Stage 10 — Link one part of the article to another",
            "Stage 15 — Perform the final academic check",
            "Four common starting situations",
        ):
            self.assertIn(required, text)
        self.assertGreaterEqual(text.count("### Stage "), 15)

    def test_tutorial_code_headings_do_not_pollute_help_navigator(self):
        sections = parse_user_guide_sections(load_user_guide(ROOT))
        titles = tuple(section.title for section in sections)
        self.assertIn(
            "Start here: from a blank editor to a finished short academic article",
            titles,
        )
        for bogus in (
            "Introduction {#introduction}",
            "1. Historical background {#historical-background}",
            "2. Theological principles {#theological-principles}",
            "3. Pastoral discernment {#pastoral-discernment}",
            "Conclusion {#conclusion}",
        ):
            self.assertNotIn(bogus, titles)

    def test_related_references_and_reference_sets_are_taught_with_examples(self):
        text = load_user_guide(ROOT)
        for required in (
            "Related References",
            "Reference Sets",
            "Related Keys: newman1870, delubac1949",
            "A relation is **symmetric**",
            "Research → Authoring Bridge",
            "reference-sets.md",
            "# Calamus Reference Sets v1",
            "## Core sources",
            "Use a Related Reference when two works have an explicit relationship",
            "deleting a set never deletes any Reference",
            "Rename Reference Key",
            "asymmetric Related References",
            "invalid set members",
            "Worked example: relate, collect and rename one source safely",
            "one active-document citation, one current Source Note, one Related-key occurrence and one Reference Set membership",
            "newman1870-revised",
        ):
            self.assertIn(required, text)

        titles = tuple(section.title for section in parse_user_guide_sections(text))
        self.assertIn("Related References", titles)
        self.assertIn("Reference Sets", titles)
        self.assertNotIn("Core sources", titles)
        self.assertNotIn("Historical background", titles)

    def test_beginner_references_tutorial_is_detailed_and_case_explicit(self):
        text = load_user_guide(ROOT)
        for required in (
            "References tutorial: from an empty library to a checked article",
            "Stage R1 — Understand the three things that look similar",
            "Stage R2 — Open References and add a book",
            "Stage R6 — Insert citations with Quick Cite",
            "Stage R7 — Create an explicit Related Reference",
            "Stage R8 — Create a Reference Set for one task",
            "Reference Set names are **case-sensitive and preserved exactly**",
            "Stage R9 — Rename a key across four authorities",
            "Stage R12 — Complete worked example",
            "Common Reference mistakes and recovery",
            "references.md = canonical library",
            "[@ratzinger1968, p. 42; @newman1870, pp. 55-57]",
        ):
            self.assertIn(required, text)
        self.assertGreaterEqual(text.count("### Stage R"), 12)
        self.assertGreater(len(text), 65000)

    def test_w90_pandoc_export_tutorial_is_complete_and_option_exhaustive(self):
        text = load_user_guide(ROOT)
        for required in (
            "Tutorial completo: esportare con Pandoc passo per passo",
            "Passo P1 — Controlla il documento che hai davvero aperto",
            "Passo P2 — Verifica che Pandoc sia disponibile",
            "Passo P4 — Scegli Product",
            "Formatted Bibliography",
            "Current Document with Citations",
            "References cited in the current document",
            "All References",
            "One Reference Set",
            "Plain text (.txt)",
            "HTML (.html)",
            "OpenDocument Text (.odt)",
            "Microsoft Word (.docx)",
            "Rich Text Format (.rtf)",
            "LaTeX source (.tex)",
            "EPUB (.epub)",
            "Use Pandoc Default",
            "Local CSL file",
            "Passo P9 — Leggi la semantic preview",
            "Passo P10 — Conferma, annulla e riapri",
            "Esempio A — Bibliografia TXT di un Reference Set",
            "Esempio B — Bibliografia HTML con stile locale",
            "Esempio C — Documento ODT con le sole fonti citate",
            "Esempio D — Documento DOCX richiesto da una rivista",
            "Esempio E — EPUB con tutte le References",
            "Esempio F — Sorgente LaTeX per un progetto esterno",
            "Passo P12 — Controllo dopo l'export",
            "Se il file non si trova, non dichiarare l'export riuscito",
        ):
            self.assertIn(required, text)
        self.assertGreaterEqual(text.count("#### Passo P"), 12)
        self.assertGreater(len(text), 120000)

    def test_canonical_research_panel_guide_is_complete_and_excludes_scratchpad(self):
        text = load_user_guide(ROOT)
        for required in (
            "Guida canonica completa del pannello Research (Scratchpad escluso)",
            "Prima idea fondamentale: Research non è un unico archivio",
            "Percorso rapido: dal documento vuoto al controllo finale",
            "Clip Collection: frammenti riutilizzabili, non fonti",
            "References: la biblioteca globale",
            "Related References: relazioni esplicite tra due opere",
            "Reference Sets: liste statiche per un compito",
            "Source Notes: il quaderno di ricerca del documento",
            "Create Source Note from Selection",
            "Insert Link to Heading",
            "Quick Cite: inserire citazioni senza ricordare le key",
            "Open Citation in References",
            "Rename Reference Key: una migrazione controllata",
            "Authoring Bridge: leggere le relazioni derivate",
            "Research Check: controllo complessivo",
            "Tag Integrity: rinominare e unificare tag senza sostituzioni cieche",
            "Import BibTeX/BibLaTeX",
            "Export References as BibTeX/BibLaTeX",
            "Export Research Apparatus",
            "Esempio completo: costruire un articolo teologico",
            "Checklist finale prima di consegnare un lavoro",
            "La guida dello **Scratchpad** sarà aggiunta in seguito",
        ):
            self.assertIn(required, text)
        self.assertGreater(len(text), 105000)

    def test_canonical_research_guide_is_one_navigable_help_topic(self):
        sections = parse_user_guide_sections(load_user_guide(ROOT))
        titles = tuple(section.title for section in sections)
        self.assertEqual(
            titles.count("Guida canonica completa del pannello Research (Scratchpad escluso)"),
            1,
        )
        section = next(
            item for item in sections
            if item.title == "Guida canonica completa del pannello Research (Scratchpad escluso)"
        )
        self.assertIn("Schema mentale", section.body)
        self.assertIn("Research Check", section.body)
        self.assertIn("Regola conclusiva", section.body)
        self.assertGreater(len(section.body), 30000)

    def test_parser_is_deterministic_and_exposes_topics(self):
        sections = parse_user_guide_sections(load_user_guide(ROOT))
        self.assertGreaterEqual(len(sections), 10)
        titles = tuple(section.title for section in sections)
        self.assertEqual(titles[0], "Overview")
        self.assertIn("Tag Integrity", titles)
        self.assertIn("Export Research Apparatus", titles)

    def test_loader_prefers_explicit_source_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            guide = Path(tmp) / "share/doc/calamus/USER_GUIDE.md"
            guide.parent.mkdir(parents=True)
            guide.write_text("# Guide\n\n## Local\n\nExact text.\n", encoding="utf-8")
            self.assertEqual(load_user_guide(tmp), guide.read_text(encoding="utf-8"))
            self.assertEqual(user_guide_candidates(tmp)[0], guide)


if __name__ == "__main__":
    unittest.main()
