import unittest

from calamus_view_preferences import (
    DEFAULT_TEXT_WRAP,
    TEXT_WRAP_KEY,
    TextWrapPlan,
    load_text_wrap_preference,
    normalize_boolean,
    prepare_text_wrap_plan,
)


class TextWrapPreferenceTests(unittest.TestCase):
    def test_loader_accepts_real_booleans_and_legacy_zero_one(self):
        self.assertTrue(load_text_wrap_preference({TEXT_WRAP_KEY: True}))
        self.assertFalse(load_text_wrap_preference({TEXT_WRAP_KEY: False}))
        self.assertTrue(load_text_wrap_preference({TEXT_WRAP_KEY: 1}))
        self.assertFalse(load_text_wrap_preference({TEXT_WRAP_KEY: 0}))

    def test_loader_rejects_truthy_strings_and_uses_default(self):
        self.assertEqual(load_text_wrap_preference({TEXT_WRAP_KEY: "false"}), DEFAULT_TEXT_WRAP)
        self.assertEqual(load_text_wrap_preference({TEXT_WRAP_KEY: []}), DEFAULT_TEXT_WRAP)
        self.assertEqual(load_text_wrap_preference({}), DEFAULT_TEXT_WRAP)
        self.assertEqual(load_text_wrap_preference(None), DEFAULT_TEXT_WRAP)

    def test_loader_requires_mapping_when_explicit_value_is_supplied(self):
        with self.assertRaises(TypeError):
            load_text_wrap_preference([])

    def test_normalizer_requires_boolean_default(self):
        with self.assertRaises(TypeError):
            normalize_boolean(True, 1)

    def test_plan_is_immutable_and_reports_change(self):
        changed = prepare_text_wrap_plan(False, True)
        self.assertIsInstance(changed, TextWrapPlan)
        self.assertTrue(changed.changed)
        self.assertFalse(changed.previous_enabled)
        self.assertTrue(changed.enabled)
        with self.assertRaises(Exception):
            changed.enabled = False

        noop = prepare_text_wrap_plan(True, True)
        self.assertFalse(noop.changed)

    def test_plan_rejects_non_boolean_states(self):
        for previous, requested in ((1, True), (False, "yes"), (None, False)):
            with self.subTest(previous=previous, requested=requested):
                with self.assertRaises(TypeError):
                    prepare_text_wrap_plan(previous, requested)




if __name__ == "__main__":
    unittest.main()
