from pathlib import Path
import tempfile
import unittest

from calamus_document_structure import build_document_structure
from calamus_reference_integrity import run_research_check
from calamus_reference_set_store import MarkdownReferenceSetStore
from calamus_reference_sets import ReferenceSet
from calamus_reference_store import MarkdownReferenceStore
from calamus_related_references import related_keys
from calamus_research_integrity_controller import ResearchIntegrityController
from calamus_references import ReferenceRecord
from calamus_source_note_store import MarkdownSourceNoteStore, source_notes_path
from calamus_source_notes import SourceNote


class W89ReferenceMigrationRealFileTests(unittest.TestCase):
    def _fixture(self, root: Path, *, replace_result=True):
        document_path = root / "article.md"
        document_text = "# Article {#article}\n\nUse [@oldkey, p. 10].\n"
        document_path.write_text(document_text, encoding="utf-8")
        references = MarkdownReferenceStore(str(root / "references.md"))
        reference_sets = MarkdownReferenceSetStore(str(root / "reference-sets.md"))
        sidecar_path = source_notes_path(str(document_path))
        self.assertIsNotNone(sidecar_path)
        source_notes = MarkdownSourceNoteStore(sidecar_path)

        self.assertTrue(references.save(
            (
                ReferenceRecord(
                    key="oldkey", title="Old", authors=("Author, A",), year="2020",
                    extra_fields=(("Related Keys", "other"),),
                ),
                ReferenceRecord(
                    key="other", title="Other", authors=("Author, B",), year="2021",
                    extra_fields=(("Related Keys", "oldkey"),),
                ),
            ),
            references.load().token,
        ).saved)
        self.assertTrue(reference_sets.save(
            (ReferenceSet("Core", "Main sources", ("oldkey", "other")),),
            reference_sets.load().token,
        ).saved)
        self.assertTrue(source_notes.save(
            (SourceNote(id="sn-1", kind="quote", text="Quoted", reference_key="oldkey"),),
            source_notes.load().token,
        ).saved)

        state = {"text": document_text}
        refreshes = []

        def replace(before, after):
            if state["text"] != before or not replace_result:
                return False
            state["text"] = after
            return True

        controller = ResearchIntegrityController(
            reference_store=references,
            reference_set_store=reference_sets,
            source_note_store_factory=lambda path: MarkdownSourceNoteStore(path),
            document_path_provider=lambda: str(document_path),
            document_text_provider=lambda: state["text"],
            document_structure_provider=lambda: build_document_structure(state["text"]),
            replace_document_text=replace,
            refresh_references=lambda: refreshes.append("references"),
            refresh_source_notes=lambda: refreshes.append("notes"),
            refresh_reference_sets=lambda: refreshes.append("sets"),
        )
        return controller, references, reference_sets, source_notes, state, refreshes

    def test_real_files_rename_updates_four_authorities_and_integrity_is_clean(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller, references, sets, notes, state, refreshes = self._fixture(Path(temporary))
            plan = controller.prepare_migration("oldkey", "newkey")
            self.assertEqual(plan.impact.related_key_occurrences, 1)
            self.assertEqual(plan.impact.reference_set_occurrences, 1)
            self.assertTrue(controller.apply_migration(plan).succeeded)

            reference_snapshot = references.load()
            self.assertEqual(reference_snapshot.diagnostics, ())
            by_key = {record.key: record for record in reference_snapshot.records}
            self.assertEqual(by_key["newkey"].aliases, ("oldkey",))
            self.assertEqual(related_keys(by_key["newkey"]), ("other",))
            self.assertEqual(related_keys(by_key["other"]), ("newkey",))
            self.assertEqual(sets.load().sets[0].members, ("newkey", "other"))
            self.assertEqual(notes.load().notes[0].reference_key, "newkey")
            self.assertIn("[@newkey, p. 10]", state["text"])
            self.assertEqual(refreshes, ["references", "notes", "sets"])

            report = run_research_check(
                reference_snapshot.records,
                state["text"],
                notes.load().notes,
                build_document_structure(state["text"]),
                sets.load().sets,
            )
            relation_or_set_issues = {
                issue.kind for issue in report.issues
                if issue.kind.startswith("related-key-") or issue.kind.startswith("reference-set-")
            }
            self.assertEqual(relation_or_set_issues, set())

    def test_real_files_stale_reference_set_blocks_every_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller, references, sets, notes, state, _ = self._fixture(Path(temporary))
            plan = controller.prepare_migration("oldkey", "newkey")
            sets_path = Path(sets.path)
            sets_path.write_text(sets_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = controller.apply_migration(plan)
            self.assertEqual(result.status, "stale")
            self.assertEqual({record.key for record in references.load().records}, {"oldkey", "other"})
            self.assertEqual(notes.load().notes[0].reference_key, "oldkey")
            self.assertIn("[@oldkey, p. 10]", state["text"])

    def test_real_files_document_gateway_failure_rolls_back_all_persistent_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller, references, sets, notes, state, _ = self._fixture(
                Path(temporary), replace_result=False
            )
            before_references = Path(references.path).read_bytes()
            before_sets = Path(sets.path).read_bytes()
            before_notes = Path(notes.path).read_bytes()
            result = controller.apply_migration(controller.prepare_migration("oldkey", "newkey"))
            self.assertEqual(result.status, "error")
            self.assertEqual(Path(references.path).read_bytes(), before_references)
            self.assertEqual(Path(sets.path).read_bytes(), before_sets)
            self.assertEqual(Path(notes.path).read_bytes(), before_notes)
            self.assertIn("[@oldkey, p. 10]", state["text"])


if __name__ == "__main__":
    unittest.main()
