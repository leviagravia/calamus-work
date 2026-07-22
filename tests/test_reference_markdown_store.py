import os
import tempfile
import unittest
from pathlib import Path

from calamus_reference_store import (
    MarkdownReferenceStore,
    default_references_path,
    file_token,
    parse_references_markdown,
    serialize_references_markdown,
)
from calamus_references import ReferenceRecord


class ReferenceMarkdownStoreTests(unittest.TestCase):
    def sample(self):
        return ReferenceRecord(
            key="ratzinger1968introduction",
            type="book",
            authors=("Ratzinger, Joseph", "Smith, John"),
            title="Introduction to Christianity",
            year="1968",
            publisher="Herder",
            location="Freiburg",
            doi="10.1234/example",
            tags=("faith", "christology"),
            annotation="A general note.\nSecond line.",
            extra_fields=(("Original Title", "Einführung in das Christentum"),),
        )

    def test_default_path_uses_xdg_data_location(self):
        path = default_references_path(home="/home/test", data_home="/data")
        self.assertEqual(path, "/data/calamus/research/references.md")

    def test_roundtrip_preserves_semantic_fields_annotation_and_unknown_fields(self):
        record = self.sample()
        encoded = serialize_references_markdown((record,))
        self.assertIn("# Calamus References v1", encoded)
        self.assertEqual(encoded.count("Author:"), 2)
        self.assertIn("Original Title: Einführung", encoded)
        records, diagnostics = parse_references_markdown(encoded)
        self.assertEqual(diagnostics, ())
        self.assertEqual(records, (record,))

    def test_duplicate_and_malformed_records_are_blocking_diagnostics(self):
        text = """# Calamus References v1

## duplicate
Title: First

## duplicate
Title: Second

## bad key
Title: Invalid
"""
        records, diagnostics = parse_references_markdown(text)
        self.assertEqual(tuple(item.key for item in records), ("duplicate",))
        self.assertGreaterEqual(len(diagnostics), 2)
        self.assertTrue(all(item.blocking for item in diagnostics))

    def test_loading_existing_markdown_does_not_rewrite_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "references.md")
            raw = "# Calamus References v1\n\n## key2020\nTitle: Title\nCustom Field: value\n"
            Path(path).write_text(raw, encoding="utf-8")
            before = Path(path).read_bytes()
            snapshot = MarkdownReferenceStore(path).load()
            self.assertEqual(Path(path).read_bytes(), before)
            self.assertEqual(snapshot.records[0].extra_fields, (("Custom Field", "value"),))

    def test_save_is_atomic_and_detects_external_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "research", "references.md")
            store = MarkdownReferenceStore(path)
            initial = store.load()
            saved = store.save((self.sample(),), initial.token)
            self.assertTrue(saved.saved)
            self.assertTrue(os.path.exists(path))
            self.assertFalse(os.path.exists(path + ".tmp"))

            Path(path).write_text(Path(path).read_text(encoding="utf-8") + "\nExternal\n", encoding="utf-8")
            conflict = store.save((), saved.token)
            self.assertEqual(conflict.status, "conflict")
            forced = store.save((), conflict.token, force=True)
            self.assertTrue(forced.saved)
            self.assertEqual(file_token(path), forced.token)

    def test_malformed_library_is_loaded_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "references.md")
            Path(path).write_text("## bad key\nTitle: Example\n", encoding="utf-8")
            snapshot = MarkdownReferenceStore(path).load()
            self.assertFalse(snapshot.writable)
            self.assertTrue(snapshot.diagnostics)


if __name__ == "__main__":
    unittest.main()
