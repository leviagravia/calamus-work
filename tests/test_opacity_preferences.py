import unittest

from calamus_opacity import (
    DEFAULT_OPACITY_PERCENT,
    MAX_OPACITY_PERCENT,
    MIN_OPACITY_PERCENT,
    OpacityPreference,
    load_opacity_preference,
    normalize_opacity_percent,
    opacity_settings_overrides,
    prepare_opacity_preference_plan,
    transparent_mode_requested_percent,
)


class OpacityPreferenceTests(unittest.TestCase):
    def test_loader_defaults_and_requires_mapping(self):
        self.assertEqual(load_opacity_preference(None).percent, DEFAULT_OPACITY_PERCENT)
        self.assertEqual(load_opacity_preference({}).percent, DEFAULT_OPACITY_PERCENT)
        with self.assertRaises(TypeError):
            load_opacity_preference([])

    def test_loader_preserves_legacy_numeric_inputs_and_clamps(self):
        self.assertEqual(load_opacity_preference({"opacity": "70"}).percent, 70)
        self.assertEqual(load_opacity_preference({"opacity": 88.9}).percent, 88)
        self.assertEqual(load_opacity_preference({"opacity": 1}).percent, MIN_OPACITY_PERCENT)
        self.assertEqual(load_opacity_preference({"opacity": 999}).percent, MAX_OPACITY_PERCENT)

    def test_malformed_and_boolean_values_use_default(self):
        for value in (None, "opaque", object(), True, False):
            self.assertEqual(normalize_opacity_percent(value), DEFAULT_OPACITY_PERCENT)

    def test_preference_is_typed_and_reports_transparent_mode(self):
        self.assertTrue(OpacityPreference(88).transparent_mode)
        self.assertFalse(OpacityPreference(100).transparent_mode)
        self.assertEqual(OpacityPreference(75).fraction, 0.75)
        for value in (True, 29, 101, "88"):
            with self.assertRaises((TypeError, ValueError)):
                OpacityPreference(value)

    def test_plan_is_immutable_and_reports_noop(self):
        changed = prepare_opacity_preference_plan(100, 88)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.previous.percent, 100)
        self.assertEqual(changed.requested.percent, 88)
        noop = prepare_opacity_preference_plan(88, 88)
        self.assertFalse(noop.changed)
        with self.assertRaises(Exception):
            changed.requested = OpacityPreference(70)

    def test_plan_rejects_invalid_explicit_requests(self):
        for value in (True, 29, 101, "70"):
            with self.assertRaises((TypeError, ValueError)):
                prepare_opacity_preference_plan(88, value)

    def test_transparent_mode_preserves_existing_semantics(self):
        self.assertEqual(transparent_mode_requested_percent(100, True), DEFAULT_OPACITY_PERCENT)
        self.assertEqual(transparent_mode_requested_percent(70, True), 70)
        self.assertEqual(transparent_mode_requested_percent(70, False), 100)
        self.assertEqual(transparent_mode_requested_percent(100, False), 100)
        with self.assertRaises(TypeError):
            transparent_mode_requested_percent(100, 1)

    def test_settings_override_writes_one_canonical_integer(self):
        self.assertEqual(opacity_settings_overrides(70), {"opacity": 70})
        with self.assertRaises(ValueError):
            opacity_settings_overrides(10)


if __name__ == "__main__":
    unittest.main()
