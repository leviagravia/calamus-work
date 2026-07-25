import unittest

from calamus_reference_store import ReferenceLibrarySnapshot, ReferenceSaveResult
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken
from calamus_source_note_store import SourceNoteSaveResult, SourceNoteSnapshot
from calamus_source_notes import SourceNote
from calamus_tag_integrity import (
    TAG_ACTION_NORMALIZE_ALL,
    TAG_ACTION_REMOVE,
    TAG_ACTION_RENAME_MERGE,
    TAG_SCOPE_REFERENCES,
)
from calamus_tag_integrity_controller import TagIntegrityController


class FakeReferenceStore:
    def __init__(self, records):
        self.records = tuple(records)
        self.token = FileToken(True, 1, 10, "refs-1")
        self.saves = []
        self.fail_next = None
        self.diagnostics = ()

    def load(self):
        return ReferenceLibrarySnapshot(self.records, self.token, self.diagnostics)

    def save(self, records, expected_token, *, force=False):
        self.saves.append((tuple(records), expected_token, force))
        if expected_token != self.token and not force:
            return ReferenceSaveResult("conflict", self.token, "References changed externally.")
        if self.fail_next:
            status, message, callback = self.fail_next
            self.fail_next = None
            if callback:
                callback()
            return ReferenceSaveResult(status, self.token, message)
        self.records = tuple(records)
        number = len(self.saves) + 1
        self.token = FileToken(True, number, len(self.records), f"refs-{number}")
        return ReferenceSaveResult("saved", self.token)


class FakeSourceStore:
    def __init__(self, notes):
        self.path = "/work/paper.md.source-notes.md"
        self.notes = tuple(notes)
        self.token = FileToken(True, 1, 10, "notes-1")
        self.saves = []
        self.fail_next = None
        self.diagnostics = ()

    def load(self):
        return SourceNoteSnapshot(self.notes, self.token, self.diagnostics)

    def save(self, notes, expected_token, *, force=False):
        self.saves.append((tuple(notes), expected_token, force))
        if expected_token != self.token and not force:
            return SourceNoteSaveResult("conflict", self.token, "Source Notes changed externally.")
        if self.fail_next:
            status, message, callback = self.fail_next
            self.fail_next = None
            if callback:
                callback()
            return SourceNoteSaveResult(status, self.token, message)
        self.notes = tuple(notes)
        number = len(self.saves) + 1
        self.token = FileToken(True, number, len(self.notes), f"notes-{number}")
        return SourceNoteSaveResult("saved", self.token)


class TagIntegrityControllerTests(unittest.TestCase):
    def setUp(self):
        self.refs = FakeReferenceStore((
            ReferenceRecord(key="r1", title="One", tags=("Faith", "method")),
            ReferenceRecord(key="r2", title="Two", tags=("faith",)),
        ))
        self.notes = FakeSourceStore((
            SourceNote(id="sn-1", kind="comment", text="Note", tags=(" FAITH ",), modified="old"),
        ))
        self.refreshes = []
        self.controller = TagIntegrityController(
            reference_store=self.refs,
            source_note_store_factory=lambda _path: self.notes,
            document_path_provider=lambda: "/work/paper.md",
            refresh_references=lambda: self.refreshes.append("references"),
            refresh_source_notes=lambda: self.refreshes.append("notes"),
            now_provider=lambda: "stamp",
        )

    def test_inventory_is_read_only_and_counts_both_authorities(self):
        inventory = self.controller.inventory()
        faith = inventory.get("faith")
        self.assertEqual(faith.reference_count, 2)
        self.assertEqual(faith.source_note_count, 1)
        self.assertEqual(self.refs.saves, [])
        self.assertEqual(self.notes.saves, [])

    def test_successful_rename_merge_updates_two_authorities(self):
        plan = self.controller.prepare(
            action=TAG_ACTION_RENAME_MERGE,
            source_tag="Faith",
            target_tag="doctrine",
        )
        result = self.controller.apply(plan)
        self.assertTrue(result.succeeded)
        self.assertEqual(self.refs.records[0].tags, ("doctrine", "method"))
        self.assertEqual(self.refs.records[1].tags, ("doctrine",))
        self.assertEqual(self.notes.notes[0].tags, ("doctrine",))
        self.assertEqual(self.notes.notes[0].modified, "stamp")
        self.assertEqual(self.refreshes, ["references", "notes"])

    def test_stale_token_writes_nothing(self):
        plan = self.controller.prepare(
            action=TAG_ACTION_REMOVE,
            source_tag="Faith",
        )
        self.refs.token = FileToken(True, 9, 9, "external")
        result = self.controller.apply(plan)
        self.assertEqual(result.status, "stale")
        self.assertEqual(self.refs.saves, [])
        self.assertEqual(self.notes.saves, [])

    def test_source_failure_rolls_back_references_without_force(self):
        self.notes.fail_next = ("error", "disk full", None)
        plan = self.controller.prepare(
            action=TAG_ACTION_REMOVE,
            source_tag="Faith",
        )
        result = self.controller.apply(plan)
        self.assertEqual(result.status, "error")
        self.assertEqual(self.refs.records[0].tags, ("Faith", "method"))
        self.assertEqual(len(self.refs.saves), 2)
        self.assertFalse(self.refs.saves[-1][2])

    def test_external_change_blocks_compensating_rollback(self):
        def external_change():
            self.refs.records = (ReferenceRecord(key="external", title="External", tags=("external",)),)
            self.refs.token = FileToken(True, 99, 99, "external")

        self.notes.fail_next = ("error", "sidecar failed", external_change)
        plan = self.controller.prepare(
            action=TAG_ACTION_REMOVE,
            source_tag="Faith",
        )
        result = self.controller.apply(plan)
        self.assertEqual(result.status, "recovery-required")
        self.assertTrue(result.recovery_errors)
        self.assertEqual(self.refs.records[0].key, "external")

    def test_reference_only_scope_does_not_write_source_notes(self):
        plan = self.controller.prepare(
            action=TAG_ACTION_REMOVE,
            scope=TAG_SCOPE_REFERENCES,
            source_tag="Faith",
        )
        result = self.controller.apply(plan)
        self.assertTrue(result.succeeded)
        self.assertEqual(len(self.refs.saves), 1)
        self.assertEqual(self.notes.saves, [])
        self.assertEqual(self.notes.notes[0].tags, ("FAITH",))

    def test_approved_plan_can_only_be_applied_once(self):
        plan = self.controller.prepare(
            action=TAG_ACTION_NORMALIZE_ALL,
        )
        self.assertTrue(self.controller.apply(plan).succeeded)
        second = self.controller.apply(plan)
        self.assertEqual(second.status, "stale")


if __name__ == "__main__":
    unittest.main()
