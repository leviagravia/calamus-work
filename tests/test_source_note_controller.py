import unittest

from calamus_research_file import FileToken
from calamus_source_note_controller import SourceNoteController
from calamus_source_note_store import SourceNoteSaveResult, SourceNoteSnapshot
from calamus_source_notes import SourceLocator, SourceNote


class FakeView:
    widget = object()

    def __init__(self):
        self.available = None
        self.message = ""
        self.reference_options = ()
        self.reference_selected = "all"
        self.rendered = ()
        self.selected = None
        self.status = ""
        self.missing = frozenset()

    def set_available(self, available, message):
        self.available = available
        self.message = message

    def set_reference_options(self, keys, selected):
        self.reference_options = tuple(keys)
        self.reference_selected = selected

    def render(self, notes, selected_id, status, missing_reference_ids):
        self.rendered = tuple(notes)
        self.selected = selected_id
        self.status = status
        self.missing = missing_reference_ids

    def selected_id(self):
        return self.selected

    def select_id(self, note_id):
        self.selected = note_id
        return note_id is not None


class FakeStore:
    def __init__(self, path, initial=()):
        self.path = path
        self.notes = tuple(initial)
        self.token = FileToken(False)
        self.saves = []
        self.next_results = []

    def load(self):
        return SourceNoteSnapshot(self.notes, self.token, ())

    def save(self, notes, expected_token, *, force=False):
        self.saves.append((tuple(notes), expected_token, force))
        if self.next_results:
            return self.next_results.pop(0)
        self.notes = tuple(notes)
        self.token = FileToken(True, len(self.saves), len(self.notes), str(len(self.saves)))
        return SourceNoteSaveResult("saved", self.token)


class SourceNoteControllerTests(unittest.TestCase):
    def note(self, note_id="sn-1", kind="quote", reference="ref1", text="Text", tags=(), page="42"):
        return SourceNote(
            id=note_id,
            kind=kind,
            reference_key=reference,
            locator=SourceLocator(page=page),
            text=text,
            tags=tags,
        )

    def build(self, keys=("ref1",), stores=None, choices=None, errors=None):
        view = FakeView()
        store_map = stores if stores is not None else {}
        choices = choices if choices is not None else []
        errors = errors if errors is not None else []

        def factory(path):
            return store_map.setdefault(path, FakeStore(path))

        controller = SourceNoteController(
            view,
            reference_keys_provider=lambda: tuple(keys),
            resolve_conflict=lambda: choices.pop(0) if choices else "cancel",
            on_error=errors.append,
            store_factory=factory,
        )
        return controller, view, store_map, errors

    def test_unsaved_document_is_unavailable_and_does_not_create_sidecar(self):
        controller, view, stores, errors = self.build()
        self.assertFalse(controller.bind_document(None))
        self.assertFalse(controller.available)
        self.assertFalse(view.available)
        self.assertEqual(stores, {})
        self.assertFalse(controller.add(self.note()))
        self.assertIn("Save the document", errors[-1])

    def test_bind_document_loads_exact_sidecar_and_rebinds(self):
        controller, view, stores, _ = self.build()
        self.assertTrue(controller.bind_document("/work/one.md"))
        self.assertEqual(controller.sidecar_path, "/work/one.md.source-notes.md")
        stores[controller.sidecar_path].notes = (self.note(),)
        controller.bind_document("/work/one.md", force=True)
        self.assertEqual(controller.notes, (self.note(),))
        controller.bind_document("/work/two.md")
        self.assertEqual(controller.sidecar_path, "/work/two.md.source-notes.md")
        self.assertEqual(controller.notes, ())
        self.assertTrue(view.available)

    def test_filters_cover_reference_kind_tags_locator_and_text(self):
        controller, view, stores, _ = self.build(keys=("ref1", "ref2"))
        path = "/work/paper.md.source-notes.md"
        stores[path] = FakeStore(path, (
            self.note("sn-1", "quote", "ref1", "Faith response", ("revelation",)),
            self.note("sn-2", "paraphrase", "ref2", "Communion", ("church",), "55"),
            SourceNote(
                id="sn-3",
                kind="comment",
                text="Independent thought",
                locator=SourceLocator(section="Conclusion"),
            ),
        ))
        controller.bind_document("/work/paper.md")
        self.assertEqual(tuple(n.id for n in controller.filtered_notes("revelation")), ("sn-1",))
        self.assertEqual(tuple(n.id for n in controller.filtered_notes("42")), ("sn-1",))
        self.assertEqual(tuple(n.id for n in controller.filtered_notes("", "paraphrase")), ("sn-2",))
        self.assertEqual(tuple(n.id for n in controller.filtered_notes("", "all", "ref2")), ("sn-2",))
        controller.refresh(query="conclusion")
        self.assertEqual(tuple(n.id for n in view.rendered), ("sn-3",))

    def test_missing_reference_links_are_reported_but_not_blocking(self):
        controller, view, stores, _ = self.build(keys=("ref1",))
        path = "/work/paper.md.source-notes.md"
        stores[path] = FakeStore(path, (self.note(reference="missing"),))
        controller.bind_document("/work/paper.md")
        self.assertEqual(view.missing, frozenset({"sn-1"}))
        self.assertIn("missing reference", view.status)
        self.assertTrue(controller.add(SourceNote(id="sn-2", kind="comment", text="Idea")))

    def test_new_missing_reference_is_rejected_before_save(self):
        controller, view, stores, errors = self.build(keys=("ref1",))
        controller.bind_document("/work/paper.md")
        missing = self.note(reference="missing")
        self.assertFalse(controller.add(missing))
        self.assertEqual(stores[controller.sidecar_path].saves, [])
        self.assertIn("Reference key is missing", errors[-1])

    def test_add_update_delete_are_persist_first(self):
        controller, view, stores, _ = self.build()
        controller.bind_document("/work/paper.md")
        store = stores[controller.sidecar_path]
        note = self.note()
        self.assertTrue(controller.add(note))
        self.assertEqual(controller.notes, (note,))
        self.assertEqual(store.saves[0][0], (note,))
        updated = note.revised(modified="2026-07-21T16:00:00+02:00", text="Updated")
        self.assertTrue(controller.update(note.id, updated))
        self.assertEqual(controller.notes, (updated,))
        self.assertTrue(controller.delete(updated.id))
        self.assertEqual(controller.notes, ())

    def test_save_failure_keeps_runtime_unchanged(self):
        controller, view, stores, errors = self.build()
        controller.bind_document("/work/paper.md")
        store = stores[controller.sidecar_path]
        store.next_results.append(SourceNoteSaveResult("error", store.token, "disk full"))
        self.assertFalse(controller.add(self.note()))
        self.assertEqual(controller.notes, ())
        self.assertEqual(errors[-1], "disk full")

    def test_conflict_reload_and_overwrite_paths(self):
        choices = ["reload", "overwrite"]
        controller, view, stores, _ = self.build(choices=choices)
        controller.bind_document("/work/paper.md")
        store = stores[controller.sidecar_path]
        conflict = FileToken(True, 1, 1, "external")
        store.next_results.append(SourceNoteSaveResult("conflict", conflict))
        self.assertFalse(controller.add(self.note()))
        self.assertEqual(controller.notes, ())

        store.next_results.extend([
            SourceNoteSaveResult("conflict", conflict),
            SourceNoteSaveResult("saved", FileToken(True, 2, 2, "saved")),
        ])
        self.assertTrue(controller.add(self.note()))
        self.assertTrue(store.saves[-1][2])


if __name__ == "__main__":
    unittest.main()
