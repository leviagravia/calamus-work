import unittest

from calamus_reference_store import ReferenceLibrarySnapshot, ReferenceSaveResult
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken
from calamus_scratchpad import ScratchpadEntry
from calamus_scratchpad_store import ScratchpadDiagnostic, ScratchpadSaveResult, ScratchpadSnapshot
from calamus_source_note_store import SourceNoteSaveResult, SourceNoteSnapshot
from calamus_source_notes import SourceNote
from calamus_tag_integrity import TAG_ACTION_REMOVE, TAG_SCOPE_ALL, TAG_SCOPE_BOTH
from calamus_tag_integrity_controller import TagIntegrityController


class _StoreBase:
    def __init__(self, values, prefix):
        self.values = tuple(values)
        self.prefix = prefix
        self.token = FileToken(True, 1, len(self.values), prefix + "-1")
        self.saves = []
        self.fail_next = False

    def _save(self, values, expected_token, result_type):
        values = tuple(values)
        self.saves.append((values, expected_token, False))
        if expected_token != self.token:
            return result_type("conflict", self.token, self.prefix + " stale")
        if self.fail_next:
            self.fail_next = False
            return result_type("error", self.token, self.prefix + " injected failure")
        self.values = values
        number = len(self.saves) + 1
        self.token = FileToken(True, number, len(values), f"{self.prefix}-{number}")
        return result_type("saved", self.token)


class FakeReferences(_StoreBase):
    def __init__(self, values):
        super().__init__(values, "refs")

    def load(self):
        return ReferenceLibrarySnapshot(self.values, self.token, ())

    def save(self, records, expected_token, *, force=False):
        self.assert_no_force(force)
        return self._save(records, expected_token, ReferenceSaveResult)

    @staticmethod
    def assert_no_force(force):
        if force:
            raise AssertionError("W94 must not force tag writes")


class FakeNotes(_StoreBase):
    path = "/work/paper.md.source-notes.md"

    def __init__(self, values):
        super().__init__(values, "notes")

    def load(self):
        return SourceNoteSnapshot(self.values, self.token, ())

    def save(self, notes, expected_token, *, force=False):
        FakeReferences.assert_no_force(force)
        return self._save(notes, expected_token, SourceNoteSaveResult)


class FakeScratchpad(_StoreBase):
    path = "/work/paper.md.scratchpad.md"

    def __init__(self, values):
        super().__init__(values, "scratch")
        self.diagnostics = ()

    def load(self):
        return ScratchpadSnapshot(self.values, self.token, self.diagnostics)

    def save(self, entries, expected_token, *, force=False):
        FakeReferences.assert_no_force(force)
        return self._save(entries, expected_token, ScratchpadSaveResult)


class W94TagsTransactionTests(unittest.TestCase):
    def setUp(self):
        self.refs = FakeReferences((
            ReferenceRecord(key="r1", title="One", tags=("Faith",)),
        ))
        self.notes = FakeNotes((
            SourceNote(id="sn-1", kind="comment", text="Note", tags=("faith",)),
        ))
        self.scratch = FakeScratchpad((
            ScratchpadEntry(
                id="sp-1", type="note", title="Entry", body="Body", tags=("FAITH",)
            ),
        ))
        self.refreshes = []
        self.controller = TagIntegrityController(
            reference_store=self.refs,
            source_note_store_factory=lambda _path: self.notes,
            scratchpad_store_factory=lambda _path: self.scratch,
            document_path_provider=lambda: "/work/paper.md",
            refresh_references=lambda: self.refreshes.append("references"),
            refresh_source_notes=lambda: self.refreshes.append("source-notes"),
            refresh_scratchpad=lambda: self.refreshes.append("scratchpad"),
            now_provider=lambda: "stamp",
        )

    def test_success_updates_and_refreshes_three_authorities(self):
        plan = self.controller.prepare(
            action=TAG_ACTION_REMOVE,
            scope=TAG_SCOPE_ALL,
            source_tag="faith",
        )
        result = self.controller.apply(plan)
        self.assertTrue(result.succeeded)
        self.assertEqual(self.refs.values[0].tags, ())
        self.assertEqual(self.notes.values[0].tags, ())
        self.assertEqual(self.scratch.values[0].tags, ())
        self.assertEqual(self.refreshes, ["references", "source-notes", "scratchpad"])

    def test_scratchpad_failure_compensates_source_notes_then_references(self):
        original_refs = self.refs.values
        original_notes = self.notes.values
        original_scratch = self.scratch.values
        self.scratch.fail_next = True
        plan = self.controller.prepare(
            action=TAG_ACTION_REMOVE,
            scope=TAG_SCOPE_ALL,
            source_tag="faith",
        )
        result = self.controller.apply(plan)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.recovery_errors, ())
        self.assertEqual(self.refs.values, original_refs)
        self.assertEqual(self.notes.values, original_notes)
        self.assertEqual(self.scratch.values, original_scratch)
        self.assertEqual(len(self.refs.saves), 2)
        self.assertEqual(len(self.notes.saves), 2)
        self.assertEqual(len(self.scratch.saves), 1)
        self.assertEqual(self.refreshes, [])

    def test_external_scratchpad_change_after_preview_fails_closed(self):
        plan = self.controller.prepare(
            action=TAG_ACTION_REMOVE,
            scope=TAG_SCOPE_ALL,
            source_tag="faith",
        )
        self.scratch.token = FileToken(True, 99, 99, "external")
        result = self.controller.apply(plan)
        self.assertEqual(result.status, "stale")
        self.assertEqual(self.refs.saves, [])
        self.assertEqual(self.notes.saves, [])
        self.assertEqual(self.scratch.saves, [])

    def test_legacy_two_authority_scope_ignores_unselected_scratchpad_diagnostics(self):
        self.scratch.diagnostics = (ScratchpadDiagnostic(3, "broken Scratchpad"),)
        inventory = self.controller.inventory(scope=TAG_SCOPE_BOTH)
        self.assertIsNotNone(inventory.get("faith"))
        self.assertEqual(inventory.get("faith").scratchpad_count, 0)

    def test_all_scope_blocks_on_scratchpad_diagnostics(self):
        self.scratch.diagnostics = (ScratchpadDiagnostic(3, "broken Scratchpad"),)
        with self.assertRaisesRegex(ValueError, "Scratchpad contains blocking diagnostics"):
            self.controller.inventory(scope=TAG_SCOPE_ALL)


if __name__ == "__main__":
    unittest.main()
