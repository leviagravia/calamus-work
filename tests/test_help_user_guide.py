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
