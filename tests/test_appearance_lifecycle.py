import unittest

from calamus_appearance_gateway import (
    execute_appearance_preference_request,
    sync_appearance_controls,
)
from calamus_appearance_preferences import (
    APPEARANCE_DARK,
    APPEARANCE_LIGHT,
    APPEARANCE_SYSTEM,
)


class _Item:
    def __init__(self, active=False):
        self.active = active
        self.events = []

    def get_active(self):
        self.events.append(("get-active", self.active))
        return self.active

    def set_active(self, value):
        self.active = value
        self.events.append(("set-active", value))


class _App:
    def __init__(self, mode=APPEARANCE_LIGHT, persist=True):
        self.appearance_mode = mode
        self.persist = persist
        self._syncing_appearance_items = False
        self.white_item = _Item(mode == APPEARANCE_LIGHT)
        self.dark_item = _Item(mode == APPEARANCE_DARK)
        self.events = []
        self.errors = []

    def save_settings(self, overrides=None):
        self.events.append(("save-settings", dict(overrides or {}), self.appearance_mode))
        return self.persist

    def apply_font(self):
        self.events.append(("apply-font", self.appearance_mode))

    def error(self, message):
        self.errors.append(message)


class AppearanceLifecycleTests(unittest.TestCase):
    def test_success_persists_before_runtime_commit_and_apply(self):
        app = _App(APPEARANCE_LIGHT, persist=True)
        self.assertTrue(execute_appearance_preference_request(app, APPEARANCE_DARK))
        self.assertEqual(app.appearance_mode, APPEARANCE_DARK)
        self.assertEqual(
            app.events,
            [
                (
                    "save-settings",
                    {
                        "appearance_mode": APPEARANCE_DARK,
                        "white_background": False,
                        "dark_mode": True,
                    },
                    APPEARANCE_LIGHT,
                ),
                ("apply-font", APPEARANCE_DARK),
            ],
        )
        self.assertEqual(app.white_item.events[-1], ("set-active", False))
        self.assertEqual(app.dark_item.events[-1], ("set-active", True))
        self.assertEqual(app.errors, [])

    def test_persistence_failure_rolls_back_both_menu_items_and_runtime(self):
        app = _App(APPEARANCE_LIGHT, persist=False)
        app.white_item.active = False
        app.dark_item.active = True
        self.assertFalse(execute_appearance_preference_request(app, APPEARANCE_DARK))
        self.assertEqual(app.appearance_mode, APPEARANCE_LIGHT)
        self.assertEqual(app.white_item.events[-1], ("set-active", True))
        self.assertEqual(app.dark_item.events[-1], ("set-active", False))
        self.assertEqual(app.errors, ["Could not save the Appearance preference."])
        self.assertFalse(app._syncing_appearance_items)
        self.assertNotIn(("apply-font", APPEARANCE_DARK), app.events)

    def test_noop_does_not_persist_or_render(self):
        app = _App(APPEARANCE_DARK, persist=True)
        self.assertFalse(execute_appearance_preference_request(app, APPEARANCE_DARK))
        self.assertEqual(app.events, [])
        self.assertEqual(app.errors, [])

    def test_sync_controls_maps_all_three_modes(self):
        app = _App(APPEARANCE_LIGHT)
        sync_appearance_controls(app)
        self.assertTrue(app.white_item.active)
        self.assertFalse(app.dark_item.active)
        app.appearance_mode = APPEARANCE_DARK
        sync_appearance_controls(app)
        self.assertFalse(app.white_item.active)
        self.assertTrue(app.dark_item.active)
        app.appearance_mode = APPEARANCE_SYSTEM
        sync_appearance_controls(app)
        self.assertFalse(app.white_item.active)
        self.assertFalse(app.dark_item.active)
        self.assertFalse(app._syncing_appearance_items)

    def test_invalid_request_rolls_back_and_reports_error(self):
        app = _App(APPEARANCE_LIGHT)
        self.assertFalse(execute_appearance_preference_request(app, "sepia"))
        self.assertEqual(app.appearance_mode, APPEARANCE_LIGHT)
        self.assertEqual(app.errors, ["requested appearance mode is invalid"])
        self.assertEqual(app.events, [])


if __name__ == "__main__":
    unittest.main()
