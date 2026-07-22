import unittest

from calamus_reference_controller import ReferenceController
from calamus_reference_store import (
    FileToken,
    ReferenceLibrarySnapshot,
    ReferenceSaveResult,
)
from calamus_references import ReferenceRecord


class FakeView:
    def __init__(self):
        self.widget = object()
        self.selected = None
        self.renders = []

    def render(self, records, selected_key, status):
        self.renders.append((records, selected_key, status))
        self.selected = selected_key

    def selected_key(self):
        return self.selected

    def select_key(self, key):
        self.selected = key
        return key is not None


class FakeStore:
    def __init__(self, records=()):
        self.token = FileToken(False)
        self.records = tuple(records)
        self.saves = []
        self.next_results = []
        self.loads = 0

    def load(self):
        self.loads += 1
        return ReferenceLibrarySnapshot(self.records, self.token, ())

    def save(self, records, expected_token, *, force=False):
        self.saves.append((tuple(records), expected_token, force))
        if self.next_results:
            result = self.next_results.pop(0)
            if result.saved:
                self.records = tuple(records)
                self.token = result.token
            return result
        self.records = tuple(records)
        self.token = FileToken(True, len(self.saves), len(records), str(len(self.saves)))
        return ReferenceSaveResult("saved", self.token)


class ReferenceControllerTests(unittest.TestCase):
    def record(self, key="key2020", title="Title"):
        return ReferenceRecord(key=key, title=title, authors=("Author, A",), year="2020")

    def make(self, store=None, choices=None):
        view = FakeView()
        errors = []
        choices = list(choices or [])
        controller = ReferenceController(
            store or FakeStore(),
            view,
            resolve_conflict=lambda: choices.pop(0) if choices else "cancel",
            on_error=errors.append,
        )
        return controller, view, errors

    def test_load_search_and_selection_use_one_controller(self):
        store = FakeStore((self.record("alpha2020", "Alpha"), self.record("beta2021", "Beta")))
        controller, view, _ = self.make(store)
        controller.load()
        self.assertTrue(controller.loaded)
        self.assertEqual(view.selected, "alpha2020")
        visible = controller.refresh("beta")
        self.assertEqual(tuple(item.key for item in visible), ("beta2021",))
        self.assertEqual(view.selected, "beta2021")

    def test_select_key_clears_filter_and_selects_existing_record(self):
        store = FakeStore((self.record("alpha2020", "Alpha"), self.record("beta2021", "Beta")))
        controller, view, _ = self.make(store)
        controller.load()
        controller.refresh("beta")
        self.assertTrue(controller.select_key("alpha2020"))
        self.assertEqual(view.selected, "alpha2020")
        self.assertFalse(controller.select_key("missing"))

    def test_add_is_persist_first_and_failure_keeps_runtime_unchanged(self):
        store = FakeStore((self.record(),))
        controller, _, errors = self.make(store)
        controller.load()
        store.next_results.append(ReferenceSaveResult("error", store.token, "disk full"))
        self.assertFalse(controller.add(self.record("new2021", "New")))
        self.assertEqual(controller.keys, ("key2020",))
        self.assertEqual(errors, ["disk full"])

    def test_add_update_delete_commit_after_save(self):
        controller, view, _ = self.make(FakeStore())
        controller.load()
        self.assertTrue(controller.add(self.record()))
        self.assertEqual(controller.keys, ("key2020",))
        changed = self.record("renamed2020", "Changed")
        self.assertTrue(controller.update("key2020", changed))
        self.assertEqual(controller.keys, ("renamed2020",))
        self.assertEqual(view.selected, "renamed2020")
        self.assertTrue(controller.delete("renamed2020"))
        self.assertEqual(controller.keys, ())

    def test_duplicate_key_is_rejected_without_save(self):
        store = FakeStore((self.record("a2020", "A"), self.record("b2020", "B")))
        controller, _, errors = self.make(store)
        controller.load()
        saves_before = len(store.saves)
        self.assertFalse(controller.update("a2020", self.record("b2020", "Changed")))
        self.assertEqual(len(store.saves), saves_before)
        self.assertIn("already exists", errors[-1])

    def test_conflict_reload_discards_candidate_and_reloads(self):
        store = FakeStore((self.record(),))
        controller, _, _ = self.make(store, ["reload"])
        controller.load()
        external = self.record("external2022", "External")
        store.records = (external,)
        conflict_token = FileToken(True, 4, 4, "external")
        store.token = conflict_token
        store.next_results.append(ReferenceSaveResult("conflict", conflict_token))
        self.assertFalse(controller.add(self.record("new2021", "New")))
        self.assertEqual(controller.keys, ("external2022",))
        self.assertEqual(store.loads, 2)

    def test_conflict_overwrite_retries_with_force(self):
        store = FakeStore()
        controller, _, _ = self.make(store, ["overwrite"])
        controller.load()
        conflict_token = FileToken(True, 5, 5, "changed")
        store.next_results.extend([
            ReferenceSaveResult("conflict", conflict_token),
            ReferenceSaveResult("saved", FileToken(True, 6, 6, "saved")),
        ])
        self.assertTrue(controller.add(self.record()))
        self.assertTrue(store.saves[-1][2])


if __name__ == "__main__":
    unittest.main()
