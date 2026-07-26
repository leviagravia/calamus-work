import unittest

from calamus_authoring_bridge_controller import AuthoringBridgeController
from calamus_document_structure import build_document_structure
from calamus_references import ReferenceRecord
from calamus_source_notes import SourceNote


class FakeView:
    def __init__(self):
        self.widget = object()
        self.subject_calls = []
        self.render_calls = []
        self.selected = None
        self.focused = 0

    def set_subjects(self, mode, subjects, selected_id):
        self.subject_calls.append((mode, subjects, selected_id))

    def render(self, occurrences, selected_id, status):
        self.render_calls.append((occurrences, selected_id, status))
        self.selected = selected_id

    def selected_occurrence_id(self):
        return self.selected

    def select_occurrence_id(self, occurrence_id):
        self.selected = occurrence_id
        return True

    def focus_subject(self):
        self.focused += 1


class AuthoringBridgeControllerTests(unittest.TestCase):
    def setUp(self):
        self.text = "# Intro {#intro}\nCite [@ref].\n"
        self.records = (ReferenceRecord(key="ref", title="Reference"),)
        self.notes = (
            SourceNote(id="sn-1", kind="comment", text="Note", target="#intro"),
        )
        self.view = FakeView()
        self.errors = []
        self.document_nav = []
        self.note_nav = []
        self.reference_nav = []
        self.current_text = self.text
        self.controller = AuthoringBridgeController(
            self.view,
            reference_records_provider=lambda: self.records,
            document_text_provider=lambda: self.current_text,
            source_notes_provider=lambda: self.notes,
            document_structure_provider=lambda: build_document_structure(self.current_text),
            selected_reference_provider=lambda: "ref",
            current_heading_provider=lambda: "intro",
            navigate_document=lambda start, end, identity: self.document_nav.append((start, end, identity)) or True,
            show_source_note=lambda note_id: self.note_nav.append(note_id) or True,
            show_reference=lambda key: self.reference_nav.append(key) or True,
            on_error=self.errors.append,
        )

    def test_activate_prefers_selected_reference_and_builds_on_demand(self):
        self.controller.activate()
        self.assertEqual(self.controller.mode, "reference")
        self.assertEqual(self.controller.subject_id, "ref")
        self.assertEqual([item.kind for item in self.controller.visible_occurrences], ["citation"])
        self.assertEqual(self.view.focused, 1)

    def test_mode_switch_uses_known_subject_identity_and_direct_source_note_dispatch(self):
        self.controller.activate()
        self.assertTrue(self.controller.set_mode("heading"))
        self.assertEqual(self.controller.subject_id, "intro")
        self.assertEqual([item.kind for item in self.controller.visible_occurrences], ["source-note-target"])
        occurrence_id = self.controller.visible_occurrences[0].id
        self.view.selected = occurrence_id
        self.assertTrue(self.controller.open_selected())
        self.assertEqual(self.note_nav, ["sn-1"])
        self.assertEqual(self.document_nav, [])


    def test_related_mode_dispatches_direct_reference_identity(self):
        self.records = (
            ReferenceRecord(
                key="ref",
                title="Reference",
                extra_fields=(("Related Keys", "other"),),
            ),
            ReferenceRecord(key="other", title="Other"),
        )
        self.controller.activate()
        self.assertTrue(self.controller.set_mode("related"))
        self.assertEqual(self.controller.subject_id, "ref")
        self.assertEqual([item.kind for item in self.controller.visible_occurrences], ["related-reference"])
        self.view.selected = self.controller.visible_occurrences[0].id
        self.assertTrue(self.controller.open_selected())
        self.assertEqual(self.reference_nav, ["other"])

    def test_document_navigation_uses_stored_offsets_and_stale_snapshot_fails(self):
        self.controller.activate()
        occurrence = self.controller.visible_occurrences[0]
        self.view.selected = occurrence.id
        self.assertTrue(self.controller.open_selected())
        self.assertEqual(self.document_nav[0][:2], (occurrence.start_offset, occurrence.end_offset))

        self.current_text += "changed"
        self.assertFalse(self.controller.open_selected())
        self.assertIn("Refresh", self.errors[-1])
        self.assertEqual(len(self.document_nav), 1)

    def test_empty_and_invalid_modes_fail_controlled(self):
        empty_view = FakeView()
        controller = AuthoringBridgeController(
            empty_view,
            reference_records_provider=lambda: (),
            document_text_provider=lambda: "",
            source_notes_provider=lambda: (),
            document_structure_provider=lambda: build_document_structure(""),
            selected_reference_provider=lambda: None,
            current_heading_provider=lambda: None,
            navigate_document=lambda *_: True,
            show_source_note=lambda *_: True,
            show_reference=lambda *_: True,
            on_error=self.errors.append,
        )
        self.assertIsNotNone(controller.refresh())
        self.assertEqual(controller.visible_occurrences, ())
        self.assertFalse(controller.set_mode("graph"))
        self.assertIn("invalid", self.errors[-1])


if __name__ == "__main__":
    unittest.main()
