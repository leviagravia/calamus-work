from pathlib import Path
import unittest

from calamus_help import load_user_guide, parse_user_guide_sections

ROOT = Path(__file__).resolve().parents[1]


class ClipHelpW95Tests(unittest.TestCase):
    def test_clip_help_documents_every_w95_feature(self):
        text = load_user_guide(ROOT)
        required = (
            "Calamus Clip Collection v2",
            "Stable ID, title and mnemonic shortcut",
            "A mnemonic shortcut is **not a tag**",
            "Create a new clip",
            "Capture selected document text",
            "Edit, duplicate and delete",
            "Insert a selected clip from the panel",
            "Insert Clip quickly with Ctrl+Alt+K",
            "**Insert Clip… — `Ctrl+Alt+K`**",
            "list of clip shortcuts",
            "Position the caret with {{cursor}}",
            "Copy Body without changing the document",
            "Numeric quick slots 1–9",
            "Refresh and external changes",
            "Open Clip File",
            "maximum of 200 records",
            "does not monitor or remember the system clipboard",
        )
        for item in required:
            self.assertIn(item, text)

    def test_clip_help_is_one_navigable_topic_before_scratchpad(self):
        sections = parse_user_guide_sections(load_user_guide(ROOT))
        titles = [section.title for section in sections]
        self.assertEqual(titles.count("Clip Collection"), 1)
        self.assertLess(titles.index("Clip Collection"), titles.index("Scratchpad"))
        body = next(section.body for section in sections if section.title == "Clip Collection")
        self.assertGreater(len(body), 8000)

    def test_help_keeps_scratchpad_full_frozen_by_current_roadmap(self):
        text = load_user_guide(ROOT)
        self.assertIn(
            "Scratchpad Full is frozen until Calamus is complete and the user gives a separate explicit authorization.",
            text,
        )
        self.assertNotIn("Scratchpad Full is frozen until after W96", text)

    def test_canonical_research_guide_has_updated_clip_summary(self):
        text = load_user_guide(ROOT)
        for item in (
            "shortcut mnemonica opzionale",
            "Research → Insert Clip…",
            "Ctrl+Alt+K",
            "numeric quick slots",
            "non è una cronologia degli appunti",
        ):
            self.assertIn(item, text)


if __name__ == "__main__":
    unittest.main()
