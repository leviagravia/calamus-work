import os
import tempfile
import unittest
from pathlib import Path

from calamus_document_structure import build_document_structure
from calamus_reference_store import MarkdownReferenceStore
from calamus_research_integrity_controller import ResearchIntegrityController
from calamus_references import ReferenceRecord
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
from calamus_source_notes import SourceLocator, SourceNote


class ReferenceIntegrityFilesystemIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.references_path = root / "data" / "references.md"
        self.document_path = root / "paper.md"
        self.document_path.write_text("# Part {#part}\nUse [@oldkey, p. 12].\n", encoding="utf-8")
        self.reference_store = MarkdownReferenceStore(str(self.references_path))
        initial = self.reference_store.load()
        saved = self.reference_store.save((
            ReferenceRecord(
                key="oldkey",
                title="Book",
                authors=("Author, A",),
                year="2020",
            ),
        ), initial.token)
        self.assertTrue(saved.saved)
        self.source_store = MarkdownSourceNoteStore(source_notes_path(str(self.document_path)))
        notes_initial = self.source_store.load()
        notes_saved = self.source_store.save((
            SourceNote(
                id="sn-1",
                kind="quote",
                text="Quote",
                reference_key="oldkey",
                locator=SourceLocator(page="12"),
                target="#part",
            ),
        ), notes_initial.token)
        self.assertTrue(notes_saved.saved)
        self.refreshes = []

        def replace_document(before, after):
            current = self.document_path.read_text(encoding="utf-8")
            if current != before:
                return False
            self.document_path.write_text(after, encoding="utf-8", newline="\n")
            return True

        self.controller = ResearchIntegrityController(
            reference_store=self.reference_store,
            source_note_store_factory=MarkdownSourceNoteStore,
            document_path_provider=lambda: str(self.document_path),
            document_text_provider=lambda: self.document_path.read_text(encoding="utf-8"),
            document_structure_provider=lambda: build_document_structure(
                self.document_path.read_text(encoding="utf-8")
            ),
            replace_document_text=replace_document,
            refresh_references=lambda: self.refreshes.append("references"),
            refresh_source_notes=lambda: self.refreshes.append("source-notes"),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_markdown_files_migrate_without_hidden_state(self):
        plan = self.controller.prepare_migration("oldkey", "newkey")
        result = self.controller.apply_migration(plan)
        self.assertTrue(result.succeeded)
        references = self.reference_store.load()
        self.assertTrue(references.writable)
        self.assertEqual(references.records[0].key, "newkey")
        self.assertEqual(references.records[0].aliases, ("oldkey",))
        notes = self.source_store.load()
        self.assertEqual(notes.notes[0].reference_key, "newkey")
        self.assertIn("[@newkey, p. 12]", self.document_path.read_text(encoding="utf-8"))
        self.assertEqual(self.refreshes, ["references", "source-notes"])
        self.assertFalse(os.path.exists(str(self.references_path) + ".tmp"))
        self.assertFalse(os.path.exists(self.source_store.path + ".tmp"))

    def test_real_external_reference_change_after_preview_fails_closed(self):
        plan = self.controller.prepare_migration("oldkey", "newkey")
        raw = self.references_path.read_text(encoding="utf-8")
        self.references_path.write_text(raw + "\nExternal Field: untouched\n", encoding="utf-8")
        before = self.references_path.read_bytes()
        result = self.controller.apply_migration(plan)
        self.assertEqual(result.status, "stale")
        self.assertEqual(self.references_path.read_bytes(), before)
        self.assertIn("[@oldkey", self.document_path.read_text(encoding="utf-8"))
        self.assertEqual(self.source_store.load().notes[0].reference_key, "oldkey")

    def test_research_check_does_not_rewrite_real_files(self):
        before = {
            str(self.references_path): self.references_path.read_bytes(),
            str(self.document_path): self.document_path.read_bytes(),
            self.source_store.path: Path(self.source_store.path).read_bytes(),
        }
        report = self.controller.research_check()
        self.assertEqual(report.error_count, 0)
        after = {
            str(self.references_path): self.references_path.read_bytes(),
            str(self.document_path): self.document_path.read_bytes(),
            self.source_store.path: Path(self.source_store.path).read_bytes(),
        }
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
