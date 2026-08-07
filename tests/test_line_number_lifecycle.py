import unittest

from calamus_line_numbers_gateway import execute_line_number_preference_request, refresh_line_number_gutter, sync_line_number_control


class _Gutter:
    def __init__(self, events, fail_on=None): self.events=events; self.fail_on=fail_on
    def current_line_count(self): self.events.append(("line-count",)); return 7
    def render(self, enabled, line_count, *, force=False):
        self.events.append(("render", enabled, line_count, force))
        if enabled == self.fail_on: raise RuntimeError("adapter failure")


class _Host:
    def __init__(self, enabled=True, *, save_results=None, fail_on_render=None):
        self.line_numbers_enabled=enabled; self.events=[]; self.errors=[]
        self.save_results=list(save_results or [True]); self.line_gutter=_Gutter(self.events, fail_on_render)
    def save_settings(self, overrides): self.events.append(("save", overrides["line_numbers"])); return self.save_results.pop(0)
    def refresh_ui_state(self): self.events.append(("refresh-ui-state", self.line_numbers_enabled))
    def update_title(self): self.events.append(("title", self.line_numbers_enabled))
    def error(self, message): self.errors.append(message)


class LineNumberLifecycleTests(unittest.TestCase):
    def test_success_persists_renders_commits_then_projects(self):
        h=_Host(True); self.assertTrue(execute_line_number_preference_request(h, False)); self.assertFalse(h.line_numbers_enabled)
        self.assertEqual(h.events[0], ("save", False)); self.assertIn(("render", False, 7, False), h.events)
        self.assertEqual(h.events[-2:], [("refresh-ui-state", False), ("title", False)])

    def test_persistence_failure_keeps_state_and_reprojects(self):
        h=_Host(True, save_results=[False]); self.assertFalse(execute_line_number_preference_request(h, False)); self.assertTrue(h.line_numbers_enabled)
        self.assertNotIn(("render", False, 7, False), h.events); self.assertEqual(h.events[-1], ("refresh-ui-state", True)); self.assertTrue(h.errors)

    def test_adapter_failure_restores_persistence_and_runtime_then_reprojects(self):
        h=_Host(True, save_results=[True,True], fail_on_render=False); self.assertFalse(execute_line_number_preference_request(h, False)); self.assertTrue(h.line_numbers_enabled)
        self.assertIn(("save", True), h.events); self.assertIn(("render", True, 7, False), h.events); self.assertEqual(h.events[-1], ("refresh-ui-state", True)); self.assertIn("adapter failure", h.errors[0])

    def test_noop_refreshes_gutter_and_ui_without_persisting(self):
        h=_Host(True); self.assertFalse(execute_line_number_preference_request(h, True)); self.assertNotIn(("save", True), h.events)
        self.assertIn(("render", True, 7, False), h.events); self.assertEqual(h.events[-1], ("refresh-ui-state", True))

    def test_invalid_request_reprojects_and_reports(self):
        h=_Host(True); self.assertFalse(execute_line_number_preference_request(h, 1)); self.assertEqual(h.events, [("refresh-ui-state", True)]); self.assertTrue(h.errors)

    def test_refresh_is_safe_and_force_is_boolean(self):
        h=_Host(False); self.assertTrue(refresh_line_number_gutter(h)); self.assertIn(("render", False, 7, False), h.events)
        self.assertTrue(refresh_line_number_gutter(h, force=True)); self.assertIn(("render", False, 7, True), h.events)
        with self.assertRaises(TypeError): refresh_line_number_gutter(h, force=1)
        del h.line_gutter; self.assertFalse(refresh_line_number_gutter(h))

    def test_sync_control_is_now_ui_state_projection_only(self):
        h=_Host(False); sync_line_number_control(h); self.assertEqual(h.events, [("refresh-ui-state", False)])


if __name__ == "__main__": unittest.main()
