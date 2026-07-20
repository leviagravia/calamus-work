import json
import os
import tempfile
import unittest

from calamus_clips import (
    clips_path,
    legacy_clips_path,
    load_clips,
    parse_clips_markdown,
    save_clips,
    serialize_clips_markdown,
)


class ClipMarkdownStoreTests(unittest.TestCase):
    def test_roundtrip_preserves_multiline_text_and_backticks(self):
        clips = [
            {
                "title": "Code and prose",
                "text": "First line\n```\n## not a record\nLast line\n",
                "created": "2026-07-20T12:00:00",
            }
        ]
        encoded = serialize_clips_markdown(clips)
        decoded = parse_clips_markdown(encoded)
        self.assertEqual(decoded, clips)
        self.assertIn("# Calamus Clip Collection v1", encoded)

    def test_save_uses_markdown_not_json(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertTrue(save_clips(td, [{"title": "A", "text": "Body", "created": ""}]))
            self.assertTrue(os.path.exists(clips_path(td)))
            self.assertFalse(os.path.exists(legacy_clips_path(td)))
            self.assertEqual(load_clips(td)[0]["text"], "Body")

    def test_legacy_json_is_migrated_but_retained_as_backup(self):
        with tempfile.TemporaryDirectory() as td:
            legacy = legacy_clips_path(td)
            with open(legacy, "w", encoding="utf-8") as handle:
                json.dump([{"title": "Legacy", "text": "Old", "created": ""}], handle)
            loaded = load_clips(td)
            self.assertEqual(loaded[0]["title"], "Legacy")
            self.assertTrue(os.path.exists(clips_path(td)))
            self.assertTrue(os.path.exists(legacy))

    def test_markdown_is_canonical_when_both_files_exist(self):
        with tempfile.TemporaryDirectory() as td:
            save_clips(td, [{"title": "Markdown", "text": "New", "created": ""}])
            with open(legacy_clips_path(td), "w", encoding="utf-8") as handle:
                json.dump([{"title": "Legacy", "text": "Old", "created": ""}], handle)
            self.assertEqual(load_clips(td)[0]["title"], "Markdown")

    def test_legacy_json_is_never_rewritten_by_migration_or_later_saves(self):
        with tempfile.TemporaryDirectory() as td:
            legacy = legacy_clips_path(td)
            original = b'[\n  {"title": "Legacy", "text": "Old", "created": ""}\n]\n'
            with open(legacy, "wb") as handle:
                handle.write(original)

            self.assertEqual(load_clips(td)[0]["title"], "Legacy")
            with open(legacy, "rb") as handle:
                self.assertEqual(handle.read(), original)

            self.assertTrue(
                save_clips(td, [{"title": "Markdown", "text": "New", "created": ""}])
            )
            with open(legacy, "rb") as handle:
                self.assertEqual(handle.read(), original)
            self.assertEqual(load_clips(td)[0]["title"], "Markdown")

    def test_existing_empty_markdown_blocks_legacy_json_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            with open(clips_path(td), "w", encoding="utf-8") as handle:
                handle.write("# Calamus Clip Collection v1\n")
            with open(legacy_clips_path(td), "w", encoding="utf-8") as handle:
                json.dump([{"title": "Legacy", "text": "Old", "created": ""}], handle)

            self.assertEqual(load_clips(td), [])

    def test_loading_existing_markdown_does_not_rewrite_user_content(self):
        with tempfile.TemporaryDirectory() as td:
            original = (
                "# Calamus Clip Collection v1\n\n"
                "## Hand edited title\n\n"
                "Created: 2026-07-20T12:00:00\n\n"
                "```text\nBody\n```\n\n"
                "<!-- user note retained -->\n"
            )
            path = clips_path(td)
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(original)

            self.assertEqual(load_clips(td)[0]["text"], "Body")
            with open(path, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), original)

    def test_malformed_markdown_fails_closed(self):
        self.assertEqual(parse_clips_markdown("# Calamus Clip Collection v1\n## Broken\nNo fence\n"), [])


if __name__ == "__main__":
    unittest.main()
