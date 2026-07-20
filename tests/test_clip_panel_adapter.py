import unittest

from calamus_clip_panel import ClipCollectionViewAdapter


class FakeRow:
    def __init__(self, index):
        self._index = index

    def get_index(self):
        return self._index


class FakeListBox:
    def __init__(self):
        self.rows = [FakeRow(0), FakeRow(1)]
        self.selected = None

    def get_selected_row(self):
        return self.selected

    def get_row_at_index(self, index):
        return self.rows[index] if 0 <= index < len(self.rows) else None

    def select_row(self, row):
        self.selected = row

    def get_row_at_y(self, y):
        return self.rows[1] if y == 8 else None


class Event:
    def __init__(self, event_type, button=1, y=8):
        self.type = event_type
        self.button = button
        self.y = y


class ClipPanelAdapterTests(unittest.TestCase):
    def test_selection_is_view_owned(self):
        listbox = FakeListBox()
        adapter = ClipCollectionViewAdapter(object(), listbox, double_click_type="double", on_activate=lambda: None)
        self.assertTrue(adapter.select_index(1))
        self.assertEqual(adapter.selected_index(), 1)
        self.assertFalse(adapter.select_index(4))

    def test_primary_double_click_selects_and_activates(self):
        listbox = FakeListBox()
        calls = []
        adapter = ClipCollectionViewAdapter(object(), listbox, double_click_type="double", on_activate=lambda: calls.append("insert"))
        self.assertTrue(adapter.on_button_press(listbox, Event("double")))
        self.assertEqual(adapter.selected_index(), 1)
        self.assertEqual(calls, ["insert"])

    def test_enter_or_single_click_cannot_activate(self):
        listbox = FakeListBox()
        calls = []
        adapter = ClipCollectionViewAdapter(object(), listbox, double_click_type="double", on_activate=lambda: calls.append("insert"))
        self.assertFalse(adapter.on_button_press(listbox, Event("single")))
        self.assertFalse(adapter.on_button_press(listbox, Event("double", button=3)))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
