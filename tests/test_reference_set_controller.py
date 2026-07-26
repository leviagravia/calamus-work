import unittest

from calamus_reference_set_controller import ReferenceSetController
from calamus_reference_set_store import ReferenceSetSaveResult, ReferenceSetSnapshot
from calamus_reference_sets import ReferenceSet
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken


class FakeView:
    def __init__(self):
        self.widget = object()
        self.set_name = None
        self.member = None
        self.renders = []

    def render(self, sets, selected_set, records, selected_member, status):
        self.renders.append((sets, selected_set, records, selected_member, status))
        self.set_name = selected_set
        self.member = selected_member

    def selected_set_name(self):
        return self.set_name

    def selected_member_key(self):
        return self.member

    def select_set_name(self, name):
        self.set_name = name
        return name is not None

    def select_member_key(self, key):
        self.member = key
        return key is not None


class FakeStore:
    def __init__(self, sets=()):
        self.sets = tuple(sets)
        self.token = FileToken(False)
        self.saves = []
        self.next_results = []

    def load(self):
        return ReferenceSetSnapshot(self.sets, self.token, ())

    def save(self, sets, expected_token, *, force=False):
        self.saves.append((tuple(sets), expected_token, force))
        if self.next_results:
            result = self.next_results.pop(0)
            if result.saved:
                self.sets = tuple(sets)
                self.token = result.token
            return result
        self.sets = tuple(sets)
        self.token = FileToken(True, len(self.saves), len(self.sets), str(len(self.saves)))
        return ReferenceSetSaveResult("saved", self.token)


class ReferenceSetControllerTests(unittest.TestCase):
    def setUp(self):
        self.records = (
            ReferenceRecord(key="a", title="A", aliases=("old-a",)),
            ReferenceRecord(key="b", title="B"),
        )

    def make(self, store=None, choices=None):
        view = FakeView()
        errors = []
        choices = list(choices or [])
        controller = ReferenceSetController(
            store or FakeStore(),
            view,
            records_provider=lambda: self.records,
            resolve_conflict=lambda: choices.pop(0) if choices else "cancel",
            on_error=errors.append,
        )
        return controller, view, errors

    def test_load_filter_selection_and_member_projection(self):
        store = FakeStore((
            ReferenceSet("Core", members=("a", "b")),
            ReferenceSet("Background", members=("b",)),
        ))
        controller, view, _ = self.make(store)
        controller.load()
        self.assertEqual(view.set_name, "Core")
        self.assertEqual(view.member, "a")
        visible = controller.refresh("back")
        self.assertEqual(tuple(item.name for item in visible), ("Background",))
        self.assertEqual(view.set_name, "Background")

    def test_add_and_update_canonicalize_alias_members(self):
        controller, view, _ = self.make()
        controller.load()
        self.assertTrue(controller.add(ReferenceSet("Core", members=("old-a",))))
        self.assertEqual(controller.sets[0].members, ("a",))
        self.assertEqual(view.set_name, "Core")
        self.assertTrue(controller.update("Core", ReferenceSet("Primary", members=("b",))))
        self.assertEqual(controller.names, ("Primary",))

    def test_missing_member_duplicate_name_and_save_failure_are_safe(self):
        store = FakeStore((ReferenceSet("Core", members=("a",)),))
        controller, _, errors = self.make(store)
        controller.load()
        self.assertFalse(controller.add(ReferenceSet("core", members=("b",))))
        self.assertIn("already exists", errors[-1])
        with self.assertRaisesRegex(ValueError, "missing"):
            controller.add(ReferenceSet("Lost", members=("missing",)))
        store.next_results.append(ReferenceSetSaveResult("error", store.token, "disk full"))
        self.assertFalse(controller.delete("Core"))
        self.assertEqual(controller.names, ("Core",))
        self.assertEqual(errors[-1], "disk full")

    def test_conflict_reload_and_overwrite(self):
        store = FakeStore()
        controller, _, _ = self.make(store, ["overwrite"])
        controller.load()
        conflict = FileToken(True, 2, 2, "external")
        store.next_results.extend((
            ReferenceSetSaveResult("conflict", conflict),
            ReferenceSetSaveResult("saved", FileToken(True, 3, 3, "saved")),
        ))
        self.assertTrue(controller.add(ReferenceSet("Core", members=("a",))))
        self.assertTrue(store.saves[-1][2])


if __name__ == "__main__":
    unittest.main()
