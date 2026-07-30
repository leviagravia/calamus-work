import unittest

from calamus_clip_panel import ClipCollectionViewAdapter


class FakeRow:
    def __init__(self, index, clip_id):
        self._index = index
        self._calamus_clip_id = clip_id

    def get_index(self):
        return self._index


class FakeListBox:
    def __init__(self):
        self.rows = [FakeRow(0, "clip-a"), FakeRow(1, "clip-b")]
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
    def make_adapter(self, calls=None):
        listbox = FakeListBox()
        adapter = ClipCollectionViewAdapter(
            object(),
            listbox,
            double_click_type="double",
            on_activate=lambda: (calls if calls is not None else []).append("insert"),
        )
        adapter._rows_by_id = {"clip-a": listbox.rows[0], "clip-b": listbox.rows[1]}
        adapter._clips_by_id = {"clip-a": {"text": "A"}, "clip-b": {"text": "B"}}
        return listbox, adapter

    def test_selection_is_exposed_as_stable_id(self):
        _listbox, adapter = self.make_adapter()
        self.assertTrue(adapter.select_id("clip-b"))
        self.assertEqual(adapter.selected_id(), "clip-b")
        self.assertFalse(adapter.select_id("missing"))

    def test_compatibility_index_helpers_remain_bounded(self):
        _listbox, adapter = self.make_adapter()
        self.assertTrue(adapter.select_index(1))
        self.assertEqual(adapter.selected_index(), 1)
        self.assertFalse(adapter.select_index(4))

    def test_primary_double_click_selects_and_activates(self):
        calls = []
        listbox, adapter = self.make_adapter(calls)
        self.assertTrue(adapter.on_button_press(listbox, Event("double")))
        self.assertEqual(adapter.selected_id(), "clip-b")
        self.assertEqual(calls, ["insert"])

    def test_single_or_secondary_click_does_not_activate(self):
        calls = []
        listbox, adapter = self.make_adapter(calls)
        self.assertFalse(adapter.on_button_press(listbox, Event("single")))
        self.assertFalse(adapter.on_button_press(listbox, Event("double", button=3)))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
