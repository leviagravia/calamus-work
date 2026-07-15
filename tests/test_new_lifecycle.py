import unittest

from calamus_file_lifecycle import NewPlan, prepare_new_plan


class NewLifecyclePlanTests(unittest.TestCase):
    def test_new_plan_describes_clean_untitled_empty_document(self):
        plan = prepare_new_plan()
        self.assertIsInstance(plan, NewPlan)
        self.assertEqual(plan.text, "")
        self.assertIsNone(plan.target_path)
        self.assertFalse(plan.modified)

    def test_new_plan_is_deterministic(self):
        self.assertEqual(prepare_new_plan(), prepare_new_plan())

    def test_new_plan_is_immutable(self):
        plan = prepare_new_plan()
        with self.assertRaises(Exception):
            plan.text = "changed"


if __name__ == "__main__":
    unittest.main()
