"""Pure decision-state tests for W87 mature-source UI repair."""
import unittest

from calamus_bibtex import (
    ACTION_IMPORT,
    ACTION_MERGE,
    ACTION_NEW_KEY,
    ACTION_SKIP,
    BIBLATEX,
    build_import_preview,
    parse_bibliography,
)
from calamus_bibtex_import_session import BibImportSession
from calamus_references import ReferenceRecord


class BibImportSessionTests(unittest.TestCase):
    def setUp(self):
        library = parse_bibliography(
            """
@book{existing, title={Incoming title}, publisher={Press}}
@online{fresh, title={Fresh title}}
@book{invalid, title={One}, title={Two}}
""",
            BIBLATEX,
        )
        current = (
            ReferenceRecord(
                key="existing",
                title="Existing local title",
                type="book",
            ),
        )
        self.preview = build_import_preview(library, current)
        self.session = BibImportSession(self.preview)

    def test_ambiguous_collision_is_unresolved_but_new_and_invalid_are_safe(self):
        self.assertEqual(self.session.unresolved_indices, (0,))
        self.assertFalse(self.session.can_review)
        self.assertIsNone(self.session.action(0))
        self.assertEqual(self.session.action(1), ACTION_IMPORT)
        self.assertEqual(self.session.action(2), ACTION_SKIP)

    def test_explicit_collision_action_unlocks_review(self):
        row = self.session.set_action(0, ACTION_MERGE)
        self.assertEqual(row.action, ACTION_MERGE)
        self.assertTrue(self.session.can_review)
        self.assertEqual(
            tuple((item.index, item.action) for item in self.session.decisions()),
            ((0, ACTION_MERGE), (1, ACTION_IMPORT), (2, ACTION_SKIP)),
        )

    def test_disallowed_action_fails_closed(self):
        with self.assertRaises(ValueError):
            self.session.set_action(2, ACTION_NEW_KEY)
        self.assertEqual(self.session.action(2), ACTION_SKIP)

    def test_unknown_index_fails_closed(self):
        with self.assertRaises(ValueError):
            self.session.set_action(999, ACTION_SKIP)

    def test_preview_exposes_matched_local_record_for_collision_summary(self):
        item = self.preview.items[0]
        self.assertIsNotNone(item.existing_record)
        self.assertEqual(item.existing_record.title, "Existing local title")
        self.assertEqual(self.preview.items[1].existing_record, None)

    def test_decisions_refuse_unresolved_collisions(self):
        with self.assertRaisesRegex(ValueError, "existing"):
            self.session.decisions()


if __name__ == "__main__":
    unittest.main()
