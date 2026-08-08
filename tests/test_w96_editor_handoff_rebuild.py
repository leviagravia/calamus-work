"""Anti-recurrence contracts for the W96 Editor-Handoff rebuild line."""
from __future__ import annotations

from pathlib import Path
import unittest

from calamus_document_dossier_app import (
    navigate_document_overview_offset,
    navigate_document_overview_range,
)

ROOT = Path(__file__).resolve().parents[1]


class W96EditorHandoffRebuildTests(unittest.TestCase):
    def test_app_boundary_owns_window_presentation_and_editor_focus(self):
        source = (ROOT / "calamus/calamus_document_dossier_app.py").read_text(encoding="utf-8")
        self.assertIn("def _present_document_editor", source)
        section = source.split("def _present_document_editor", 1)[1].split(
            "def navigate_document_overview_offset", 1
        )[0]
        self.assertIn("present_window()", section)
        self.assertIn("focus_document()", section)
        self.assertLess(section.index("\n    present_window()\n"), section.index("\n    focus_document()\n"))
        self.assertNotIn("app.", section)

    def test_handoff_command_order_is_owned_by_app_boundary(self):
        events = []

        class FakeText:
            def grab_focus(self):
                events.append("focus")
                return True

        class FakeApp:
            text = FakeText()

            def __init__(self):
                self._text = "0123456789"
                self._cursor = 0
                self.selection = None

            def buffer_text(self):
                return self._text

            def set_cursor_offset(self, offset):
                events.append(("cursor", offset))
                self._cursor = offset

            def get_cursor_offset(self):
                return self._cursor

            def select_range(self, start, end):
                events.append(("selection", start, end))
                self.selection = (start, end)

            def present(self):
                events.append("present")

        app = FakeApp()
        self.assertTrue(navigate_document_overview_offset(
            app.buffer_text, app.set_cursor_offset, app.get_cursor_offset,
            app.present, app.text.grab_focus, 4,
        ))
        self.assertEqual([("cursor", 4), "present", "focus"], events)
        events.clear()
        self.assertTrue(navigate_document_overview_range(
            app.buffer_text, app.select_range, app.present, app.text.grab_focus, 2, 6,
        ))
        self.assertEqual([("selection", 2, 6), "present", "focus"], events)

    def test_transient_tool_window_is_hidden_for_document_handoff(self):
        view = (ROOT / "calamus/calamus_document_overview_view.py").read_text(encoding="utf-8")
        runtime = (ROOT / "calamus/calamus_document_overview_runtime.py").read_text(encoding="utf-8")
        gate = (ROOT / "tests/test_w96_document_overview_app_desktop_e2e.py").read_text(encoding="utf-8")
        self.assertIn("def hide(self)", view)
        self.assertIn("def _handoff_to_document", runtime)
        self.assertIn("view.hide()", runtime)
        self.assertIn("self.assertFalse(runtime.window.get_visible())", gate)
        self.assertIn("self.assertFalse(runtime.window.get_mapped())", gate)
        self.assertIn('items["Document Overview"].activate()', gate)

    def test_true_app_gate_verifies_internal_focus_scroll_and_exact_destination(self):
        source = (ROOT / "tests/test_w96_document_overview_app_desktop_e2e.py").read_text(encoding="utf-8")
        for token in (
            "[Go to Method](#method)",
            "self.app.get_focus()",
            "self.app.get_visible()",
            "self.app.get_mapped()",
            "get_visible_rect()",
            "get_iter_location",
            "method_offset",
            "W96_EDITOR_HANDOFF_WM_ACTIVE_OBSERVATION",
        ):
            self.assertIn(token, source)
        self.assertNotIn("self.assertTrue(self.app.is_active())", source)

    def test_stale_status_and_notice_distinguish_mark_from_refresh(self):
        view = (ROOT / "calamus/calamus_document_overview_view.py").read_text(encoding="utf-8")
        runtime = (ROOT / "calamus/calamus_document_overview_runtime.py").read_text(encoding="utf-8")
        gate = (ROOT / "tests/test_w96_document_overview_app_desktop_e2e.py").read_text(encoding="utf-8")
        self.assertIn("no refresh has run yet", view)
        self.assertIn("Action blocked", runtime)
        self.assertIn("has now been refreshed", runtime)
        self.assertIn("selected_before_stale_action", gate)
        self.assertIn("self.assertEqual(before, runtime._controller.refresh_count)", gate)

    def test_current_contract_records_retired_line_and_new_failure_classifications(self):
        text = (ROOT / "docs/canonical/CALAMUS_W96_EDITOR_HANDOFF_REBUILD_CONTRACT.md").read_text(encoding="utf-8")
        for token in (
            "Profile-Owned Rebuild R1/R2 remain retired after FAIL 2/2",
            "CALAMUS-DOCUMENT-OVERVIEW-TRANSIENT-STACKING-01",
            "CALAMUS-DOCUMENT-OVERVIEW-STALE-OBSERVABILITY-01",
            "CALAMUS-DESKTOP-WM-ACTIVE-ORACLE-01",
            "hide the non-modal Document Overview tool window",
            "attempt 2/2",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
