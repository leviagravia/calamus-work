import os
from pathlib import Path
import tempfile
import unittest

from calamus_bibtex import (
    ACTION_IMPORT, ACTION_MERGE, ACTION_NEW_KEY, BIBLATEX, BIBTEX,
    BibImportDecision,
)
from calamus_bibtex_controller import BibtexController
from calamus_reference_store import MarkdownReferenceStore
from calamus_references import ReferenceRecord


class BibtexControllerTests(unittest.TestCase):
    def make_store(self, tmp, records=()):
        path = os.path.join(tmp, "references.md")
        store = MarkdownReferenceStore(path)
        saved = store.save(tuple(records), store.load().token)
        self.assertTrue(saved.saved)
        return store

    def test_real_import_updates_only_references_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp, (ReferenceRecord(key="old", title="Old"),))
            source = os.path.join(tmp, "library.bib")
            Path(source).write_text('''@book{new, title={New Book}, author={Doe, Jane}, keywords={faith}}''', encoding="utf-8")
            source_before = Path(source).read_bytes()
            refreshes = []
            controller = BibtexController(store, refresh_references=lambda: refreshes.append(True))
            inspection = controller.inspect_import(source, BIBTEX)
            item = inspection.preview.items[0]
            plan = controller.prepare_import(inspection, (BibImportDecision(item.index, ACTION_IMPORT),))
            result = controller.apply_import(plan)
            self.assertTrue(result.succeeded, result.message)
            self.assertEqual(tuple(record.key for record in store.load().records), ("old", "new"))
            self.assertEqual(Path(source).read_bytes(), source_before)
            self.assertEqual(refreshes, [True])

    def test_stale_source_blocks_import_without_reference_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp)
            source = os.path.join(tmp, "library.bib")
            Path(source).write_text('@book{new, title={One}}', encoding="utf-8")
            controller = BibtexController(store)
            inspection = controller.inspect_import(source, BIBTEX)
            plan = controller.prepare_import(inspection, (BibImportDecision(0, ACTION_IMPORT),))
            before = Path(store.path).read_bytes()
            Path(source).write_text('@book{new, title={Changed}}', encoding="utf-8")
            result = controller.apply_import(plan)
            self.assertFalse(result.succeeded)
            self.assertEqual(result.status, "stale")
            self.assertEqual(Path(store.path).read_bytes(), before)

    def test_stale_references_blocks_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp)
            source = os.path.join(tmp, "library.bib")
            Path(source).write_text('@book{new, title={One}}', encoding="utf-8")
            controller = BibtexController(store)
            inspection = controller.inspect_import(source, BIBTEX)
            plan = controller.prepare_import(inspection, (BibImportDecision(0, ACTION_IMPORT),))
            current = store.load()
            store.save((ReferenceRecord(key="external", title="External"),), current.token)
            result = controller.apply_import(plan)
            self.assertFalse(result.succeeded)
            self.assertEqual(result.status, "stale")
            self.assertEqual(tuple(r.key for r in store.load().records), ("external",))

    def test_merge_and_new_key_are_applied_deterministically(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp, (ReferenceRecord(key="same", title="Old"),))
            source = os.path.join(tmp, "library.bib")
            Path(source).write_text('''
@book{same, title={Incoming}, publisher={Publisher}}
@book{same, title={Duplicate input}}
''', encoding="utf-8")
            controller = BibtexController(store)
            inspection = controller.inspect_import(source, BIBTEX)
            decisions = (
                BibImportDecision(0, ACTION_NEW_KEY),
                BibImportDecision(1, ACTION_NEW_KEY),
            )
            plan = controller.prepare_import(inspection, decisions)
            result = controller.apply_import(plan)
            self.assertTrue(result.succeeded, result.message)
            keys = tuple(record.key for record in store.load().records)
            self.assertEqual(len(keys), 3)
            self.assertEqual(len(set(keys)), 3)

    def test_real_export_is_derived_atomic_and_preserves_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp, (
                ReferenceRecord(key="r1", title="Title", authors=("Doe, Jane",), year="2025"),
            ))
            before = Path(store.path).read_bytes()
            controller = BibtexController(store)
            plan = controller.prepare_export(BIBLATEX)
            output = os.path.join(tmp, "references.bib")
            result = controller.apply_export(plan, output)
            self.assertTrue(result.succeeded, result.message)
            self.assertIn("@book{r1,", Path(output).read_text(encoding="utf-8"))
            self.assertFalse(Path(output + ".tmp").exists())
            self.assertEqual(Path(store.path).read_bytes(), before)

    def test_export_stale_and_writer_failure_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp, (ReferenceRecord(key="r1", title="Title"),))
            output = os.path.join(tmp, "references.bib")
            controller = BibtexController(store)
            plan = controller.prepare_export(BIBTEX)
            snap = store.load()
            store.save((*snap.records, ReferenceRecord(key="r2", title="Two")), snap.token)
            stale = controller.apply_export(plan, output)
            self.assertEqual(stale.status, "stale")
            self.assertFalse(os.path.exists(output))

            failing = BibtexController(store, writer=lambda *_: (_ for _ in ()).throw(OSError("disk full")))
            failed = failing.apply_export(failing.prepare_export(BIBTEX), output)
            self.assertEqual(failed.status, "error")
            self.assertFalse(os.path.exists(output))

    def test_import_and_export_reject_symlinks_and_wrong_suffixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp)
            real = os.path.join(tmp, "real.bib")
            Path(real).write_text('@book{x, title={X}}', encoding="utf-8")
            link = os.path.join(tmp, "link.bib")
            os.symlink(real, link)
            controller = BibtexController(store)
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                controller.inspect_import(link, BIBTEX)
            result = controller.apply_export(controller.prepare_export(BIBTEX), os.path.join(tmp, "out.txt"))
            self.assertFalse(result.succeeded)
            self.assertIn(".bib extension", result.message)

    def test_source_replaced_by_symlink_after_preview_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp)
            source = os.path.join(tmp, "library.bib")
            replacement = os.path.join(tmp, "replacement.bib")
            content = '@book{new, title={One}}'
            Path(source).write_text(content, encoding="utf-8")
            Path(replacement).write_text(content, encoding="utf-8")
            controller = BibtexController(store)
            inspection = controller.inspect_import(source, BIBTEX)
            plan = controller.prepare_import(inspection, (BibImportDecision(0, ACTION_IMPORT),))
            before = Path(store.path).read_bytes()
            os.unlink(source)
            os.symlink(replacement, source)
            result = controller.apply_import(plan)
            self.assertEqual(result.status, "stale")
            self.assertEqual(Path(store.path).read_bytes(), before)

    def test_export_rejects_existing_non_regular_destination(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            store = self.make_store(tmp, (ReferenceRecord(key="r1", title="Title"),))
            fifo = os.path.join(tmp, "output.bib")
            os.mkfifo(fifo)
            result = BibtexController(store).apply_export(
                BibtexController(store).prepare_export(BIBTEX),
                fifo,
            )
            self.assertEqual(result.status, "error")
            self.assertIn("regular file", result.message)


if __name__ == "__main__":
    unittest.main()
