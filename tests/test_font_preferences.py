import unittest

from calamus_typography import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    FontPreference,
    FontPreferencePlan,
    load_font_preference,
    normalize_font_family,
    normalize_font_size,
    prepare_font_preference_plan,
)


class FontPreferenceTests(unittest.TestCase):
    def test_loader_normalizes_legacy_values_and_defaults(self):
        self.assertEqual(
            load_font_preference({"font_family": "  Serif  ", "font_size": "18"}),
            FontPreference("Serif", 18),
        )
        self.assertEqual(
            load_font_preference({"font_family": "", "font_size": "bad"}),
            FontPreference(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE),
        )
        self.assertEqual(load_font_preference(None), FontPreference(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE))

    def test_loader_requires_mapping(self):
        with self.assertRaises(TypeError):
            load_font_preference([])

    def test_family_normalizer_rejects_controls(self):
        self.assertEqual(normalize_font_family("Mono\nspace"), DEFAULT_FONT_FAMILY)
        self.assertEqual(normalize_font_family("Mono\x00space"), DEFAULT_FONT_FAMILY)

    def test_size_normalizer_rejects_bool_and_clamps(self):
        self.assertEqual(normalize_font_size(True), DEFAULT_FONT_SIZE)
        self.assertEqual(normalize_font_size(MIN_FONT_SIZE - 100), MIN_FONT_SIZE)
        self.assertEqual(normalize_font_size(MAX_FONT_SIZE + 100), MAX_FONT_SIZE)

    def test_plan_is_immutable_and_reports_noop(self):
        changed = prepare_font_preference_plan("Monospace", 12, "Serif", 16)
        self.assertIsInstance(changed, FontPreferencePlan)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.previous, FontPreference("Monospace", 12))
        self.assertEqual(changed.requested, FontPreference("Serif", 16))
        with self.assertRaises(Exception):
            changed.requested = FontPreference("Sans", 10)

        noop = prepare_font_preference_plan("Monospace", 12, "Monospace", 12)
        self.assertFalse(noop.changed)

    def test_plan_rejects_invalid_requested_family_and_non_integer_size(self):
        with self.assertRaises(ValueError):
            prepare_font_preference_plan("Monospace", 12, "", 12)
        with self.assertRaises(ValueError):
            prepare_font_preference_plan("Monospace", 12, "Bad\nFont", 12)
        with self.assertRaises(TypeError):
            prepare_font_preference_plan("Monospace", 12, "Serif", True)


if __name__ == "__main__":
    unittest.main()
