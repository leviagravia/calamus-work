"""Real-filesystem transaction proofs for W86 Tag Integrity."""
from pathlib import Path
import tempfile
import unittest

from calamus_reference_store import (
    MarkdownReferenceStore,
    serialize_references_markdown,
)
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken
from calamus_source_note_store import (
    MarkdownSourceNoteStore,
    SourceNoteSaveResult,
    serialize_source_notes_markdown,
)
from calamus_source_notes import SourceNote
from calamus_tag_integrity import TAG_ACTION_REMOVE, TAG_ACTION_RENAME_MERGE
from calamus_tag_integrity_controller import TagIntegrityController


class _FailingRealSourceStore:
    """Load from a real sidecar and fail the first real transaction boundary."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._real = MarkdownSourceNoteStore(path)
        self._failed = False

    def load(self):
        return self._real.load()

    def save(self, notes, expected_token: FileToken, *, force: bool = False):
        self.assert_no_force(force)
        if not self._failed:
            self._failed = True
            return SourceNoteSaveResult("error", expected_token, "injected sidecar failure")
        return self._real.save(notes, expected_token, force=force)

    @staticmethod
    def assert_no_force(force: bool) -> None:
        if force:
            raise AssertionError("W86 must never bypass conflict detection")


class TagIntegrityRealFilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.references_path = root / "data" / "calamus" / "research" / "references.md"
        self.document_path = root / "Documents" / "paper.md"
        self.sidecar_path = Path(str(self.document_path) + ".source-notes.md")
        self.references_path.parent.mkdir(parents=True)
        self.document_path.parent.mkdir(parents=True)
        self.document_path.write_text("# Paper\n\nBody.\n", encoding="utf-8")
        self.references = (
            ReferenceRecord(key="r1", title="One", tags=("Faith", "method")),
            ReferenceRecord(key="r2", title="Two", tags=("faith",)),
        )
        self.notes = (
            SourceNote(id="sn-1", kind="comment", text="Note", tags=("FAITH",)),
        )
        self.references_path.write_text(
            serialize_references_markdown(self.references), encoding="utf-8"
        )
        self.sidecar_path.write_text(
            serialize_source_notes_markdown(self.notes), encoding="utf-8"
        )
        self.refreshes = []

    def tearDown(self):
        self.temp.cleanup()

    def _controller(self, source_factory=MarkdownSourceNoteStore):
        return TagIntegrityController(
            reference_store=MarkdownReferenceStore(str(self.references_path)),
            source_note_store_factory=source_factory,
            document_path_provider=lambda: str(self.document_path),
            refresh_references=lambda: self.refreshes.append("references"),
            refresh_source_notes=lambda: self.refreshes.append("notes"),
            now_provider=lambda: "2026-07-25T12:00:00+02:00",
        )

    def test_real_atomic_stores_update_both_authorities_and_not_document(self):
        document_before = self.document_path.read_bytes()
        controller = self._controller()
        plan = controller.prepare(
            action=TAG_ACTION_RENAME_MERGE,
            source_tag="faith",
            target_tag="doctrine",
        )
        result = controller.apply(plan)
        self.assertTrue(result.succeeded)

        records = MarkdownReferenceStore(str(self.references_path)).load().records
        notes = MarkdownSourceNoteStore(str(self.sidecar_path)).load().notes
        self.assertEqual(records[0].tags, ("doctrine", "method"))
        self.assertEqual(records[1].tags, ("doctrine",))
        self.assertEqual(notes[0].tags, ("doctrine",))
        self.assertEqual(notes[0].modified, "2026-07-25T12:00:00+02:00")
        self.assertEqual(self.document_path.read_bytes(), document_before)
        self.assertEqual(self.refreshes, ["references", "notes"])

    def test_real_external_change_after_preview_fails_closed_without_writes(self):
        controller = self._controller()
        plan = controller.prepare(action=TAG_ACTION_REMOVE, source_tag="faith")
        references_before = self.references_path.read_bytes()
        sidecar_before = self.sidecar_path.read_bytes()
        self.sidecar_path.write_text(
            self.sidecar_path.read_text(encoding="utf-8") + "\n<!-- external -->\n",
            encoding="utf-8",
        )
        externally_changed = self.sidecar_path.read_bytes()

        result = controller.apply(plan)
        self.assertEqual(result.status, "stale")
        self.assertEqual(self.references_path.read_bytes(), references_before)
        self.assertEqual(self.sidecar_path.read_bytes(), externally_changed)
        self.assertNotEqual(self.sidecar_path.read_bytes(), sidecar_before)
        self.assertEqual(self.refreshes, [])

    def test_real_reference_file_is_byte_restored_when_sidecar_commit_fails(self):
        references_before = self.references_path.read_bytes()
        sidecar_before = self.sidecar_path.read_bytes()
        controller = self._controller(_FailingRealSourceStore)
        plan = controller.prepare(action=TAG_ACTION_REMOVE, source_tag="faith")

        result = controller.apply(plan)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.recovery_errors, ())
        self.assertEqual(self.references_path.read_bytes(), references_before)
        self.assertEqual(self.sidecar_path.read_bytes(), sidecar_before)
        self.assertEqual(self.refreshes, [])


if __name__ == "__main__":
    unittest.main()
