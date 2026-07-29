import unittest

from calamus_references import ReferenceRecord
from calamus_scratchpad import ScratchpadEntry
from calamus_source_notes import SourceNote
from calamus_tag_integrity import (
    TAG_ACTION_REMOVE,
    TAG_ACTION_RENAME_MERGE,
    TAG_RENAME_MODE_MERGE,
    TAG_RENAME_MODE_NORMALIZE,
    TAG_RENAME_MODE_RENAME,
    TAG_SCOPE_ALL,
    TAG_SCOPE_SCRATCHPAD,
    build_tag_inventory,
    plan_tag_mutation,
)


class W94TagsPureTests(unittest.TestCase):
    def setUp(self):
        self.references = (
            ReferenceRecord(key="r1", title="Reference", tags=("Faith", "method")),
        )
        self.notes = (
            SourceNote(id="sn-1", kind="comment", text="Source note", tags=("faith",)),
        )
        self.scratchpad = (
            ScratchpadEntry(
                id="sp-1",
                type="idea",
                title="Scratch idea",
                body="Body",
                tags=(" FAITH ", "drafting"),
                updated="before",
            ),
        )

    def test_all_scope_projects_three_markdown_authorities(self):
        inventory = build_tag_inventory(
            self.references,
            self.notes,
            self.scratchpad,
            scope=TAG_SCOPE_ALL,
        )
        faith = inventory.get("faith")
        self.assertEqual(faith.reference_count, 1)
        self.assertEqual(faith.source_note_count, 1)
        self.assertEqual(faith.scratchpad_count, 1)
        self.assertEqual(faith.total_count, 3)
        self.assertTrue(faith.needs_normalization)
        self.assertEqual(
            tuple(use.authority for use in faith.uses),
            ("references", "source-notes", "scratchpad"),
        )

    def test_scratchpad_scope_is_exact_and_does_not_mutate_other_authorities(self):
        plan = plan_tag_mutation(
            self.references,
            self.notes,
            self.scratchpad,
            action=TAG_ACTION_REMOVE,
            scope=TAG_SCOPE_SCRATCHPAD,
            source_tag="faith",
            modified_stamp="stamp",
        )
        self.assertEqual(plan.references_after, self.references)
        self.assertEqual(plan.source_notes_after, self.notes)
        self.assertEqual(plan.scratchpad_after[0].tags, ("drafting",))
        self.assertEqual(plan.scratchpad_after[0].updated, "stamp")
        self.assertEqual(plan.impact.scratchpad_entries_changed, 1)

    def test_all_scope_rename_merge_is_deterministic_across_three_authorities(self):
        plan = plan_tag_mutation(
            self.references,
            self.notes,
            self.scratchpad,
            action=TAG_ACTION_RENAME_MERGE,
            scope=TAG_SCOPE_ALL,
            source_tag="faith",
            target_tag="method",
            modified_stamp="stamp",
        )
        self.assertEqual(plan.references_after[0].tags, ("method",))
        self.assertEqual(plan.source_notes_after[0].tags, ("method",))
        self.assertEqual(plan.scratchpad_after[0].tags, ("method", "drafting"))
        self.assertEqual(plan.source_notes_after[0].modified, "stamp")
        self.assertEqual(plan.scratchpad_after[0].updated, "stamp")
        self.assertEqual(plan.impact.reference_records_changed, 1)
        self.assertEqual(plan.impact.source_notes_changed, 1)
        self.assertEqual(plan.impact.scratchpad_entries_changed, 1)
        self.assertEqual(plan.impact.rename_mode, TAG_RENAME_MODE_MERGE)

    def test_rename_mode_distinguishes_new_target_existing_target_and_spelling(self):
        renamed = plan_tag_mutation(
            self.references, self.notes, self.scratchpad,
            action=TAG_ACTION_RENAME_MERGE, scope=TAG_SCOPE_ALL,
            source_tag="faith", target_tag="doctrine", modified_stamp="stamp",
        )
        normalized = plan_tag_mutation(
            self.references, self.notes, self.scratchpad,
            action=TAG_ACTION_RENAME_MERGE, scope=TAG_SCOPE_ALL,
            source_tag="faith", target_tag="FAITH", modified_stamp="stamp",
        )
        self.assertEqual(renamed.impact.rename_mode, TAG_RENAME_MODE_RENAME)
        self.assertEqual(normalized.impact.rename_mode, TAG_RENAME_MODE_NORMALIZE)


if __name__ == "__main__":
    unittest.main()
