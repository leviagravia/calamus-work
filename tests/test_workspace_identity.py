import os
from pathlib import Path
import tempfile
import unittest

from calamus_workspace_identity import (
    WorkspacePathReferenceSnapshot, filter_trashed_path_collection,
    path_after_rename, path_is_trashed, plan_workspace_rename_identity,
    plan_workspace_trash_identity, rewrite_path_collection,
)


class WorkspaceIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Workspace"
        self.root.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_file_identity_follows_rename(self):
        source = self.root / "Draft.md"
        target = self.root / "Chapter.md"
        self.assertEqual(
            path_after_rename(str(source), str(source), str(target), source_is_directory=False),
            str(target),
        )

    def test_folder_rename_rewrites_descendants_but_not_prefix_lookalikes(self):
        source = self.root / "Drafts"
        target = self.root / "Chapters"
        child = source / "One.md"
        lookalike = self.root / "Drafts-old" / "One.md"
        self.assertEqual(
            path_after_rename(str(child), str(source), str(target), source_is_directory=True),
            str(target / "One.md"),
        )
        self.assertEqual(
            path_after_rename(str(lookalike), str(source), str(target), source_is_directory=True),
            str(lookalike),
        )

    def test_collections_preserve_order_and_dedupe_after_rewrite(self):
        source = self.root / "Draft.md"
        target = self.root / "Chapter.md"
        result = rewrite_path_collection(
            (str(source), str(target), str(self.root / "Other.md")),
            str(source), str(target), source_is_directory=False,
        )
        self.assertEqual(result, (str(target), str(self.root / "Other.md")))

    def test_identity_plan_updates_current_recent_and_favourites(self):
        source = self.root / "Drafts"
        target = self.root / "Chapters"
        current = source / "One.md"
        refs = WorkspacePathReferenceSnapshot(
            recent_files=(str(current), str(self.root / "Other.md")),
            favourites=(str(source / "Notes.txt"),),
        )
        plan = plan_workspace_rename_identity(
            str(current), refs, str(source), str(target), source_is_directory=True
        )
        self.assertTrue(plan.document_identity_changed)
        self.assertEqual(plan.current_file_after, str(target / "One.md"))
        self.assertEqual(plan.recent_files_after[0], str(target / "One.md"))
        self.assertEqual(plan.favourites_after, (str(target / "Notes.txt"),))

    def test_trash_identity_detaches_active_file_and_filters_references(self):
        source = self.root / "Draft.md"
        other = self.root / "Other.md"
        refs = WorkspacePathReferenceSnapshot(
            recent_files=(str(source), str(other)),
            favourites=(str(source), str(other)),
        )
        plan = plan_workspace_trash_identity(
            str(source), refs, str(source), source_is_directory=False
        )
        self.assertTrue(plan.active_document_detached)
        self.assertIsNone(plan.current_file_after)
        self.assertEqual(plan.recent_files_after, (str(other),))
        self.assertEqual(plan.favourites_after, (str(other),))

    def test_folder_trash_filters_descendants_not_prefix_lookalikes(self):
        source = self.root / "Drafts"
        child = source / "One.md"
        lookalike = self.root / "Drafts-old" / "Two.md"
        refs = WorkspacePathReferenceSnapshot(
            recent_files=(str(child), str(lookalike)),
            favourites=(str(source / "Notes.md"), str(lookalike)),
        )
        plan = plan_workspace_trash_identity(
            str(child), refs, str(source), source_is_directory=True
        )
        self.assertTrue(plan.active_document_detached)
        self.assertEqual(plan.recent_files_after, (str(lookalike),))
        self.assertEqual(plan.favourites_after, (str(lookalike),))
        self.assertTrue(path_is_trashed(str(child), str(source), source_is_directory=True))
        self.assertFalse(path_is_trashed(str(lookalike), str(source), source_is_directory=True))

    def test_trash_collection_preserves_order_and_dedupes(self):
        source = self.root / "Draft.md"
        other = self.root / "Other.md"
        result = filter_trashed_path_collection(
            (str(source), str(other), str(other)),
            str(source), source_is_directory=False,
        )
        self.assertEqual(result, (str(other),))


if __name__ == "__main__":
    unittest.main()
