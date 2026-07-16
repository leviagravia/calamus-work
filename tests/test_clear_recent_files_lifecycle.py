import unittest

from calamus_recent_files import ClearRecentPlan, prepare_clear_recent_plan


class ClearRecentFilesLifecycleTests(unittest.TestCase):
    def test_plan_is_immutable_and_clears_to_empty(self):
        plan = prepare_clear_recent_plan(["/tmp/a.txt", "/tmp/b.txt"])
        self.assertIsInstance(plan, ClearRecentPlan)
        self.assertEqual(plan.previous_paths, ("/tmp/a.txt", "/tmp/b.txt"))
        self.assertEqual(plan.remaining_paths, ())
        self.assertTrue(plan.should_clear)
        with self.assertRaises(Exception):
            plan.previous_paths = ()

    def test_plan_deduplicates_and_ignores_empty_entries(self):
        plan = prepare_clear_recent_plan(
            ["/tmp/a.txt", "", "/tmp/a.txt", "/tmp/b.txt", ""]
        )
        self.assertEqual(plan.previous_paths, ("/tmp/a.txt", "/tmp/b.txt"))
        self.assertEqual(plan.remaining_paths, ())

    def test_empty_history_is_a_no_op(self):
        plan = prepare_clear_recent_plan([])
        self.assertEqual(plan.previous_paths, ())
        self.assertEqual(plan.remaining_paths, ())
        self.assertFalse(plan.should_clear)

    def test_tuple_input_is_supported(self):
        plan = prepare_clear_recent_plan(("/tmp/a.txt",))
        self.assertEqual(plan.previous_paths, ("/tmp/a.txt",))
        self.assertTrue(plan.should_clear)

    def test_container_type_is_strict(self):
        for value in (None, "not-a-list", {"/tmp/a.txt"}, 3):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    prepare_clear_recent_plan(value)

    def test_entry_type_is_strict(self):
        for value in ([None], [3], [object()]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    prepare_clear_recent_plan(value)


if __name__ == "__main__":
    unittest.main()
