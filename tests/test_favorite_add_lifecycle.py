import unittest

from calamus_favorites import AddFavoritePlan, prepare_add_favorite_plan


class FavoriteAddLifecycleTests(unittest.TestCase):
    def test_new_favorite_is_inserted_at_front(self):
        plan = prepare_add_favorite_plan(
            "/tmp/current.txt",
            ["/tmp/a.txt", "/tmp/b.txt"],
        )
        self.assertIsInstance(plan, AddFavoritePlan)
        self.assertEqual(plan.favorite_path, "/tmp/current.txt")
        self.assertEqual(plan.previous_paths, ("/tmp/a.txt", "/tmp/b.txt"))
        self.assertEqual(
            plan.updated_paths,
            ("/tmp/current.txt", "/tmp/a.txt", "/tmp/b.txt"),
        )
        self.assertFalse(plan.was_already_present)

    def test_existing_favorite_moves_to_front_exactly_once(self):
        plan = prepare_add_favorite_plan(
            "/tmp/b.txt",
            ["/tmp/a.txt", "/tmp/b.txt", "/tmp/c.txt"],
        )
        self.assertEqual(
            plan.updated_paths,
            ("/tmp/b.txt", "/tmp/a.txt", "/tmp/c.txt"),
        )
        self.assertTrue(plan.was_already_present)
        self.assertEqual(plan.updated_paths.count("/tmp/b.txt"), 1)

    def test_duplicate_and_empty_existing_entries_are_cleaned_stably(self):
        plan = prepare_add_favorite_plan(
            "/tmp/current.txt",
            ["", "/tmp/a.txt", "/tmp/a.txt", "", "/tmp/b.txt", "/tmp/a.txt"],
        )
        self.assertEqual(plan.previous_paths, ("/tmp/a.txt", "/tmp/b.txt"))
        self.assertEqual(
            plan.updated_paths,
            ("/tmp/current.txt", "/tmp/a.txt", "/tmp/b.txt"),
        )

    def test_tuple_input_is_supported(self):
        plan = prepare_add_favorite_plan("/tmp/a.txt", ("/tmp/b.txt",))
        self.assertEqual(plan.updated_paths, ("/tmp/a.txt", "/tmp/b.txt"))

    def test_plan_is_immutable(self):
        plan = prepare_add_favorite_plan("/tmp/a.txt", [])
        with self.assertRaises(Exception):
            plan.favorite_path = "/tmp/b.txt"
        with self.assertRaises(Exception):
            plan.updated_paths = ()

    def test_current_path_type_and_value_are_strict(self):
        with self.assertRaises(TypeError):
            prepare_add_favorite_plan(None, [])
        with self.assertRaises(ValueError):
            prepare_add_favorite_plan("", [])

    def test_existing_container_type_is_strict(self):
        for value in (None, "not-a-list", {"/tmp/a.txt"}, 3):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    prepare_add_favorite_plan("/tmp/current.txt", value)

    def test_existing_entry_type_is_strict(self):
        for value in ([None], [3], [object()]):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    prepare_add_favorite_plan("/tmp/current.txt", value)


if __name__ == "__main__":
    unittest.main()
