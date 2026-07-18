import os
import tempfile
import unittest

from calamus_favorites import (
    EditFavoritePlan,
    parse_favorite_edit_text,
    prepare_edit_favorite_plan,
)
from calamus_state import StateManager


class FavoriteEditLifecycleTests(unittest.TestCase):
    def test_dialog_text_is_trimmed_deduped_and_ordered(self):
        self.assertEqual(
            parse_favorite_edit_text("  /tmp/a.txt  \n\n/tmp/b.txt\n/tmp/a.txt\n"),
            ("/tmp/a.txt", "/tmp/b.txt"),
        )

    def test_empty_dialog_text_produces_empty_submission(self):
        self.assertEqual(parse_favorite_edit_text(" \n\t\n"), ())

    def test_parser_requires_text(self):
        for value in (None, 3, [], object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    parse_favorite_edit_text(value)

    def test_plan_separates_regular_files_from_rejected_entries(self):
        plan = prepare_edit_favorite_plan(
            ["/old/a.txt", "/old/missing.txt"],
            [
                ("/new/a.txt", True),
                ("/new/directory", False),
                ("/new/b.txt", True),
                ("/new/missing.txt", False),
            ],
        )
        self.assertIsInstance(plan, EditFavoritePlan)
        self.assertEqual(plan.previous_paths, ("/old/a.txt", "/old/missing.txt"))
        self.assertEqual(
            plan.submitted_paths,
            ("/new/a.txt", "/new/directory", "/new/b.txt", "/new/missing.txt"),
        )
        self.assertEqual(plan.updated_paths, ("/new/a.txt", "/new/b.txt"))
        self.assertEqual(plan.rejected_paths, ("/new/directory", "/new/missing.txt"))
        self.assertTrue(plan.changed)

    def test_plan_dedupes_normalized_paths_stably(self):
        plan = prepare_edit_favorite_plan(
            [],
            [
                ("/tmp/a.txt", True),
                ("/tmp/a.txt", True),
                ("/tmp/missing", False),
                ("/tmp/missing", False),
                ("/tmp/b.txt", True),
            ],
        )
        self.assertEqual(plan.submitted_paths, ("/tmp/a.txt", "/tmp/missing", "/tmp/b.txt"))
        self.assertEqual(plan.updated_paths, ("/tmp/a.txt", "/tmp/b.txt"))
        self.assertEqual(plan.rejected_paths, ("/tmp/missing",))

    def test_unchanged_valid_store_is_not_marked_changed(self):
        plan = prepare_edit_favorite_plan(
            ["/tmp/a.txt", "/tmp/b.txt"],
            [("/tmp/a.txt", True), ("/tmp/b.txt", True)],
        )
        self.assertFalse(plan.changed)

    def test_explicit_empty_edit_clears_store(self):
        plan = prepare_edit_favorite_plan(["/tmp/a.txt"], [])
        self.assertEqual(plan.updated_paths, ())
        self.assertTrue(plan.changed)

    def test_plan_is_immutable(self):
        plan = prepare_edit_favorite_plan([], [])
        with self.assertRaises(Exception):
            plan.updated_paths = ("/tmp/a.txt",)

    def test_plan_contract_is_strict(self):
        for existing in (None, "bad", {"/tmp/a"}):
            with self.subTest(existing=existing):
                with self.assertRaises(TypeError):
                    prepare_edit_favorite_plan(existing, [])
        for entries in (None, "bad", {("/tmp/a", True)}):
            with self.subTest(entries=entries):
                with self.assertRaises(TypeError):
                    prepare_edit_favorite_plan([], entries)
        invalid_entries = [
            ["/tmp/a"],
            [("/tmp/a",)],
            [("/tmp/a", True, "extra")],
            [(None, True)],
            [("", True)],
            [("/tmp/a", 1)],
        ]
        for entries in invalid_entries:
            with self.subTest(entries=entries):
                with self.assertRaises((TypeError, ValueError)):
                    prepare_edit_favorite_plan([], entries)

    def test_canonical_store_keeps_unavailable_entries_manageable(self):
        with tempfile.TemporaryDirectory() as td:
            state = StateManager(td)
            existing = os.path.join(td, "exists.txt")
            missing = os.path.join(td, "missing.txt")
            with open(existing, "w", encoding="utf-8"):
                pass
            self.assertTrue(state.save_favourites([existing, missing, existing]))
            self.assertEqual(state.load_favourite_store(), [existing, missing])
            self.assertEqual(state.load_favourites(), [existing])


if __name__ == "__main__":
    unittest.main()
