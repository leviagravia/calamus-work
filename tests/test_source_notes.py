import unittest
from datetime import datetime, timezone

from calamus_source_notes import (
    SourceLocator,
    SourceNote,
    new_source_note_id,
    normalize_heading_target,
    source_note_kinds,
)


class SourceNoteModelTests(unittest.TestCase):
    def test_locator_display_and_search(self):
        locator = SourceLocator(
            page="42",
            page_end="45",
            chapter="3",
            section="Communion",
            paragraph="7",
        )
        self.assertEqual(locator.display, "p. 42–45, ch. 3, sec. Communion, para. 7")
        self.assertIn("communion", locator.search_text)

    def test_quote_requires_reference_and_text(self):
        with self.assertRaises(ValueError):
            SourceNote(id="sn-1", kind="quote", text="Text")
        with self.assertRaises(ValueError):
            SourceNote(id="sn-1", kind="comment", text="")
        comment = SourceNote(id="sn-1", kind="comment", text="My idea")
        self.assertEqual(comment.reference_key, "")

    def test_note_normalizes_and_searches_all_semantics(self):
        note = SourceNote(
            id=" sn-1 ",
            kind="Quote",
            reference_key=" ratzinger1968introduction ",
            locator=SourceLocator(page=" 42 "),
            text="  Faith is response.  ",
            comment="Important for chapter one",
            tags=("faith", "faith", "revelation"),
        )
        self.assertEqual(note.id, "sn-1")
        self.assertEqual(note.kind, "quote")
        self.assertEqual(note.tags, ("faith", "revelation"))
        self.assertEqual(note.excerpt, "Faith is response.")
        self.assertIn("ratzinger1968introduction", note.search_text)
        self.assertIn("chapter one", note.search_text)
        self.assertEqual(source_note_kinds(), ("quote", "paraphrase", "comment"))


    def test_heading_target_is_canonical_optional_and_searchable(self):
        note = SourceNote(
            id="sn-target",
            kind="comment",
            text="Use this in the method section.",
            target="method",
        )
        self.assertEqual(note.target, "#method")
        self.assertIn("#method", note.search_text)
        self.assertEqual(normalize_heading_target(" #Ética-1 "), "#Ética-1")
        self.assertEqual(normalize_heading_target(""), "")

    def test_malformed_heading_target_is_rejected(self):
        for target in ("#", "#1-number", "#bad/path", "#bad target"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    SourceNote(
                        id="sn-target",
                        kind="comment",
                        text="Text",
                        target=target,
                    )

    def test_new_id_is_readable_and_disambiguated(self):
        now = datetime(2026, 7, 21, 15, 30, 0, tzinfo=timezone.utc)
        first = new_source_note_id((), now=now, token="abc123")
        self.assertEqual(first, "sn-20260721-153000-abc123")
        second = new_source_note_id((first,), now=now, token="abc123")
        self.assertEqual(second, first + "-2")


if __name__ == "__main__":
    unittest.main()
