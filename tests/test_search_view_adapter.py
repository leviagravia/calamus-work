import unittest

from calamus_search_view import SearchViewAdapter


class FakeIter:
    def __init__(self, buffer, offset):
        self.buffer = buffer
        self.offset = offset

    def get_offset(self):
        return self.offset

    def get_line(self):
        return self.buffer.coordinates.get(self.offset, self.buffer.default_coordinates(self.offset))[0]

    def get_line_offset(self):
        return self.buffer.coordinates.get(self.offset, self.buffer.default_coordinates(self.offset))[1]


class FakeBuffer:
    def __init__(self, text="alpha beta", selection=None, cursor=0, coordinates=None):
        self.text = text
        self.selection = selection
        self.cursor = cursor
        self.coordinates = dict(coordinates or {})
        self.removed = []
        self.applied = []
        self.selected = None

    def default_coordinates(self, offset):
        prefix = self.text[:offset]
        line = prefix.count("\n")
        last_break = prefix.rfind("\n")
        column = offset if last_break < 0 else offset - last_break - 1
        return line, column

    def get_bounds(self):
        return FakeIter(self, 0), FakeIter(self, len(self.text))

    def get_text(self, start, end, include_hidden):
        return self.text[start.offset:end.offset]

    def get_has_selection(self):
        return self.selection is not None

    def get_selection_bounds(self):
        return FakeIter(self, self.selection[0]), FakeIter(self, self.selection[1])

    def get_insert(self):
        return object()

    def get_iter_at_mark(self, mark):
        return FakeIter(self, self.cursor)

    def get_iter_at_offset(self, offset):
        return FakeIter(self, offset)

    def remove_tag(self, tag, start, end):
        self.removed.append((tag, start.offset, end.offset))

    def apply_tag(self, tag, start, end):
        self.applied.append((tag, start.offset, end.offset))

    def select_range(self, start, end):
        self.selected = (start.offset, end.offset)


class FakeTextView:
    def __init__(self, buffer):
        self.buffer = buffer
        self.scrolled = None
        self.focused = False

    def get_buffer(self):
        return self.buffer

    def scroll_to_iter(self, iterator, within_margin, use_align, xalign, yalign):
        self.scrolled = (iterator.offset, within_margin, use_align, xalign, yalign)

    def grab_focus(self):
        self.focused = True


class SearchViewAdapterTests(unittest.TestCase):
    def test_requires_view_protocol_and_tag(self):
        with self.assertRaises(TypeError):
            SearchViewAdapter(object(), object())
        with self.assertRaises(TypeError):
            SearchViewAdapter(FakeTextView(FakeBuffer()), None)

    def test_reads_text_and_cursor_or_selection_boundary(self):
        buffer = FakeBuffer("alpha beta", selection=(0, 5), cursor=7)
        adapter = SearchViewAdapter(FakeTextView(buffer), "search")
        self.assertEqual(adapter.text(), "alpha beta")
        self.assertEqual(adapter.cursor_offset(), 5)
        self.assertEqual(adapter.cursor_offset(backwards=True), 0)
        buffer.selection = None
        self.assertEqual(adapter.cursor_offset(), 7)

    def test_line_column_comes_from_authoritative_text_iter(self):
        buffer = FakeBuffer(
            "alpha\nsecond alpha",
            coordinates={13: (306, 7)},
        )
        adapter = SearchViewAdapter(FakeTextView(buffer), "search")
        self.assertEqual(adapter.line_column_for_offset(13), (307, 8))

    def test_line_column_rejects_invalid_offset(self):
        adapter = SearchViewAdapter(FakeTextView(FakeBuffer()), "search")
        with self.assertRaises(TypeError):
            adapter.line_column_for_offset(True)
        with self.assertRaises(ValueError):
            adapter.line_column_for_offset(-1)

    def test_apply_highlights_clears_then_applies_spans(self):
        buffer = FakeBuffer("alpha beta alpha")
        adapter = SearchViewAdapter(FakeTextView(buffer), "search")
        self.assertEqual(adapter.apply_highlights([(0, 5), (11, 16)]), 2)
        self.assertEqual(buffer.removed, [("search", 0, 16)])
        self.assertEqual(
            buffer.applied,
            [("search", 0, 5), ("search", 11, 16)],
        )

    def test_select_span_owns_selection_scroll_and_focus(self):
        buffer = FakeBuffer("alpha beta")
        view = FakeTextView(buffer)
        adapter = SearchViewAdapter(view, "search")
        adapter.select_span(0, 5)
        self.assertEqual(buffer.selected, (0, 5))
        self.assertEqual(view.scrolled, (0, 0.15, False, 0, 0))
        self.assertTrue(view.focused)

    def test_invalid_spans_are_rejected(self):
        adapter = SearchViewAdapter(FakeTextView(FakeBuffer()), "search")
        with self.assertRaises(ValueError):
            adapter.apply_highlights([(5, 2)])
        with self.assertRaises(TypeError):
            adapter.select_span(True, 2)


if __name__ == "__main__":
    unittest.main()
