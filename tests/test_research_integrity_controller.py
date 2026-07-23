import unittest

from calamus_document_structure import build_document_structure
from calamus_reference_store import ReferenceLibrarySnapshot, ReferenceSaveResult
from calamus_research_file import FileToken
from calamus_research_integrity_controller import ResearchIntegrityController
from calamus_references import ReferenceRecord
from calamus_source_note_store import SourceNoteSaveResult, SourceNoteSnapshot
from calamus_source_notes import SourceNote


class FakeReferenceStore:
    def __init__(self, records):
        self.records = tuple(records)
        self.token = FileToken(True, 1, 10, "refs-1")
        self.saves = []
        self.fail_next = None

    def load(self):
        return ReferenceLibrarySnapshot(self.records, self.token, ())

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


class FakeSourceNoteStore:
    def __init__(self, notes):
        self.path = "/work/paper.md.source-notes.md"
        self.notes = tuple(notes)
        self.token = FileToken(True, 1, 10, "notes-1")
        self.saves = []
        self.fail_next = None

    def load(self):
        return SourceNoteSnapshot(self.notes, self.token, ())

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


class ResearchIntegrityControllerTests(unittest.TestCase):
    def setUp(self):
        self.references = FakeReferenceStore((
            ReferenceRecord(key="oldkey", title="Title", authors=("A",), year="2020"),
        ))
        self.notes = FakeSourceNoteStore((
            SourceNote(id="sn-1", kind="quote", text="Quote", reference_key="oldkey"),
        ))
        self.state = {"text": "Use [@oldkey, p. 4].\n"}
        self.refreshes = []
        self.replace_calls = []
        self.replace_result = True

        def replace(before, after):
            self.replace_calls.append((before, after))
            if self.state["text"] != before or not self.replace_result:
                return False
            self.state["text"] = after
            return True

        self.controller = ResearchIntegrityController(
            reference_store=self.references,
            source_note_store_factory=lambda _path: self.notes,
            document_path_provider=lambda: "/work/paper.md",
            document_text_provider=lambda: self.state["text"],
            document_structure_provider=lambda: build_document_structure(self.state["text"]),
            replace_document_text=replace,
            refresh_references=lambda: self.refreshes.append("references"),
            refresh_source_notes=lambda: self.refreshes.append("notes"),
        )

    def test_success_updates_three_authorities_and_preserves_alias(self):
        plan = self.controller.prepare_migration("oldkey", "newkey")
        result = self.controller.apply_migration(plan)
        self.assertTrue(result.succeeded)
        self.assertEqual(self.references.records[0].key, "newkey")
        self.assertEqual(self.references.records[0].aliases, ("oldkey",))
        self.assertEqual(self.notes.notes[0].reference_key, "newkey")
        self.assertIn("[@newkey, p. 4]", self.state["text"])
        self.assertEqual(len(self.replace_calls), 1)
        self.assertEqual(self.refreshes, ["references", "notes"])

    def test_stale_preview_writes_nothing(self):
        plan = self.controller.prepare_migration("oldkey", "newkey")
        self.state["text"] += "External edit\n"
        result = self.controller.apply_migration(plan)
        self.assertEqual(result.status, "stale")
        self.assertEqual(self.references.saves, [])
        self.assertEqual(self.notes.saves, [])
        self.assertEqual(self.references.records[0].key, "oldkey")

    def test_source_note_failure_rolls_back_references(self):
        self.notes.fail_next = ("error", "disk full", None)
        plan = self.controller.prepare_migration("oldkey", "newkey")
        result = self.controller.apply_migration(plan)
        self.assertEqual(result.status, "error")
        self.assertEqual(self.references.records[0].key, "oldkey")
        self.assertEqual(self.state["text"], plan.document_before)
        self.assertEqual(len(self.references.saves), 2)

    def test_external_change_blocks_rollback_without_overwrite(self):
        def external_change():
            self.references.records = (
                ReferenceRecord(key="external", title="External"),
            )
            self.references.token = FileToken(True, 99, 99, "external")

        self.notes.fail_next = ("error", "sidecar failed", external_change)
        plan = self.controller.prepare_migration("oldkey", "newkey")
        result = self.controller.apply_migration(plan)
        self.assertEqual(result.status, "recovery-required")
        self.assertTrue(result.recovery_errors)
        self.assertEqual(self.references.records[0].key, "external")
        self.assertEqual(self.references.saves[-1][2], False)

    def test_document_gateway_failure_rolls_back_persistent_files(self):
        self.replace_result = False
        plan = self.controller.prepare_migration("oldkey", "newkey")
        result = self.controller.apply_migration(plan)
        self.assertEqual(result.status, "error")
        self.assertEqual(self.references.records[0].key, "oldkey")
        self.assertEqual(self.notes.notes[0].reference_key, "oldkey")
        self.assertEqual(self.state["text"], plan.document_before)

    def test_research_check_is_read_only(self):
        report = self.controller.research_check()
        self.assertGreaterEqual(report.reference_count, 1)
        self.assertEqual(self.references.saves, [])
        self.assertEqual(self.notes.saves, [])
        self.assertEqual(self.replace_calls, [])


if __name__ == "__main__":
    unittest.main()
