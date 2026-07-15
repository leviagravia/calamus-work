import unittest

from calamus_file_lifecycle import OpenPlan, prepare_open_plan


class OpenLifecyclePlanTests(unittest.TestCase):
    def test_open_plan_preserves_loaded_text_path_and_large_file_flag(self):
        plan = prepare_open_plan(
            "/tmp/note.txt",
            "alpha\nbeta\n",
            large_file=True,
        )
        self.assertIsInstance(plan, OpenPlan)
        self.assertEqual(plan.target_path, "/tmp/note.txt")
        self.assertEqual(plan.text, "alpha\nbeta\n")
        self.assertTrue(plan.large_file)

    def test_open_plan_defaults_to_normal_file(self):
        plan = prepare_open_plan("/tmp/note.txt", "Body")
        self.assertFalse(plan.large_file)

    def test_open_plan_rejects_invalid_path_before_state_transition(self):
        with self.assertRaises(TypeError):
            prepare_open_plan(None, "Body")
        with self.assertRaises(ValueError):
            prepare_open_plan("", "Body")

    def test_open_plan_rejects_non_string_text(self):
        with self.assertRaises(TypeError):
            prepare_open_plan("/tmp/note.txt", None)

    def test_open_plan_requires_boolean_large_file_flag(self):
        with self.assertRaises(TypeError):
            prepare_open_plan("/tmp/note.txt", "Body", large_file=1)

    def test_open_plan_is_immutable(self):
        plan = prepare_open_plan("/tmp/note.txt", "Body")
        with self.assertRaises(Exception):
            plan.text = "Changed"


if __name__ == "__main__":
    unittest.main()
