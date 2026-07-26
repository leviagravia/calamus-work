import unittest
from unittest.mock import patch

from calamus_source_note_runtime import SourceNotePanelRuntime


class FakeController:
    available = True
    ids = ("existing",)
    target_options = (("#intro", "Introduction — #intro"),)

    def __init__(self):
        self.added = []
        self.selected = []

    def resolve_reference_key(self, key):
        return "canonical" if key in {"canonical", "alias"} else None

    def add(self, note):
        self.added.append(note)
        return True

    def select_id(self, note_id):
        self.selected.append(note_id)
        return note_id == "existing"


class SourceNoteSelectionBridgeTests(unittest.TestCase):
    def runtime(self):
        runtime = SourceNotePanelRuntime.__new__(SourceNotePanelRuntime)
        runtime._controller = FakeController()
        runtime._parent = object()
        runtime._reference_keys_provider = lambda: ("canonical",)
        runtime.sync_document = lambda **_: True
        runtime._show_error = lambda message: self.errors.append(message)
        return runtime

    def setUp(self):
        self.errors = []

    def test_prefills_selection_reference_and_heading_target(self):
        runtime = self.runtime()
        captured = []

        def fake_dialog(*args, **kwargs):
            captured.append(kwargs["draft"])
            return kwargs["draft"]

        with patch("calamus_source_note_runtime.run_source_note_dialog", fake_dialog):
            self.assertTrue(
                runtime.add_from_selection(
                    " Selected research text ",
                    reference_key="alias",
                    target="#intro",
                )
            )
        draft = captured[0]
        self.assertEqual(draft.text, "Selected research text")
        self.assertEqual(draft.kind, "quote")
        self.assertEqual(draft.reference_key, "canonical")
        self.assertEqual(draft.target, "#intro")
        self.assertEqual(runtime._controller.added, [draft])

    def test_without_reference_defaults_to_comment_and_empty_selection_is_blocked(self):
        runtime = self.runtime()
        captured = []
        with patch(
            "calamus_source_note_runtime.run_source_note_dialog",
            lambda *args, **kwargs: captured.append(kwargs["draft"]) or kwargs["draft"],
        ):
            self.assertTrue(runtime.add_from_selection("Comment text"))
        self.assertEqual(captured[0].kind, "comment")
        self.assertEqual(captured[0].reference_key, "")
        self.assertFalse(runtime.add_from_selection("   "))
        self.assertIn("Select document text", self.errors[-1])

    def test_show_note_dispatches_stable_id_directly(self):
        runtime = self.runtime()
        self.assertTrue(runtime.show_note("existing"))
        self.assertEqual(runtime._controller.selected, ["existing"])


class DirectSelectionView:
    def __init__(self):
        self.reset_count = 0
        self.selected = None

    def reset_filters(self):
        self.reset_count += 1

    def select_id(self, note_id):
        self.selected = note_id
        return True


class DirectSourceNoteSelectionTests(unittest.TestCase):
    def test_missing_reference_prefill_fails_before_dialog(self):
        runtime = SourceNoteSelectionBridgeTests().runtime()
        runtime._show_error = self.errors.append
        self.assertFalse(runtime.add_from_selection("Text", reference_key="missing"))
        self.assertIn("Reference key is missing", self.errors[-1])

    def setUp(self):
        self.errors = []

    def test_controller_select_id_clears_filters_before_direct_selection(self):
        from calamus_source_note_controller import SourceNoteController
        from calamus_source_notes import SourceNote

        controller = SourceNoteController.__new__(SourceNoteController)
        controller._notes = (SourceNote(id="sn-one", kind="comment", text="Text"),)
        controller._view = DirectSelectionView()
        controller._query = "hidden"
        controller._kind_filter = "quote"
        controller._reference_filter = "ref"
        controller.refresh = lambda: None

        self.assertTrue(controller.select_id("sn-one"))
        self.assertEqual(controller._query, "")
        self.assertEqual(controller._kind_filter, "all")
        self.assertEqual(controller._reference_filter, "all")
        self.assertEqual(controller._view.reset_count, 1)
        self.assertEqual(controller._view.selected, "sn-one")


class _RefreshRecorder:
    def __init__(self):
        self.calls = []

    def refresh(self, *, prefer_context=False):
        self.calls.append(prefer_context)
        return object()


class AuthoringBridgeRuntimeSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.errors = []

    def runtime(self, snapshot):
        from calamus_authoring_bridge_runtime import AuthoringBridgeRuntime

        runtime = AuthoringBridgeRuntime.__new__(AuthoringBridgeRuntime)
        runtime._parent = object()
        runtime._selection_provider = lambda: snapshot
        runtime._selected_reference_provider = lambda: "ref"
        runtime._on_error = self.errors.append
        runtime._controller = _RefreshRecorder()
        runtime._create_source_note_from_snapshot = lambda *args: True
        runtime._apply_heading_link_plan = lambda plan: True
        return runtime

    def test_source_note_uses_one_immutable_selection_snapshot(self):
        from calamus_authoring_bridge import EditorSelectionSnapshot

        text = "# Intro {#intro}\nSelected evidence.\n"
        start = text.index("Selected evidence")
        snapshot = EditorSelectionSnapshot(
            text, start, start + len("Selected evidence")
        )
        runtime = self.runtime(snapshot)
        captured = []
        runtime._create_source_note_from_snapshot = (
            lambda *args: captured.append(args) or True
        )

        self.assertTrue(runtime.on_create_source_note())
        self.assertEqual(captured, [(snapshot, "ref", "#intro")])
        self.assertEqual(runtime._controller.calls, [])

    def test_source_note_rejects_empty_or_foreign_snapshot(self):
        from calamus_authoring_bridge import EditorSelectionSnapshot

        runtime = self.runtime(EditorSelectionSnapshot("text", 2, 2))
        self.assertFalse(runtime.on_create_source_note())
        self.assertIn("Select document text", self.errors[-1])

        runtime = self.runtime((0, 1, "x"))
        self.assertFalse(runtime.on_create_source_note())
        self.assertIn("invalid snapshot", self.errors[-1])

    def test_heading_link_plan_uses_captured_range_not_later_cursor(self):
        from calamus_authoring_bridge import EditorSelectionSnapshot

        text = "# Intro {#intro}\nCite this.\n## Method {#method}\nBody.\n"
        start = text.index("Cite")
        snapshot = EditorSelectionSnapshot(text, start, start + len("Cite"))
        runtime = self.runtime(snapshot)
        plans = []
        runtime._apply_heading_link_plan = lambda plan: plans.append(plan) or True

        with patch(
            "calamus_authoring_bridge_runtime.run_heading_link_dialog",
            return_value=("method", "See method"),
        ) as dialog:
            self.assertTrue(runtime.on_insert_heading_link())

        self.assertEqual(dialog.call_args.kwargs["default_identifier"], "intro")
        self.assertEqual(dialog.call_args.kwargs["default_label"], "Cite")
        plan = plans[0]
        self.assertEqual((plan.replace_start, plan.replace_end), (start, start + 4))
        self.assertEqual(plan.replacement, "[See method](#method)")
        self.assertEqual(
            plan.document_after,
            text[:start] + "[See method](#method)" + text[start + 4:],
        )

    def test_heading_link_multiline_selection_is_rejected_before_dialog(self):
        from calamus_authoring_bridge import EditorSelectionSnapshot

        text = "# Intro {#intro}\none\ntwo\n"
        start = text.index("one")
        runtime = self.runtime(EditorSelectionSnapshot(text, start, start + 7))
        with patch(
            "calamus_authoring_bridge_runtime.run_heading_link_dialog"
        ) as dialog:
            self.assertFalse(runtime.on_insert_heading_link())
        dialog.assert_not_called()
        self.assertIn("one line", self.errors[-1])


if __name__ == "__main__":
    unittest.main()
