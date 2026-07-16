import unittest

from calamus_favorites import OpenFavoritePlan, prepare_open_favorite_plan


class FavoriteOpenLifecycleTests(unittest.TestCase):
    def test_regular_file_produces_open_target(self):
        plan = prepare_open_favorite_plan(
            "/tmp/chapter.txt",
            path_is_file=True,
        )
        self.assertIsInstance(plan, OpenFavoritePlan)
        self.assertEqual(plan.selected_path, "/tmp/chapter.txt")
        self.assertTrue(plan.should_open)
        self.assertEqual(plan.target_path, "/tmp/chapter.txt")

    def test_missing_or_non_file_path_suppresses_open_without_pruning_plan(self):
        plan = prepare_open_favorite_plan(
            "/tmp/unavailable.txt",
            path_is_file=False,
        )
        self.assertFalse(plan.should_open)
        self.assertIsNone(plan.target_path)
        self.assertEqual(plan.selected_path, "/tmp/unavailable.txt")
        self.assertFalse(hasattr(plan, "remaining_paths_after_failure"))
        self.assertFalse(hasattr(plan, "paths_to_persist"))

    def test_plan_is_immutable(self):
        plan = prepare_open_favorite_plan("/tmp/a.txt", path_is_file=True)
        with self.assertRaises(Exception):
            plan.target_path = "/tmp/b.txt"

    def test_invalid_inputs_are_rejected(self):
        with self.assertRaises(TypeError):
            prepare_open_favorite_plan(None, path_is_file=True)
        with self.assertRaises(ValueError):
            prepare_open_favorite_plan("", path_is_file=True)
        with self.assertRaises(TypeError):
            prepare_open_favorite_plan("/tmp/a.txt", path_is_file=1)


if __name__ == "__main__":
    unittest.main()
