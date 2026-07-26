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
