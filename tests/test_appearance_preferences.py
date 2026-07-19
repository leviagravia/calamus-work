import unittest

from calamus_appearance_preferences import (
    APPEARANCE_DARK,
    APPEARANCE_LIGHT,
    APPEARANCE_SYSTEM,
    AppearancePreference,
    AppearancePreferencePlan,
    appearance_settings_overrides,
    load_appearance_preference,
    normalize_appearance_mode,
    prepare_appearance_preference_plan,
)


class AppearancePreferenceTests(unittest.TestCase):
    def test_loader_prefers_canonical_mode(self):
        preference = load_appearance_preference({
            "appearance_mode": " DARK ",
            "white_background": True,
            "dark_mode": False,
        })
        self.assertEqual(preference, AppearancePreference(APPEARANCE_DARK))

    def test_loader_migrates_each_legacy_state(self):
        self.assertEqual(
            load_appearance_preference({"white_background": True, "dark_mode": False}),
            AppearancePreference(APPEARANCE_LIGHT),
        )
        self.assertEqual(
            load_appearance_preference({"white_background": False, "dark_mode": True}),
            AppearancePreference(APPEARANCE_DARK),
        )
        self.assertEqual(
            load_appearance_preference({"white_background": False, "dark_mode": False}),
            AppearancePreference(APPEARANCE_SYSTEM),
        )

    def test_legacy_impossible_true_true_state_preserves_w64_light_precedence(self):
        self.assertEqual(
            load_appearance_preference({"white_background": True, "dark_mode": True}),
            AppearancePreference(APPEARANCE_LIGHT),
        )

    def test_malformed_values_do_not_use_python_truthiness(self):
        self.assertEqual(
            load_appearance_preference({"white_background": "false", "dark_mode": "true"}),
            AppearancePreference(APPEARANCE_LIGHT),
        )
        self.assertEqual(normalize_appearance_mode(True), APPEARANCE_LIGHT)

    def test_loader_defaults_and_requires_mapping(self):
        self.assertEqual(load_appearance_preference(None), AppearancePreference(APPEARANCE_LIGHT))
        self.assertEqual(load_appearance_preference({}), AppearancePreference(APPEARANCE_LIGHT))
        with self.assertRaises(TypeError):
            load_appearance_preference([])

    def test_plan_is_immutable_and_reports_noop(self):
        plan = prepare_appearance_preference_plan(APPEARANCE_LIGHT, APPEARANCE_DARK)
        self.assertIsInstance(plan, AppearancePreferencePlan)
        self.assertTrue(plan.changed)
        self.assertEqual(plan.previous.mode, APPEARANCE_LIGHT)
        self.assertEqual(plan.requested.mode, APPEARANCE_DARK)
        with self.assertRaises(Exception):
            plan.requested = AppearancePreference(APPEARANCE_SYSTEM)
        self.assertFalse(
            prepare_appearance_preference_plan(APPEARANCE_SYSTEM, APPEARANCE_SYSTEM).changed
        )

    def test_plan_rejects_invalid_explicit_requests(self):
        with self.assertRaises(ValueError):
            prepare_appearance_preference_plan("sepia", APPEARANCE_DARK)
        with self.assertRaises(ValueError):
            prepare_appearance_preference_plan(APPEARANCE_LIGHT, "sepia")
        with self.assertRaises(ValueError):
            AppearancePreference("sepia")

    def test_overrides_write_one_canonical_state_and_legacy_compatibility(self):
        self.assertEqual(
            appearance_settings_overrides(APPEARANCE_SYSTEM),
            {
                "appearance_mode": APPEARANCE_SYSTEM,
                "white_background": False,
                "dark_mode": False,
            },
        )
        self.assertEqual(appearance_settings_overrides(APPEARANCE_LIGHT)["white_background"], True)
        self.assertEqual(appearance_settings_overrides(APPEARANCE_DARK)["dark_mode"], True)


if __name__ == "__main__":
    unittest.main()
