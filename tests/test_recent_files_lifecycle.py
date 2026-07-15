import unittest

from calamus_recent_files import OpenRecentPlan, prepare_open_recent_plan


class RecentFilesLifecycleTests(unittest.TestCase):
    def test_existing_recent_path_produces_open_target_and_failure_cleanup(self):
        plan = prepare_open_recent_plan(
            "/tmp/b.txt",
            ["/tmp/a.txt", "/tmp/b.txt", "/tmp/c.txt"],
            path_exists=True,
        )
        self.assertIsInstance(plan, OpenRecentPlan)
        self.assertTrue(plan.should_open)
        self.assertEqual(plan.target_path, "/tmp/b.txt")
        self.assertEqual(
            plan.remaining_paths_after_failure,
            ("/tmp/a.txt", "/tmp/c.txt"),
        )

    def test_missing_recent_path_suppresses_open_and_prunes_all_duplicates(self):
        plan = prepare_open_recent_plan(
            "/tmp/missing.txt",
            ["/tmp/a.txt", "/tmp/missing.txt", "/tmp/missing.txt", "/tmp/a.txt"],
            path_exists=False,
        )
        self.assertFalse(plan.should_open)
        self.assertIsNone(plan.target_path)
        self.assertEqual(plan.remaining_paths_after_failure, ("/tmp/a.txt",))

    def test_input_sequence_is_not_mutated_and_plan_is_immutable(self):
        items = ["/tmp/a.txt", "/tmp/b.txt"]
        plan = prepare_open_recent_plan(
            "/tmp/a.txt",
            items,
            path_exists=True,
        )
        self.assertEqual(items, ["/tmp/a.txt", "/tmp/b.txt"])
        with self.assertRaises(Exception):
            plan.target_path = "/tmp/other.txt"

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(TypeError):
            prepare_open_recent_plan(None, [], path_exists=True)
        with self.assertRaises(ValueError):
            prepare_open_recent_plan("", [], path_exists=True)
        with self.assertRaises(TypeError):
            prepare_open_recent_plan("/tmp/a", {"/tmp/a"}, path_exists=True)
        with self.assertRaises(TypeError):
            prepare_open_recent_plan("/tmp/a", [1], path_exists=True)
        with self.assertRaises(TypeError):
            prepare_open_recent_plan("/tmp/a", [], path_exists=1)


if __name__ == "__main__":
    unittest.main()
