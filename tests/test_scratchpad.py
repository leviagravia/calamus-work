from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from calamus_research_file import file_token
from calamus_scratchpad import (
    ScratchpadEntry,
    new_scratchpad_id,
    normalize_heading_target,
)
from calamus_scratchpad_store import (
    MarkdownScratchpadStore,
    parse_scratchpad_markdown,
    scratchpad_path,
    serialize_scratchpad_markdown,
)


class ScratchpadModelTests(unittest.TestCase):
    def entry(self, **changes):
        values = dict(
            id="sp-20260727-001",
            type="idea",
            title="Tradizione vivente",
            status="active",
            tags=("Tradizione", "ecclesiologia", "tradizione"),
            sections=("#intro", "intro", "#chapter-one"),
            created="2026-07-27T20:00:00+02:00",
            updated="2026-07-27T20:10:00+02:00",
            body="Prima riga\n\nSeconda riga with ``` fence.",
        )
        values.update(changes)
        return ScratchpadEntry(**values)

    def test_entry_normalizes_without_losing_display_case(self):
        entry = self.entry()
        self.assertEqual(entry.type, "idea")
        self.assertEqual(entry.tags, ("Tradizione", "ecclesiologia"))
        self.assertEqual(entry.sections, ("#intro", "#chapter-one"))
        self.assertIn("tradizione", entry.search_text)

    def test_only_four_basic_types_and_required_title(self):
        for kind in ("note", "idea", "draft", "task"):
            self.assertEqual(self.entry(type=kind).type, kind)
        for forbidden in ("concept", "question", "argument"):
            with self.assertRaises(ValueError):
                self.entry(type=forbidden)
        with self.assertRaises(ValueError):
            self.entry(title="  ")

    def test_heading_target_is_explicit_and_validated(self):
        self.assertEqual(normalize_heading_target("intro"), "#intro")
        with self.assertRaises(ValueError):
            normalize_heading_target("heading with spaces")

    def test_id_is_stable_and_collision_safe(self):
        now = datetime(2026, 7, 27, 20, 30, tzinfo=timezone.utc)
        first = new_scratchpad_id((), now=now, token="abc")
        second = new_scratchpad_id((first,), now=now, token="abc")
        self.assertEqual(first, "sp-20260727-203000-abc")
        self.assertEqual(second, first + "-2")

    def test_markdown_round_trip_is_deterministic_and_fence_safe(self):
        entries = (self.entry(), self.entry(id="sp-20260727-002", type="task", title="Verificare fonte", body=""))
        text = serialize_scratchpad_markdown(entries)
        self.assertTrue(text.startswith("# Calamus Scratchpad v1\n"))
        self.assertIn("````text", text)
        parsed, diagnostics = parse_scratchpad_markdown(text)
        self.assertEqual(diagnostics, ())
        self.assertEqual(parsed, entries)
        self.assertEqual(serialize_scratchpad_markdown(parsed), text)

    def test_duplicate_id_and_malformed_body_fail_closed(self):
        duplicate = """# Calamus Scratchpad v1

## sp-1
Type: Note
Title: A
Status: Inbox
Tags:
Sections:
Created:
Updated:

### Body

```text
A
```

## sp-1
Type: Note
Title: B
Status: Inbox
Tags:
Sections:
Created:
Updated:

### Body

```text
B
```
"""
        entries, diagnostics = parse_scratchpad_markdown(duplicate)
        self.assertEqual(len(entries), 1)
        self.assertTrue(any("Duplicate Scratchpad entry id" in item.message for item in diagnostics))
        broken = duplicate.split("```\n", 1)[0]
        _entries, diagnostics = parse_scratchpad_markdown(broken)
        self.assertTrue(diagnostics)

    def test_document_sidecar_path_is_transparent(self):
        path = scratchpad_path("~/Documents/article.md")
        self.assertTrue(path.endswith("Documents/article.md.scratchpad.md"))
        self.assertIsNone(scratchpad_path(None))

    def test_store_detects_external_change_and_atomic_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "article.md.scratchpad.md"
            store = MarkdownScratchpadStore(str(path))
            initial = store.load()
            result = store.save((self.entry(),), initial.token)
            self.assertTrue(result.saved)
            self.assertTrue(path.exists())
            token = result.token
            path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            conflict = store.save((self.entry(title="Changed"),), token)
            self.assertEqual(conflict.status, "conflict")
            self.assertEqual(file_token(str(path)), conflict.token)
            self.assertFalse((Path(str(path) + ".tmp")).exists())


if __name__ == "__main__":
    unittest.main()
