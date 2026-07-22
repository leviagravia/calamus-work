import os
import tempfile
import unittest
from pathlib import Path

from calamus_source_note_store import (
    MarkdownSourceNoteStore,
    parse_source_notes_markdown,
    serialize_source_notes_markdown,
    source_notes_path,
)
from calamus_source_notes import SourceLocator, SourceNote


class SourceNoteMarkdownStoreTests(unittest.TestCase):
    def sample(self):
        return SourceNote(
            id="sn-20260721-120000-test",
            reference_key="ratzinger1968introduction",
            kind="quote",
            locator=SourceLocator(page="42", page_end="43", section="Faith"),
            text="Faith is the response to revelation.",
            comment="Useful for the first chapter.",
            tags=("faith", "revelation"),
            created="2026-07-21T12:00:00+02:00",
            modified="2026-07-21T12:05:00+02:00",
            extra_fields=(("Original Language", "de"),),
        )

    def test_sidecar_path_is_next_to_document(self):
        self.assertEqual(
            source_notes_path("/work/thesis.md"),
            "/work/thesis.md.source-notes.md",
        )
        self.assertIsNone(source_notes_path(None))
        self.assertIsNone(source_notes_path(""))

    def test_roundtrip_preserves_locator_text_comment_and_unknown_fields(self):
        note = self.sample()
        encoded = serialize_source_notes_markdown((note,))
        self.assertIn("# Calamus Source Notes v1", encoded)
        self.assertIn("## Source Note: sn-20260721-120000-test", encoded)
        self.assertIn("Page End: 43", encoded)
        self.assertIn("Original Language: de", encoded)
        notes, diagnostics = parse_source_notes_markdown(encoded)
        self.assertEqual(diagnostics, ())
        self.assertEqual(notes, (note,))

    def test_duplicate_and_invalid_notes_are_blocking(self):
        text = """# Calamus Source Notes v1

## Source Note: duplicate
Reference: ref1
Kind: quote

### Text

```text
One
```

### Comment

```text

```

## Source Note: duplicate
Reference: ref1
Kind: quote

### Text

```text
Two
```

### Comment

```text

```

## Source Note: bad id
Kind: comment

### Text

```text
Text
```

### Comment

```text

```
"""
        notes, diagnostics = parse_source_notes_markdown(text)
        self.assertEqual(tuple(note.id for note in notes), ("duplicate",))
        self.assertGreaterEqual(len(diagnostics), 2)
        self.assertTrue(all(item.blocking for item in diagnostics))

    def test_loading_existing_sidecar_does_not_rewrite_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "paper.md.source-notes.md")
            raw = """# Calamus Source Notes v1

## Source Note: sn-1
Kind: comment
Custom Field: value

### Text

```text
A thought.
```

### Comment

```text

```
"""
            Path(path).write_text(raw, encoding="utf-8")
            before = Path(path).read_bytes()
            snapshot = MarkdownSourceNoteStore(path).load()
            self.assertEqual(Path(path).read_bytes(), before)
            self.assertEqual(snapshot.notes[0].extra_fields, (("Custom Field", "value"),))

    def test_atomic_save_and_external_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "paper.md.source-notes.md")
            store = MarkdownSourceNoteStore(path)
            initial = store.load()
            saved = store.save((self.sample(),), initial.token)
            self.assertTrue(saved.saved)
            self.assertFalse(os.path.exists(path + ".tmp"))
            Path(path).write_text(
                Path(path).read_text(encoding="utf-8") + "\nExternal\n",
                encoding="utf-8",
            )
            conflict = store.save((), saved.token)
            self.assertEqual(conflict.status, "conflict")
            forced = store.save((), conflict.token, force=True)
            self.assertTrue(forced.saved)

    def test_fenced_blocks_preserve_markdown_headings_and_backticks(self):
        note = SourceNote(
            id="sn-fence",
            kind="comment",
            text="## A heading inside the note\n```code```",
            comment="### Comment is content here",
        )
        encoded = serialize_source_notes_markdown((note,))
        notes, diagnostics = parse_source_notes_markdown(encoded)
        self.assertEqual(diagnostics, ())
        self.assertEqual(notes, (note,))

    def test_malformed_sidecar_is_loaded_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "paper.md.source-notes.md")
            Path(path).write_text("## Source Note: bad id\nKind: quote\n", encoding="utf-8")
            snapshot = MarkdownSourceNoteStore(path).load()
            self.assertFalse(snapshot.writable)
            self.assertTrue(snapshot.diagnostics)


if __name__ == "__main__":
    unittest.main()
