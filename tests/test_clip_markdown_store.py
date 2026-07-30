import json
import os
import tempfile
import unittest
from unittest.mock import patch

from calamus_clips import (
    ClipConflictError,
    ClipFormatError,
    ClipLimitError,
    ClipValidationError,
    MarkdownClipStore,
    clip_revision,
    clips_path,
    legacy_clips_path,
    load_clips,
    new_clip,
    parse_clips_markdown,
    save_clips,
    serialize_clips_markdown,
)


class ClipMarkdownStoreTests(unittest.TestCase):
    def test_v2_roundtrip_preserves_ids_shortcut_unknown_fields_and_backticks(self):
        clip = new_clip("Code and prose", "First line\n```\n## not a record\nLast line\n", "code")
        clip["extra_fields"] = (("Origin", "hand written"),)
        encoded = serialize_clips_markdown([clip])
        decoded = parse_clips_markdown(encoded, strict=True)
        self.assertEqual(decoded, [clip])
        self.assertIn("# Calamus Clip Collection v2", encoded)
        self.assertIn("Shortcut: code", encoded)
        self.assertIn("Origin: hand written", encoded)
        self.assertIn("````text", encoded)

    def test_save_uses_markdown_not_json_and_compatibility_input_gets_id(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertTrue(save_clips(td, [{"title": "A", "text": "Body", "created": ""}]))
            self.assertTrue(os.path.exists(clips_path(td)))
            self.assertFalse(os.path.exists(legacy_clips_path(td)))
            loaded = load_clips(td)
            self.assertEqual(loaded[0]["text"], "Body")
            self.assertRegex(loaded[0]["id"], r"^clip-[0-9a-f]{32}$")

    def test_v1_markdown_is_migrated_to_v2_on_load(self):
        with tempfile.TemporaryDirectory() as td:
            path = clips_path(td)
            original = (
                "# Calamus Clip Collection v1\n\n"
                "## Hand edited title\n\n"
                "Created: 2026-07-20T12:00:00+02:00\n\n"
                "```text\nBody\n```\n"
            )
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(original)
            loaded = load_clips(td)
            self.assertEqual(loaded[0]["text"], "Body")
            self.assertEqual(loaded[0]["shortcut"], "")
            migrated = open(path, encoding="utf-8").read()
            self.assertIn("# Calamus Clip Collection v2", migrated)
            self.assertIn("ID: clip-", migrated)
            self.assertNotEqual(migrated, original)

    def test_existing_v2_markdown_load_is_byte_preserving(self):
        with tempfile.TemporaryDirectory() as td:
            clip = new_clip("A", "Body", "a")
            original = serialize_clips_markdown([clip])
            path = clips_path(td)
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(original)
            self.assertEqual(load_clips(td)[0]["id"], clip["id"])
            self.assertEqual(open(path, encoding="utf-8").read(), original)

    def test_legacy_json_is_migrated_and_retained_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as td:
            legacy = legacy_clips_path(td)
            original = b'[\n  {"title": "Legacy", "text": "Old", "created": ""}\n]\n'
            with open(legacy, "wb") as handle:
                handle.write(original)
            loaded = load_clips(td)
            self.assertEqual(loaded[0]["title"], "Legacy")
            self.assertTrue(os.path.exists(clips_path(td)))
            self.assertEqual(open(legacy, "rb").read(), original)
            self.assertTrue(save_clips(td, [new_clip("Markdown", "New", "new")]))
            self.assertEqual(open(legacy, "rb").read(), original)

    def test_markdown_is_canonical_when_both_files_exist(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertTrue(save_clips(td, [new_clip("Markdown", "New", "md")]))
            with open(legacy_clips_path(td), "w", encoding="utf-8") as handle:
                json.dump([{"title": "Legacy", "text": "Old"}], handle)
            self.assertEqual(load_clips(td)[0]["title"], "Markdown")

    def test_malformed_markdown_fails_closed_and_strict_mode_explains(self):
        malformed = "# Calamus Clip Collection v2\n\n## Broken\n\nID: clip-" + "a" * 32 + "\n"
        self.assertEqual(parse_clips_markdown(malformed), [])
        with self.assertRaises(ClipFormatError):
            parse_clips_markdown(malformed, strict=True)

    def test_duplicate_id_and_shortcut_are_rejected(self):
        first = new_clip("A", "One", "same")
        second = new_clip("B", "Two", "other")
        second["id"] = first["id"]
        with self.assertRaises(ClipValidationError):
            serialize_clips_markdown([first, second])
        second = new_clip("B", "Two", "same")
        with self.assertRaises(ClipValidationError):
            serialize_clips_markdown([first, second])

    def test_limit_is_explicit_and_never_truncates(self):
        with tempfile.TemporaryDirectory() as td:
            store = MarkdownClipStore(td)
            clips = [new_clip(str(i), f"Body {i}") for i in range(3)]
            with self.assertRaises(ClipLimitError):
                store.save_snapshot(clips, expected_revision="missing", limit=2)
            self.assertFalse(os.path.exists(clips_path(td)))

    def test_stale_revision_blocks_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            store = MarkdownClipStore(td)
            first = store.save_snapshot([new_clip("A", "One")], expected_revision="missing")
            with open(store.path, "a", encoding="utf-8") as handle:
                handle.write("\n<!-- external -->\n")
            with self.assertRaises(ClipConflictError):
                store.save_snapshot([new_clip("B", "Two")], expected_revision=first.revision)
            self.assertIn("external", open(store.path, encoding="utf-8").read())

    def test_replace_failure_keeps_previous_authority(self):
        with tempfile.TemporaryDirectory() as td:
            store = MarkdownClipStore(td)
            snap = store.save_snapshot([new_clip("A", "One")], expected_revision="missing")
            original = open(store.path, "rb").read()
            with patch("calamus_clips.os.replace", side_effect=OSError("blocked")):
                with self.assertRaises(Exception):
                    store.save_snapshot([new_clip("B", "Two")], expected_revision=snap.revision)
            self.assertEqual(open(store.path, "rb").read(), original)
            leftovers = [name for name in os.listdir(td) if name.startswith(".clips-")]
            self.assertEqual(leftovers, [])

    def test_revision_token_covers_missing_and_raw_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = clips_path(td)
            self.assertEqual(clip_revision(path), "missing")
            with open(path, "wb") as handle:
                handle.write(b"abc")
            self.assertTrue(clip_revision(path).startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
