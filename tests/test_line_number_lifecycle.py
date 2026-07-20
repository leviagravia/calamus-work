import unittest

from calamus_line_numbers_gateway import (
    execute_line_number_preference_request,
    refresh_line_number_gutter,
    sync_line_number_control,
)


class _Control:
    def __init__(self, host, events):
        self.host = host
        self.events = events
        self.active = None

    def set_active(self, active):
        self.events.append(("control", active, self.host._syncing_line_number_item))
        self.active = active


class _Gutter:
    def __init__(self, events, fail_on=None):
        self.events = events
        self.fail_on = fail_on

    def render(self, enabled, line_count, *, force=False):
        self.events.append(("render", enabled, line_count, force))
        if enabled == self.fail_on:
            raise RuntimeError("adapter failure")


class _Host:
    def __init__(self, enabled=True, *, save_results=None, fail_on_render=None):
        self.line_numbers_enabled = enabled
        self._syncing_line_number_item = False
        self.events = []
        self.save_results = list(save_results or [True])
        self.line_gutter = _Gutter(self.events, fail_on_render)
        self.line_item = _Control(self, self.events)
        self.errors = []

    def save_settings(self, overrides):
        self.events.append(("save", overrides["line_numbers"]))
        return self.save_results.pop(0)

    def text_stats(self):
        self.events.append(("stats",))
        return 10, 20, 7

    def update_title(self):
        self.events.append(("title", self.line_numbers_enabled))

    def error(self, message):
        self.errors.append(message)


class LineNumberLifecycleTests(unittest.TestCase):
    def test_success_persists_then_renders_before_runtime_commit(self):
        host = _Host(True)
        changed = execute_line_number_preference_request(host, False)
        self.assertTrue(changed)
        self.assertFalse(host.line_numbers_enabled)
        self.assertEqual(host.events[0], ("save", False))
        self.assertLess(host.events.index(("save", False)), host.events.index(("render", False, 7, False)))
        self.assertIn(("control", False, True), host.events)
        self.assertEqual(host.events[-1], ("title", False))
        self.assertEqual(host.errors, [])

    def test_persistence_failure_rolls_back_control_and_runtime(self):
        host = _Host(True, save_results=[False])
        changed = execute_line_number_preference_request(host, False)
        self.assertFalse(changed)
        self.assertTrue(host.line_numbers_enabled)
        self.assertEqual(host.events[0], ("save", False))
        self.assertNotIn(("render", False, 7, False), host.events)
        self.assertIn(("control", True, True), host.events)
        self.assertIn("Could not save", host.errors[0])

    def test_adapter_failure_restores_persistence_runtime_and_control(self):
        host = _Host(True, save_results=[True, True], fail_on_render=False)
        changed = execute_line_number_preference_request(host, False)
        self.assertFalse(changed)
        self.assertTrue(host.line_numbers_enabled)
        self.assertEqual(host.events[0], ("save", False))
        self.assertIn(("save", True), host.events)
        self.assertIn(("render", False, 7, False), host.events)
        self.assertIn(("render", True, 7, False), host.events)
        self.assertIn(("control", True, True), host.events)
        self.assertIn("adapter failure", host.errors[0])

    def test_noop_refreshes_view_without_persisting(self):
        host = _Host(True)
        changed = execute_line_number_preference_request(host, True)
        self.assertFalse(changed)
        self.assertNotIn(("save", True), host.events)
        self.assertIn(("render", True, 7, False), host.events)
        self.assertIn(("control", True, True), host.events)

    def test_invalid_request_rolls_back_control_and_reports_error(self):
        host = _Host(True)
        changed = execute_line_number_preference_request(host, 1)
        self.assertFalse(changed)
        self.assertTrue(host.line_numbers_enabled)
        self.assertEqual(host.events, [("control", True, True)])
        self.assertTrue(host.errors)

    def test_refresh_is_safe_without_gutter_and_uses_canonical_state(self):
        host = _Host(False)
        self.assertTrue(refresh_line_number_gutter(host))
        self.assertIn(("render", False, 7, False), host.events)
        del host.line_gutter
        self.assertFalse(refresh_line_number_gutter(host))


    def test_forced_refresh_reapplies_the_mapped_gutter(self):
        host = _Host(True)
        self.assertTrue(refresh_line_number_gutter(host, force=True))
        self.assertIn(("render", True, 7, True), host.events)

    def test_refresh_force_flag_must_be_boolean(self):
        host = _Host(True)
        with self.assertRaises(TypeError):
            refresh_line_number_gutter(host, force=1)

    def test_sync_control_uses_guard_and_restores_it(self):
        host = _Host(False)
        sync_line_number_control(host)
        self.assertEqual(host.line_item.active, False)
        self.assertEqual(host.events[-1], ("control", False, True))
        self.assertFalse(host._syncing_line_number_item)


if __name__ == "__main__":
    unittest.main()
