import unittest

from calamus_navigation_view import NavigationViewAdapter


class FakeIter:
    def __init__(self, offset):
        self.offset = offset

    def get_offset(self):
        return self.offset


class FakeBuffer:
    def __init__(self, text="abc", cursor=0):
        self.text_value = text
        self.cursor = cursor
        self.placed = None

    def get_bounds(self):
        return FakeIter(0), FakeIter(len(self.text_value))

    def get_text(self, start, end, include_hidden):
        return self.text_value[start.offset:end.offset]

    def get_line_count(self):
        return max(1, self.text_value.count("\n") + 1)

    def get_insert(self):
        return object()

    def get_iter_at_mark(self, _mark):
        return FakeIter(self.cursor)

    def get_iter_at_offset(self, offset):
        return FakeIter(min(offset, len(self.text_value)))

    def get_iter_at_line_offset(self, line_index, line_offset):
        starts = [0]
        for index, character in enumerate(self.text_value):
            if character == "\n":
                starts.append(index + 1)
        return FakeIter(starts[min(line_index, len(starts) - 1)] + line_offset)

    def place_cursor(self, iterator):
        self.placed = iterator.offset
        self.cursor = iterator.offset


class FakeView:
    def __init__(self, text="abc", cursor=0):
        self.buffer = FakeBuffer(text, cursor)
        self.scrolled = None
        self.focused = False

    def get_buffer(self):
        return self.buffer

    def scroll_to_iter(self, iterator, within_margin, use_align, xalign, yalign):
        self.scrolled = (iterator.offset, within_margin, use_align, xalign, yalign)

    def grab_focus(self):
        self.focused = True


class NavigationViewAdapterTests(unittest.TestCase):
    def test_requires_view_protocol(self):
        with self.assertRaises(TypeError):
            NavigationViewAdapter(object())

    def test_reads_text_and_cursor(self):
        adapter = NavigationViewAdapter(FakeView("hello", 3))
        self.assertEqual(adapter.text(), "hello")
        self.assertEqual(adapter.cursor_offset(), 3)

    def test_navigate_places_cursor_scrolls_and_focuses(self):
        view = FakeView("hello", 0)
        adapter = NavigationViewAdapter(view)
        adapter.navigate_offset(4)
        self.assertEqual(view.buffer.placed, 4)
        self.assertEqual(view.scrolled, (4, 0.15, False, 0, 0))
        self.assertTrue(view.focused)

    def test_line_count_and_line_navigation_use_text_buffer(self):
        view = FakeView("one\ntwo\nthree", 0)
        adapter = NavigationViewAdapter(view)
        self.assertEqual(adapter.line_count(), 3)
        adapter.navigate_line(1)
        self.assertEqual(view.buffer.placed, 4)
        self.assertTrue(view.focused)

    def test_navigate_rejects_invalid_offsets(self):
        adapter = NavigationViewAdapter(FakeView())
        with self.assertRaises(TypeError):
            adapter.navigate_offset(True)
        with self.assertRaises(ValueError):
            adapter.navigate_offset(-1)
        with self.assertRaises(TypeError):
            adapter.navigate_line(False)
        with self.assertRaises(ValueError):
            adapter.navigate_line(-1)


if __name__ == "__main__":
    unittest.main()
