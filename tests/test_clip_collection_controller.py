import unittest

from calamus_clip_collection import ClipCollectionController


class FakeStore:
    def __init__(self, clips=None):
        self.clips = list(clips or [])
        self.save_ok = True
        self.saved = []

    def load_clips(self, limit=200):
        return list(self.clips[:limit])

    def save_clips(self, clips, limit=200):
        self.saved.append(list(clips[:limit]))
        if not self.save_ok:
            return False
        self.clips = list(clips[:limit])
        return True


class FakeView:
    def __init__(self):
        self.widget = object()
        self.rows = []
        self.selected = None

    def render(self, clips):
        self.rows = [dict(item) for item in clips]
        if self.selected is not None and self.selected >= len(self.rows):
            self.selected = None

    def selected_index(self):
        return self.selected

    def select_index(self, index):
        if index < 0 or index >= len(self.rows):
            return False
        self.selected = index
        return True


class ClipCollectionControllerTests(unittest.TestCase):
    def test_load_normalizes_and_renders(self):
        store = FakeStore([{"text": "Hello", "title": 3}, {"bad": True}])
        view = FakeView()
        controller = ClipCollectionController(store, view)
        controller.load()
        self.assertEqual(len(controller.clips), 1)
        self.assertEqual(view.rows[0]["title"], "Hello")

    def test_add_is_persist_first_and_selects_new_clip(self):
        store = FakeStore([{"title": "Old", "text": "Body", "created": ""}])
        view = FakeView()
        controller = ClipCollectionController(store, view)
        controller.load()
        self.assertTrue(controller.add_text("New text"))
        self.assertEqual(store.saved[-1][0]["text"], "New text")
        self.assertEqual(view.rows[0]["text"], "New text")
        self.assertEqual(view.selected, 0)

    def test_add_failure_does_not_commit_runtime_or_view(self):
        store = FakeStore([{"title": "Old", "text": "Body", "created": ""}])
        view = FakeView()
        controller = ClipCollectionController(store, view)
        controller.load()
        before = controller.clips
        store.save_ok = False
        self.assertFalse(controller.add_text("New"))
        self.assertEqual(controller.clips, before)
        self.assertEqual(view.rows[0]["title"], "Old")

    def test_delete_is_persist_first_and_reselects_neighbor(self):
        store = FakeStore([
            {"title": "A", "text": "One", "created": ""},
            {"title": "B", "text": "Two", "created": ""},
        ])
        view = FakeView()
        controller = ClipCollectionController(store, view)
        controller.load()
        view.select_index(0)
        self.assertTrue(controller.delete_selected())
        self.assertEqual([row["title"] for row in view.rows], ["B"])
        self.assertEqual(view.selected, 0)

    def test_delete_without_selection_is_noop(self):
        controller = ClipCollectionController(FakeStore(), FakeView())
        controller.load()
        self.assertIsNone(controller.delete_selected())

    def test_select_number_uses_one_based_shortcut_and_selected_text(self):
        store = FakeStore([
            {"title": "A", "text": "One", "created": ""},
            {"title": "B", "text": "Two", "created": ""},
        ])
        view = FakeView()
        controller = ClipCollectionController(store, view)
        controller.load()
        self.assertTrue(controller.select_number(2))
        self.assertEqual(controller.selected_index(), 1)
        self.assertEqual(controller.selected_text(), "Two")
        self.assertFalse(controller.select_number(3))


if __name__ == "__main__":
    unittest.main()
