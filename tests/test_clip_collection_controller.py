import tempfile
import unittest

from calamus_clip_collection import ClipCollectionController
from calamus_clips import MarkdownClipStore, new_clip


class FakeView:
    def __init__(self):
        self.widget = object()
        self.rows = []
        self.selected = None
        self.focus_calls = 0
        self.total = 0
        self.query = ""

    def render(self, clips, *, total, query):
        self.rows = [dict(item) for item in clips]
        self.total = total
        self.query = query
        if self.selected and not any(row["id"] == self.selected for row in self.rows):
            self.selected = None

    def selected_id(self):
        return self.selected

    def select_id(self, clip_id):
        if not any(row["id"] == clip_id for row in self.rows):
            return False
        self.selected = clip_id
        return True

    def focus_search(self):
        self.focus_calls += 1


class ClipCollectionControllerTests(unittest.TestCase):
    def make_controller(self, initial=()):
        td = tempfile.TemporaryDirectory()
        store = MarkdownClipStore(td.name)
        if initial:
            store.save_snapshot(list(initial), expected_revision="missing")
        view = FakeView()
        controller = ClipCollectionController(store, view)
        self.assertTrue(controller.load())
        self.addCleanup(td.cleanup)
        return store, view, controller

    def test_load_renders_search_order_and_selects_first_by_id(self):
        alpha = new_clip("Alpha", "Body A", "zeta")
        beta = new_clip("Beta", "Body B", "beta")
        no_shortcut = new_clip("A title", "Body C")
        _store, view, controller = self.make_controller([alpha, no_shortcut, beta])
        self.assertEqual([row["shortcut"] for row in view.rows], ["beta", "zeta", ""])
        self.assertEqual(view.selected, beta["id"])
        self.assertEqual(view.total, 3)
        self.assertEqual(len(controller.clips), 3)

    def test_search_ranking_and_exact_shortcut_priority(self):
        exact = new_clip("Unrelated", "Other", "intro")
        title = new_clip("Introductory paragraph", "Body")
        body = new_clip("Third", "Contains intro in body")
        _store, view, controller = self.make_controller([body, title, exact])
        controller.set_query("intro")
        self.assertEqual([row["id"] for row in view.rows], [exact["id"], title["id"], body["id"]])
        self.assertEqual(view.query, "intro")

    def test_create_is_persist_first_and_selects_new_stable_id(self):
        store, view, controller = self.make_controller([new_clip("Old", "Body")])
        self.assertTrue(controller.create("New", "New text", "new"))
        selected = controller.selected_clip()
        self.assertEqual(selected["shortcut"], "new")
        self.assertEqual(store.load_snapshot().clips[0]["id"], selected["id"])
        self.assertEqual(view.selected, selected["id"])

    def test_shortcut_collision_fails_without_runtime_commit(self):
        _store, view, controller = self.make_controller([new_clip("Old", "Body", "same")])
        before = controller.clips
        self.assertFalse(controller.create("New", "New text", "SAME"))
        self.assertIn("already used", controller.last_error)
        self.assertEqual(controller.clips, before)
        self.assertEqual(len(view.rows), 1)

    def test_edit_preserves_id_and_created_but_changes_content(self):
        item = new_clip("Old", "Body", "old")
        _store, view, controller = self.make_controller([item])
        view.select_id(item["id"])
        self.assertTrue(controller.update_selected("Edited", "Changed", "edited"))
        changed = controller.selected_clip()
        self.assertEqual(changed["id"], item["id"])
        self.assertEqual(changed["created"], item["created"])
        self.assertEqual(changed["title"], "Edited")
        self.assertEqual(changed["shortcut"], "edited")

    def test_duplicate_gets_new_id_and_empty_shortcut(self):
        item = new_clip("Original", "Body", "original")
        _store, view, controller = self.make_controller([item])
        view.select_id(item["id"])
        self.assertTrue(controller.duplicate_selected())
        duplicated = controller.selected_clip()
        self.assertNotEqual(duplicated["id"], item["id"])
        self.assertEqual(duplicated["shortcut"], "")
        self.assertEqual(duplicated["text"], item["text"])

    def test_delete_reselects_neighbor_by_id(self):
        a = new_clip("A", "One", "a")
        b = new_clip("B", "Two", "b")
        _store, view, controller = self.make_controller([a, b])
        view.select_id(a["id"])
        self.assertTrue(controller.delete_selected())
        self.assertEqual(controller.selected_id(), b["id"])
        self.assertEqual(len(controller.clips), 1)

    def test_delete_without_selection_is_noop(self):
        _store, view, controller = self.make_controller([])
        view.selected = None
        self.assertIsNone(controller.delete_selected())

    def test_numeric_slot_uses_canonical_order_not_search_order(self):
        first = new_clip("Z", "First", "z")
        second = new_clip("A", "Second", "a")
        _store, _view, controller = self.make_controller([first, second])
        controller.set_query("first")
        self.assertTrue(controller.select_number(2))
        self.assertEqual(controller.selected_id(), second["id"])
        self.assertEqual(controller.query, "")
        self.assertEqual(controller.selected_text(), "Second")

    def test_refresh_reloads_external_change_and_preserves_id(self):
        item = new_clip("A", "One", "a")
        store, view, controller = self.make_controller([item])
        view.select_id(item["id"])
        external = dict(item)
        external["title"] = "Externally edited"
        external["updated"] = "2026-07-29T21:00:00+02:00"
        store.save_snapshot([external], expected_revision=controller.revision)
        self.assertTrue(controller.refresh())
        self.assertEqual(controller.selected_id(), item["id"])
        self.assertEqual(controller.selected_clip()["title"], "Externally edited")

    def test_activate_clears_query_and_focuses_search(self):
        _store, view, controller = self.make_controller([new_clip("A", "Body")])
        controller.set_query("body")
        controller.activate()
        self.assertEqual(controller.query, "")
        self.assertEqual(view.focus_calls, 1)


if __name__ == "__main__":
    unittest.main()
