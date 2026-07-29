import unittest

from calamus_reference_store import ReferenceLibrarySnapshot, ReferenceSaveResult
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken
from calamus_scratchpad import ScratchpadEntry
from calamus_scratchpad_store import ScratchpadSaveResult, ScratchpadSnapshot
from calamus_source_note_store import SourceNoteSaveResult, SourceNoteSnapshot
from calamus_source_notes import SourceNote
from calamus_tag_integrity_controller import TagIntegrityController
from calamus_tags_controller import TAG_SORT_USAGE, TagsController


class FakeView:
    widget = object()

    def __init__(self):
        self.items = ()
        self.uses = ()
        self.tag_identity = None
        self.use = None
        self.status = ""
        self.query = ""
        self.scope = "all"
        self.issues = False
        self.sort = "name"

    def render_tags(self, items, selected_identity, status):
        self.items = tuple(items)
        self.tag_identity = selected_identity
        self.status = status

    def render_uses(self, uses, selected_index, status):
        self.uses = tuple(uses)
        self.use = self.uses[selected_index] if selected_index is not None and self.uses else None

    def selected_tag_identity(self):
        return self.tag_identity

    def selected_use(self):
        return self.use

    def set_query(self, value):
        self.query = value

    def set_scope(self, value):
        self.scope = value

    def set_issues_only(self, active):
        self.issues = bool(active)

    def set_sort(self, value):
        self.sort = value


class _ReferenceStore:
    def __init__(self, records):
        self.records = tuple(records)
        self.token = FileToken(True, 1, 1, "refs")

    def load(self):
        return ReferenceLibrarySnapshot(self.records, self.token, ())

    def save(self, records, expected_token, *, force=False):
        self.records = tuple(records)
        self.token = FileToken(True, 2, 2, "refs2")
        return ReferenceSaveResult("saved", self.token)


class _NoteStore:
    path = "/work/paper.md.source-notes.md"

    def __init__(self, notes):
        self.notes = tuple(notes)
        self.token = FileToken(True, 1, 1, "notes")

    def load(self):
        return SourceNoteSnapshot(self.notes, self.token, ())

    def save(self, notes, expected_token, *, force=False):
        self.notes = tuple(notes)
        self.token = FileToken(True, 2, 2, "notes2")
        return SourceNoteSaveResult("saved", self.token)


class _ScratchStore:
    path = "/work/paper.md.scratchpad.md"

    def __init__(self, entries):
        self.entries = tuple(entries)
        self.token = FileToken(True, 1, 1, "scratch")

    def load(self):
        return ScratchpadSnapshot(self.entries, self.token, ())

    def save(self, entries, expected_token, *, force=False):
        self.entries = tuple(entries)
        self.token = FileToken(True, 2, 2, "scratch2")
        return ScratchpadSaveResult("saved", self.token)


class W94TagsControllerTests(unittest.TestCase):
    def setUp(self):
        refs = _ReferenceStore((
            ReferenceRecord(key="r1", title="Faith book", tags=("Faith",)),
            ReferenceRecord(key="r2", title="Method book", tags=("method",)),
        ))
        notes = _NoteStore((
            SourceNote(id="sn-1", kind="comment", text="A note", tags=("faith",)),
        ))
        scratch = _ScratchStore((
            ScratchpadEntry(
                id="sp-1", type="idea", title="Draft idea", body="Body", tags=("drafting",)
            ),
        ))
        integrity = TagIntegrityController(
            reference_store=refs,
            source_note_store_factory=lambda _path: notes,
            scratchpad_store_factory=lambda _path: scratch,
            document_path_provider=lambda: "/work/paper.md",
            refresh_references=lambda: None,
            refresh_source_notes=lambda: None,
            refresh_scratchpad=lambda: None,
        )
        self.view = FakeView()
        self.opened = []
        self.errors = []
        self.controller = TagsController(
            self.view,
            integrity,
            show_reference=lambda value: self.opened.append(("reference", value)) or True,
            show_source_note=lambda value: self.opened.append(("source-note", value)) or True,
            show_scratchpad_entry=lambda value: self.opened.append(("scratchpad", value)) or True,
            on_error=self.errors.append,
        )

    def test_activate_projects_all_authorities_without_owning_gtk_focus(self):
        self.assertFalse(hasattr(self.view, "focus_search"))
        self.assertTrue(self.controller.activate())
        self.assertEqual(tuple(item.canonical for item in self.view.items), ("drafting", "Faith", "method"))
        faith = next(item for item in self.view.items if item.canonical == "Faith")
        self.assertEqual(faith.total_count, 2)

    def test_search_matches_owner_labels_and_scope_is_exact(self):
        self.controller.activate()
        visible = self.controller.set_query("Draft idea")
        self.assertEqual(tuple(item.canonical for item in visible), ("drafting",))
        self.controller.set_query("")
        self.controller.set_scope("scratchpad")
        self.assertEqual(tuple(item.canonical for item in self.view.items), ("drafting",))


    def test_search_ranks_exact_tag_identity_before_owner_only_matches(self):
        self.controller.activate()
        visible = self.controller.set_query("faith")
        self.assertEqual(tuple(item.canonical for item in visible), ("Faith",))

    def test_sort_by_usage_is_derived_and_does_not_persist_an_authority(self):
        self.controller.activate()
        visible = self.controller.set_sort(TAG_SORT_USAGE)
        self.assertEqual(tuple(item.canonical for item in visible), ("Faith", "drafting", "method"))
        self.assertEqual(self.view.sort, TAG_SORT_USAGE)

    def test_variants_filter_exposes_only_identity_issues(self):
        self.controller.activate()
        visible = self.controller.set_issues_only(True)
        self.assertEqual(tuple(item.canonical for item in visible), ("Faith",))
        self.assertTrue(self.view.issues)


    def test_show_all_tags_az_resets_every_presentation_filter(self):
        self.controller.activate()
        self.controller.set_query("faith")
        self.controller.set_scope("references")
        self.controller.set_sort(TAG_SORT_USAGE)
        self.controller.set_issues_only(True)
        self.assertTrue(self.controller.show_all_tags_az())
        self.assertEqual(self.view.query, "")
        self.assertEqual(self.view.scope, "all")
        self.assertEqual(self.view.sort, "name")
        self.assertFalse(self.view.issues)
        self.assertEqual(
            tuple(item.canonical for item in self.view.items),
            ("drafting", "Faith", "method"),
        )
        self.assertIn("All tags A–Z", self.view.status)

    def test_open_selected_use_dispatches_by_explicit_authority(self):
        self.controller.activate()
        self.controller.select_tag("faith")
        self.assertTrue(self.controller.open_selected_use())
        self.assertEqual(self.opened, [("reference", "r1")])
        self.controller.select_tag("drafting")
        self.assertTrue(self.controller.open_selected_use())
        self.assertEqual(self.opened[-1], ("scratchpad", "sp-1"))


if __name__ == "__main__":
    unittest.main()
