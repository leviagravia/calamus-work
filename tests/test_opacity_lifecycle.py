import unittest

from calamus_opacity_gateway import (
    execute_opacity_preference_request,
    sync_transparent_control,
)


class _Item:
    def __init__(self, active=False):
        self.active = active
        self.events = []

    def set_active(self, value):
        self.active = value
        self.events.append(("set-active", value))


class _WidgetAPI:
    @staticmethod
    def set_opacity(host, fraction):
        host.events.append(("apply-opacity", fraction, host.opacity_percent))
        if host.fail_apply_for == fraction:
            raise RuntimeError("adapter failed")


class _App:
    def __init__(self, percent=100, save_results=None, fail_apply_for=None):
        self.opacity_percent = percent
        self._syncing_opacity_item = False
        self._opacity_widget_api = _WidgetAPI
        self.transparent_item = _Item(percent < 100)
        self.save_results = list(save_results if save_results is not None else [True])
        self.fail_apply_for = fail_apply_for
        self.events = []
        self.errors = []

    def save_settings(self, overrides=None):
        self.events.append(("save-settings", dict(overrides or {}), self.opacity_percent))
        return self.save_results.pop(0) if self.save_results else True

    def update_title(self):
        self.events.append(("update-title", self.opacity_percent))

    def error(self, message):
        self.errors.append(message)


class OpacityLifecycleTests(unittest.TestCase):
    def test_success_persists_then_applies_before_runtime_commit(self):
        app = _App(100, [True])
        self.assertTrue(execute_opacity_preference_request(app, 88))
        self.assertEqual(app.opacity_percent, 88)
        self.assertEqual(
            app.events,
            [
                ("save-settings", {"opacity": 88}, 100),
                ("apply-opacity", 0.88, 100),
                ("update-title", 88),
            ],
        )
        self.assertTrue(app.transparent_item.active)
        self.assertEqual(app.errors, [])

    def test_noop_does_not_persist_or_apply(self):
        app = _App(88)
        self.assertFalse(execute_opacity_preference_request(app, 88))
        self.assertEqual(app.events, [])
        self.assertTrue(app.transparent_item.active)
        self.assertEqual(app.errors, [])

    def test_persistence_failure_rolls_back_control_and_runtime(self):
        app = _App(100, [False])
        app.transparent_item.active = True
        self.assertFalse(execute_opacity_preference_request(app, 88))
        self.assertEqual(app.opacity_percent, 100)
        self.assertFalse(app.transparent_item.active)
        self.assertEqual(app.events, [("save-settings", {"opacity": 88}, 100)])
        self.assertEqual(app.errors, ["Could not save the Opacity preference."])

    def test_adapter_failure_restores_persistence_runtime_and_control(self):
        app = _App(100, [True, True], fail_apply_for=0.88)
        app.transparent_item.active = True
        self.assertFalse(execute_opacity_preference_request(app, 88))
        self.assertEqual(app.opacity_percent, 100)
        self.assertFalse(app.transparent_item.active)
        self.assertEqual(
            app.events,
            [
                ("save-settings", {"opacity": 88}, 100),
                ("apply-opacity", 0.88, 100),
                ("save-settings", {"opacity": 100}, 100),
                ("apply-opacity", 1.0, 100),
            ],
        )
        self.assertEqual(
            app.errors,
            ["Could not apply the Opacity preference: adapter failed"],
        )

    def test_invalid_request_rolls_back_control_and_reports_error(self):
        app = _App(100)
        app.transparent_item.active = True
        self.assertFalse(execute_opacity_preference_request(app, 10))
        self.assertEqual(app.events, [])
        self.assertFalse(app.transparent_item.active)
        self.assertEqual(app.errors, ["opacity percent is outside the supported range"])

    def test_sync_control_maps_canonical_percent(self):
        app = _App(100)
        sync_transparent_control(app)
        self.assertFalse(app.transparent_item.active)
        app.opacity_percent = 70
        sync_transparent_control(app)
        self.assertTrue(app.transparent_item.active)
        self.assertFalse(app._syncing_opacity_item)


if __name__ == "__main__":
    unittest.main()
