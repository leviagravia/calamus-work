import unittest

from calamus_line_numbers import (
    DEFAULT_LINE_NUMBERS_ENABLED,
    LineNumberPreference,
    build_line_number_text,
    line_number_settings_overrides,
    load_line_number_preference,
    prepare_line_number_preference_plan,
)


class LineNumberPreferenceTests(unittest.TestCase):
    def test_loader_defaults_and_requires_mapping(self):
        self.assertEqual(
            load_line_number_preference(None),
            LineNumberPreference(DEFAULT_LINE_NUMBERS_ENABLED),
        )
        with self.assertRaises(TypeError):
            load_line_number_preference([])

    def test_loader_accepts_legacy_boolean_and_zero_one(self):
        self.assertTrue(load_line_number_preference({"line_numbers": True}).enabled)
        self.assertFalse(load_line_number_preference({"line_numbers": False}).enabled)
        self.assertTrue(load_line_number_preference({"line_numbers": 1}).enabled)
        self.assertFalse(load_line_number_preference({"line_numbers": 0}).enabled)

    def test_loader_rejects_arbitrary_truthiness(self):
        self.assertEqual(
            load_line_number_preference({"line_numbers": "false"}).enabled,
            DEFAULT_LINE_NUMBERS_ENABLED,
        )
        self.assertEqual(
            load_line_number_preference({"line_numbers": []}).enabled,
            DEFAULT_LINE_NUMBERS_ENABLED,
        )

    def test_plan_is_immutable_and_reports_noop(self):
        unchanged = prepare_line_number_preference_plan(True, True)
        changed = prepare_line_number_preference_plan(True, False)
        self.assertFalse(unchanged.changed)
        self.assertTrue(changed.changed)
        with self.assertRaises(Exception):
            changed.requested = LineNumberPreference(True)

    def test_plan_rejects_invalid_explicit_requests(self):
        for current, requested in ((1, True), (True, 0), ("yes", False)):
            with self.assertRaises(TypeError):
                prepare_line_number_preference_plan(current, requested)

    def test_settings_override_writes_one_canonical_boolean(self):
        self.assertEqual(line_number_settings_overrides(True), {"line_numbers": True})
        with self.assertRaises(TypeError):
            line_number_settings_overrides(1)

    def test_line_number_text_is_logical_one_based_and_handles_empty_document(self):
        self.assertEqual(build_line_number_text(0), "1")
        self.assertEqual(build_line_number_text(1), "1")
        self.assertEqual(build_line_number_text(4), "1\n2\n3\n4")

    def test_line_number_text_rejects_invalid_counts(self):
        with self.assertRaises(TypeError):
            build_line_number_text(True)
        with self.assertRaises(ValueError):
            build_line_number_text(-1)


if __name__ == "__main__":
    unittest.main()
