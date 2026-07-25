import os
import tempfile
import unittest
from pathlib import Path

from calamus_document_structure import build_document_structure
from calamus_reference_store import MarkdownReferenceStore
from calamus_references import ReferenceRecord
from calamus_research_export import FULL_RESEARCH_DOSSIER
from calamus_research_export_controller import ResearchExportController
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
from calamus_source_notes import SourceNote


class ResearchExportControllerTests(unittest.TestCase):
    def make_controller(self, tmp, *, document_path=True, text="See [@ref1]."):
        document = os.path.join(tmp, "paper.md")
        if document_path:
            Path(document).write_text("disk version", encoding="utf-8")
        references = os.path.join(tmp, "references.md")
        reference_store = MarkdownReferenceStore(references)
        initial = reference_store.load()
        saved = reference_store.save(
            (ReferenceRecord(key="ref1", title="A Book", authors=("Author, A",), year="2020"),),
            initial.token,
        )
        self.assertTrue(saved.saved)
        if document_path:
            note_store = MarkdownSourceNoteStore(source_notes_path(document))
            note_store.save(
                (SourceNote(id="sn-1", kind="quote", text="Evidence", reference_key="ref1"),),
                note_store.load().token,
            )
        controller = ResearchExportController(
            reference_store=reference_store,
            document_path_provider=lambda: document if document_path else None,
            document_text_provider=lambda: text,
            document_structure_provider=lambda: build_document_structure(text),
        )
        return controller, document, references

    def test_atomic_export_preserves_all_three_authorities(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, document, references = self.make_controller(tmp)
            sidecar = source_notes_path(document)
            before = {
                document: Path(document).read_bytes(),
                references: Path(references).read_bytes(),
                sidecar: Path(sidecar).read_bytes(),
            }
            output = os.path.join(tmp, "paper-research-dossier.md")
            result = controller.export(FULL_RESEARCH_DOSSIER, output)
            self.assertTrue(result.exported, result.message)
            self.assertTrue(Path(output).is_file())
            self.assertFalse(Path(output + ".tmp").exists())
            self.assertIn("Complete Research Dossier", Path(output).read_text(encoding="utf-8"))
            for path, content in before.items():
                self.assertEqual(Path(path).read_bytes(), content)

    def test_unsaved_document_fails_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, _ = self.make_controller(tmp, document_path=False)
            output = os.path.join(tmp, "out.md")
            result = controller.export(FULL_RESEARCH_DOSSIER, output)
            self.assertFalse(result.exported)
            self.assertIn("Save the current document", result.message)
            self.assertFalse(os.path.exists(output))

    def test_protected_authority_destinations_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, document, references = self.make_controller(tmp)
            for protected in (document, references, source_notes_path(document)):
                result = controller.export(FULL_RESEARCH_DOSSIER, protected)
                self.assertFalse(result.exported)
                self.assertIn("canonical Research authority", result.message)

    def test_only_existing_folder_and_markdown_suffix_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, _ = self.make_controller(tmp)
            wrong_suffix = controller.export(FULL_RESEARCH_DOSSIER, os.path.join(tmp, "out.txt"))
            self.assertFalse(wrong_suffix.exported)
            self.assertIn(".md extension", wrong_suffix.message)
            missing_folder = controller.export(FULL_RESEARCH_DOSSIER, os.path.join(tmp, "missing", "out.md"))
            self.assertFalse(missing_folder.exported)
            self.assertIn("folder does not exist", missing_folder.message)

    def test_blocking_reference_diagnostics_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, _, references = self.make_controller(tmp)
            Path(references).write_text("## bad key\nTitle: Bad\n", encoding="utf-8")
            result = controller.export(FULL_RESEARCH_DOSSIER, os.path.join(tmp, "out.md"))
            self.assertFalse(result.exported)
            self.assertIn("blocking diagnostics", result.message)

    def test_blocking_source_note_diagnostics_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            controller, document, _ = self.make_controller(tmp)
            Path(source_notes_path(document)).write_text("## bad id\nKind: quote\n", encoding="utf-8")
            result = controller.export(FULL_RESEARCH_DOSSIER, os.path.join(tmp, "out.md"))
            self.assertFalse(result.exported)
            self.assertIn("blocking diagnostics", result.message)


if __name__ == "__main__":
    unittest.main()
