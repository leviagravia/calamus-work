import unittest

from calamus_clip_expansion import expand_clip_text
from calamus_clip_search import clip_preview, duplicate_body_ids, search_clips
from calamus_clips import ClipValidationError, new_clip


class ClipSearchAndExpansionTests(unittest.TestCase):
    def test_empty_query_lists_shortcuts_then_title(self):
        clips = [
            new_clip("Zulu", "Z"),
            new_clip("Beta", "B", "beta"),
            new_clip("Alpha", "A", "alpha"),
        ]
        self.assertEqual([item["shortcut"] for item in search_clips(clips, "")], ["alpha", "beta", ""])

    def test_body_search_is_last_rank(self):
        exact = new_clip("X", "none", "term")
        title = new_clip("Term title", "none")
        body = new_clip("Y", "contains term")
        self.assertEqual([item["id"] for item in search_clips([body, title, exact], "term")], [exact["id"], title["id"], body["id"]])

    def test_preview_uses_first_nonempty_line_and_ellipsis(self):
        self.assertEqual(clip_preview("\n  First   line \nSecond", 8), "First li…")

    def test_duplicate_body_ids_excludes_current(self):
        a = new_clip("A", "Same")
        b = new_clip("B", "Same")
        self.assertEqual(duplicate_body_ids([a, b], "Same", exclude_id=a["id"]), (b["id"],))

    def test_cursor_marker_is_removed_and_offset_preserved(self):
        result = expand_clip_text("Hello {{cursor}}world")
        self.assertEqual(result.text, "Hello world")
        self.assertEqual(result.cursor_offset, 6)

    def test_no_cursor_marker_places_caret_at_end(self):
        result = expand_clip_text("Hello")
        self.assertEqual(result.cursor_offset, 5)

    def test_multiple_cursor_markers_fail_closed(self):
        with self.assertRaises(ClipValidationError):
            expand_clip_text("{{cursor}}x{{cursor}}")


if __name__ == "__main__":
    unittest.main()
