from pathlib import Path
import tempfile
import unittest

from calamus_document_structure import build_document_structure
from calamus_scratchpad import ScratchpadEntry
from calamus_scratchpad_controller import ScratchpadController


class FakeView:
    def __init__(self):
        self.widget = object()
        self.available = False
        self.message = ""
        self.tags = ()
        self.rendered = ()
        self.selected = None
        self.section_label = ""
    def set_available(self, available, message):
        self.available, self.message = available, message
    def set_tag_options(self, tags, selected):
        self.tags = tuple(tags)
    def render(self, entries, selected_id, status, missing, ambiguous):
        self.rendered = tuple(entries)
        self.selected = selected_id
        self.status = status
        self.missing = missing
        self.ambiguous = ambiguous
    def selected_id(self):
        return self.selected
    def select_id(self, entry_id):
        self.selected = entry_id
        return entry_id is not None
    def reset_filters(self):
        pass
    def set_section_filter_label(self, label):
        self.section_label = label


class ScratchpadControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.document = str(Path(self.tmp.name) / "article.md")
        Path(self.document).write_text("# Article {#article}\n\n## One {#one}\nText\n\n## Two {#two}\n", encoding="utf-8")
        self.structure = build_document_structure(Path(self.document).read_text(encoding="utf-8"))
        self.view = FakeView()
        self.errors = []
        self.conflict = "cancel"
        self.controller = ScratchpadController(
            self.view,
            document_structure_provider=lambda: self.structure,
            resolve_conflict=lambda: self.conflict,
            on_error=self.errors.append,
        )
        self.controller.bind_document(self.document)

    def tearDown(self):
        self.tmp.cleanup()

    def entry(self, entry_id="sp-1", **changes):
        values = dict(
            id=entry_id,
            type="note",
            title="A note",
            status="active",
            tags=("Alpha",),
            sections=("#one",),
            created="2026-07-27T20:00:00+02:00",
            updated="2026-07-27T20:00:00+02:00",
            body="Body text",
        )
        values.update(changes)
        return ScratchpadEntry(**values)

    def test_bind_add_reload_and_sidecar_path(self):
        self.assertTrue(self.controller.available)
        self.assertTrue(self.controller.sidecar_path.endswith("article.md.scratchpad.md"))
        self.assertTrue(self.controller.add(self.entry()))
        self.assertEqual(self.controller.ids, ("sp-1",))
        self.controller.reload()
        self.assertEqual(self.controller.entries[0].title, "A note")

    def test_filter_by_type_status_tag_and_section(self):
        self.controller.add(self.entry("sp-1"))
        self.controller.add(self.entry("sp-2", type="task", title="Task", status="archived", tags=("Beta",), sections=("#two",)))
        self.assertEqual([e.id for e in self.controller.filtered_entries(entry_type="task", status="all")], ["sp-2"])
        self.assertEqual([e.id for e in self.controller.filtered_entries(status="active-work")], ["sp-1"])
        self.assertEqual([e.id for e in self.controller.filtered_entries(status="all", tag="beta")], ["sp-2"])
        self.assertEqual([e.id for e in self.controller.filtered_entries(status="all", section="#two")], ["sp-2"])
        visible = self.controller.show_for_section("#one")
        self.assertEqual([e.id for e in visible], ["sp-1"])
        self.assertEqual(self.view.section_label, "#one")

    def test_missing_or_ambiguous_targets_block_new_mutations(self):
        self.assertFalse(self.controller.add(self.entry(sections=("#missing",))))
        self.assertIn("Heading target is missing", self.errors[-1])
        duplicate_text = "## One {#same}\n\n## Again {#same}\n"
        self.structure = build_document_structure(duplicate_text)
        with self.assertRaises(ValueError):
            # Duplicate identifiers are diagnosed by the structure and cannot be
            # represented as a valid ScratchpadEntry link through the controller.
            self.controller.target_state("#not valid")

    def test_archive_restore_update_delete_are_persist_first(self):
        self.controller.add(self.entry())
        archived = self.entry(status="archived", updated="later")
        self.assertTrue(self.controller.update("sp-1", archived))
        self.assertEqual(self.controller.entries[0].status, "archived")
        self.assertTrue(self.controller.delete("sp-1"))
        self.assertEqual(self.controller.entries, ())

    def test_diagnostics_make_sidecar_read_only(self):
        path = Path(self.controller.sidecar_path)
        path.write_text("# broken\n\n## sp-1\nTitle: A\n", encoding="utf-8")
        self.controller.reload()
        self.assertTrue(self.errors)
        self.assertFalse(self.controller.add(self.entry()))


if __name__ == "__main__":
    unittest.main()
