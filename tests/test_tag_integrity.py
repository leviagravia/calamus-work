import unicodedata
import unittest

from calamus_document_structure import build_document_structure
from calamus_reference_integrity import run_research_check
from calamus_references import ReferenceRecord
from calamus_source_notes import SourceNote
from calamus_tag_integrity import (
    TAG_ACTION_NORMALIZE_ALL,
    TAG_ACTION_REMOVE,
    TAG_ACTION_RENAME_MERGE,
    TAG_SCOPE_REFERENCES,
    TAG_SCOPE_SOURCE_NOTES,
    build_tag_inventory,
    clean_tag_display,
    plan_tag_mutation,
    tag_color,
    tag_identity,
)


class TagIntegrityPureTests(unittest.TestCase):
    def setUp(self):
        nfd = unicodedata.normalize("NFD", "café")
        self.references = (
            ReferenceRecord(
                key="r1",
                title="One",
                tags=("Faith", "café", "social  doctrine"),
            ),
            ReferenceRecord(
                key="r2",
                title="Two",
                tags=("faith", nfd, "Social doctrine"),
            ),
        )
        self.notes = (
            SourceNote(
                id="sn-1",
                kind="comment",
                text="Note",
                tags=(" FAITH ", "social doctrine"),
                modified="before",
            ),
        )

    def test_identity_is_nfc_whitespace_collapsed_and_casefolded(self):
        self.assertEqual(clean_tag_display("  Social\t doctrine  "), "Social doctrine")
        self.assertEqual(tag_identity("CAFÉ"), tag_identity(unicodedata.normalize("NFD", "café")))
        self.assertEqual(tag_identity("Faith"), "faith")

    def test_inventory_groups_variants_and_tracks_exact_uses(self):
        inventory = build_tag_inventory(self.references, self.notes)
        faith = inventory.get("faith")
        self.assertIsNotNone(faith)
        self.assertEqual(faith.canonical, "Faith")
        self.assertEqual(faith.reference_count, 2)
        self.assertEqual(faith.source_note_count, 1)
        self.assertIn("Faith", faith.variants)
        self.assertIn("faith", faith.variants)
        self.assertIn("FAITH", faith.variants)
        self.assertTrue(faith.needs_normalization)

    def test_swatch_is_stable_and_identity_derived(self):
        self.assertEqual(tag_color("Faith"), tag_color(" faith "))
        self.assertEqual(tag_color("café"), tag_color(unicodedata.normalize("NFD", "CAFÉ")))
        self.assertRegex(tag_color("Faith"), r"^#[0-9A-F]{6}$")

    def test_rename_to_existing_identity_merges_and_deduplicates(self):
        plan = plan_tag_mutation(
            self.references,
            self.notes,
            action=TAG_ACTION_RENAME_MERGE,
            source_tag="Faith",
            target_tag="social doctrine",
            modified_stamp="2026-07-25T12:00:00+02:00",
        )
        self.assertTrue(plan.changed)
        self.assertEqual(plan.references_after[0].tags, ("social doctrine", "café"))
        self.assertEqual(plan.references_after[1].tags, ("social doctrine", unicodedata.normalize("NFD", "café")))
        self.assertEqual(plan.source_notes_after[0].tags, ("social doctrine",))
        self.assertEqual(plan.source_notes_after[0].modified, "2026-07-25T12:00:00+02:00")
        self.assertGreaterEqual(plan.impact.occurrences_changed, 3)

    def test_remove_can_be_confined_to_references(self):
        plan = plan_tag_mutation(
            self.references,
            self.notes,
            action=TAG_ACTION_REMOVE,
            scope=TAG_SCOPE_REFERENCES,
            source_tag="Faith",
        )
        self.assertNotIn("Faith", plan.references_after[0].tags)
        self.assertNotIn("faith", plan.references_after[1].tags)
        self.assertEqual(plan.source_notes_after, self.notes)
        self.assertEqual(plan.impact.source_notes_changed, 0)

    def test_remove_can_be_confined_to_source_notes(self):
        plan = plan_tag_mutation(
            self.references,
            self.notes,
            action=TAG_ACTION_REMOVE,
            scope=TAG_SCOPE_SOURCE_NOTES,
            source_tag="faith",
            modified_stamp="stamp",
        )
        self.assertEqual(plan.references_after, self.references)
        self.assertEqual(plan.source_notes_after[0].tags, ("social doctrine",))
        self.assertEqual(plan.source_notes_after[0].modified, "stamp")

    def test_normalize_all_uses_first_authority_display_deterministically(self):
        plan = plan_tag_mutation(
            self.references,
            self.notes,
            action=TAG_ACTION_NORMALIZE_ALL,
            modified_stamp="stamp",
        )
        self.assertEqual(plan.references_after[0].tags, ("Faith", "café", "social doctrine"))
        self.assertEqual(plan.references_after[1].tags, ("Faith", "café", "social doctrine"))
        self.assertEqual(plan.source_notes_after[0].tags, ("Faith", "social doctrine"))
        self.assertTrue(plan.impact.reference_records_changed)
        self.assertEqual(plan.source_notes_after[0].modified, "stamp")

    def test_noop_and_invalid_requests_fail_closed(self):
        clean_refs = (ReferenceRecord(key="r", title="R", tags=("stable",)),)
        with self.assertRaisesRegex(ValueError, "no tag normalization"):
            plan_tag_mutation(clean_refs, (), action=TAG_ACTION_NORMALIZE_ALL)
        with self.assertRaisesRegex(ValueError, "not available"):
            plan_tag_mutation(clean_refs, (), action=TAG_ACTION_REMOVE, source_tag="missing")
        with self.assertRaisesRegex(ValueError, "target tag"):
            plan_tag_mutation(clean_refs, (), action=TAG_ACTION_RENAME_MERGE, source_tag="stable")

    def test_research_check_reports_logical_tag_collision(self):
        report = run_research_check(
            self.references,
            "",
            self.notes,
            build_document_structure(""),
        )
        issues = [issue for issue in report.issues if issue.kind == "tag-identity-collision"]
        self.assertTrue(issues)
        self.assertTrue(any(issue.subject == "Faith" for issue in issues))


if __name__ == "__main__":
    unittest.main()
