import os
from pathlib import Path
import tempfile
import unittest

from calamus_help import (
    load_user_guide,
    parse_user_guide_sections,
    parse_user_guide_topics,
    user_guide_candidates,
)


ROOT = Path(__file__).resolve().parents[1]


PUBLISHED_TAG_INTEGRITY_BODY = '`Research → Tag Integrity…` builds a transient inventory from References and the current document Source Notes. It does not scan or rewrite the document text.\n\nLogical identity uses Unicode NFC normalization, collapsed whitespace and case-insensitive comparison. Therefore `Faith`, `faith`, ` FAITH ` and Unicode-equivalent spellings are treated as variants of one logical tag.\n\nAvailable operations:\n\n- `Show Uses`: list the exact References and Source Notes that use the selected tag.\n- `Rename / Merge…`: rename all selected variants in the chosen scope; if the target already exists, duplicates are merged.\n- `Remove Everywhere…`: remove the selected logical tag in the chosen scope.\n- `Normalize All…`: rewrite variant spellings to the first canonical display spelling.\n\nScopes are `References and Source Notes`, `References only`, and `Current Source Notes only`.\n\nPractical example: the current Reference has tags `Faith`, `church history`, `temporary`; a Source Note has `FAITH`, `church history`, `temporary`. Select `Faith`, choose `Rename / Merge…`, enter `doctrine`, review the impact preview and confirm. Only the logical variants of `Faith` become `doctrine`; unrelated tags such as `church history` and `temporary` remain unchanged. The active document remains byte-identical.\n\nThe colour swatch is deterministic and derived from tag identity. It is presentation only: it is not stored in References or Source Notes and cannot create a colour-only tag.'


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
            "unrelated tags such as `church history` and `temporary` remain unchanged",
            "The active document remains byte-identical.",
        ):
            self.assertIn(required, text)

    def test_published_tag_integrity_contract_is_preserved_verbatim(self):
        sections = parse_user_guide_sections(load_user_guide(ROOT))
        section = next(item for item in sections if item.title == "Tag Integrity")
        self.assertTrue(
            section.body.startswith(PUBLISHED_TAG_INTEGRITY_BODY),
            "The published W92 Tag Integrity contract must remain verbatim at the start of the topic.",
        )
        self.assertIn("Relationship with the W94 Tags client", section.body)

    def test_research_learning_path_explains_authorities_and_recovery(self):
        text = load_user_guide(ROOT)
        for required in (
            "The six objects you must distinguish",
            "Start here: from a blank editor to a finished short academic article",
            "Source Note types: Quote, Paraphrase and Comment",
            "Understanding every Source Note field",
            "Worked scenario: building one section from several sources",
            "Common mistakes and how to recover",
            "Research habits that scale",
            "Research glossary",
            "A Reference is not a citation",
            "Backlinks are derived on demand",
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

    def test_canonical_research_panel_guide_includes_scratchpad_basic(self):
        text = load_user_guide(ROOT)
        for required in (
            "Guida canonica completa del pannello Research",
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
            "Scratchpad Basic",
            "article.md.scratchpad.md",
            "Capture Selection in Scratchpad",
            "Show Scratchpad for Current Section",
        ):
            self.assertIn(required, text)
        self.assertGreater(len(text), 105000)

    def test_canonical_research_guide_is_one_navigable_help_topic(self):
        sections = parse_user_guide_sections(load_user_guide(ROOT))
        titles = tuple(section.title for section in sections)
        self.assertEqual(
            titles.count("Guida canonica completa del pannello Research"),
            1,
        )
        section = next(
            item for item in sections
            if item.title == "Guida canonica completa del pannello Research"
        )
        self.assertIn("Schema mentale", section.body)
        self.assertIn("Research Check", section.body)
        self.assertIn("Regola conclusiva", section.body)
        self.assertGreater(len(section.body), 30000)

    def test_research_help_topics_follow_menu_learning_order(self):
        text = load_user_guide(ROOT)
        sections = parse_user_guide_sections(text)
        titles = tuple(section.title for section in sections)
        expected = (
            "Research Panel",
            "Clip Collection",
            "Scratchpad",
            "References",
            "Reference Sets",
            "Source Notes",
            "Authoring Bridge",
        )
        positions = tuple(titles.index(title) for title in expected)
        self.assertEqual(positions, tuple(sorted(positions)))
        self.assertNotIn("Scratchpad Basic", titles)
        self.assertNotIn("Tradition and memory {#tradition-and-memory}", titles)

    def test_scratchpad_learning_path_is_progressive_and_example_driven(self):
        text = load_user_guide(ROOT)
        for required in (
            "Start with the mental model, not with the buttons",
            "First guided exercise: ten minutes from an empty document",
            "capture → clarify → connect → retrieve → insert → resolve",
            "Understand the four types through examples",
            "Understand the four states as a simple lifecycle",
            "Three ways to create an entry",
            "Finding an entry without remembering where you put it",
            "Three realistic working scenarios",
            "Common mistakes and recovery",
            "A five-minute end-of-session review",
            "Quick reference after you have learned the workflow",
            "Open with lived memory",
            "Distinguish memory from nostalgia",
        ):
            self.assertIn(required, text)
        scratchpad = next(
            section for section in parse_user_guide_sections(text)
            if section.title == "Scratchpad"
        )
        self.assertGreater(len(scratchpad.body), 10000)


    def test_w94_tags_learning_path_is_complete_and_safe(self):
        text = load_user_guide(ROOT)
        for required in (
            "## Tags",
            "Tutorial: build a useful tag vocabulary from one article",
            "Start with the mental model",
            "Create one realistic research trail",
            "Open the complete A–Z inventory",
            "Three daily workflows",
            "A good stopping rule",
            "First guided exercise",
            "Reading the tag list",
            "Search, scope, sorting and Variants only",
            "Show Uses and Open",
            "All tags A–Z",
            "Name (A–Z)",
            "Most used",
            "**Mode: Rename**",
            "**Mode: Merge**",
            "**Mode: Normalize spelling**",
            "Rename or merge a tag",
            "Transaction safety",
            "Tags versus Tag Integrity",
            "What Tags deliberately does not do",
            "References, current Source Notes and current Scratchpad",
            "Add Tag to Selection",
        ):
            self.assertIn(required, text)
        tags = next(
            section for section in parse_user_guide_sections(text)
            if section.title == "Tags"
        )
        self.assertGreater(len(tags.body), 12000)

    def test_current_command_map_is_complete_and_follows_visible_menu_order(self):
        text = load_user_guide(ROOT)
        section = next(
            item for item in parse_user_guide_sections(text)
            if item.title == "Current command menu (W95extra mature-source rebuilt candidate)"
        )
        for menu in (
            "### File",
            "### Edit",
            "### Research",
            "### Navigate",
            "### Revise",
            "### View",
            "### Options",
            "### Tools",
            "### Help",
        ):
            self.assertIn(menu, section.body)
        positions = tuple(section.body.index(menu) for menu in (
            "### File",
            "### Edit",
            "### Research",
            "### Navigate",
            "### Revise",
            "### View",
            "### Options",
            "### Tools",
            "### Help",
        ))
        self.assertEqual(positions, tuple(sorted(positions)))
        for required in (
            "New from Template",
            "Writing Workspace",
            "Recent Workspaces",
            "Favorites",
            "Find All…",
            "Capture Selection in Scratchpad…",
            "Tags",
            "Export with Pandoc/citeproc…",
            "Navigator Panel",
            "Manage Bookmarks…",
            "Opacity Selection…",
            "System Info…",
            "Keyboard Shortcuts",
        ):
            self.assertIn(required, section.body)

    def test_final_command_target_preserves_entry_061_and_later_research_decisions(self):
        text = load_user_guide(ROOT)
        section = next(
            item for item in parse_user_guide_sections(text)
            if item.title == "Final command menu target"
        )
        for menu in (
            "### Final File",
            "### Final Edit",
            "### Final Research",
            "### Final Navigate",
            "### Final Writing",
            "### Final Revise",
            "### Final View",
            "### Final Tools",
            "### Final Help",
        ):
            self.assertIn(menu, section.body)
        for required in (
            "Tags",
            "Add Tag to Selection",
            "Go to Next Tag",
            "Go to Previous Tag",
            "Add Reference Note",
            "Insert Reference Marker",
            "Clear Unused References",
            "Insert Source Note Marker",
            "Clear Scratchpad",
            "Show Uses",
            "Rename Tag…",
            "Merge Tags…",
            "Scratchpad Full is frozen until Calamus is complete",
            "Options` menu disappears",
            "About Calamus",
            "Guide Navigator",
            "A work item cannot be published",
        ):
            self.assertIn(required, section.body)

    def test_hierarchical_help_topics_expose_menu_and_submenu_structure(self):
        topics = parse_user_guide_topics(load_user_guide(ROOT))
        titles = tuple(topic.title for topic in topics)
        self.assertIn("Current command menu (W95extra mature-source rebuilt candidate)", titles)
        self.assertIn("File", titles)
        self.assertIn("Final Research", titles)
        self.assertIn("Current boundaries", titles)
        current_index = titles.index("Current command menu (W95extra mature-source rebuilt candidate)")
        file_index = titles.index("File")
        self.assertEqual(topics[file_index].parent_index, current_index)
        final_index = titles.index("Final command menu target")
        final_research_index = titles.index("Final Research")
        self.assertEqual(topics[final_research_index].parent_index, final_index)
        for bogus in (
            "Tradition and Renewal in Parish Life",
            "Introduction {#introduction}",
            "Core sources",
        ):
            self.assertNotIn(bogus, titles)

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
