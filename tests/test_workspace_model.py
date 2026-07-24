import os
from pathlib import Path
import tempfile
import unittest

from calamus_workspace import WorkspaceError, normalize_workspace_root, path_is_within_root, scan_workspace


class WorkspaceModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Workspace"
        (self.root / "01_Drafts").mkdir(parents=True)
        (self.root / "02_Research").mkdir()
        (self.root / "01_Drafts" / "Capitolo_1.md").write_text("# Capitolo\n", encoding="utf-8")
        (self.root / "01_Drafts" / "Appunti.txt").write_text("Appunti\n", encoding="utf-8")
        (self.root / "02_Research" / "figure.png").write_bytes(b"png")
        (self.root / ".hidden.txt").write_text("hidden", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_is_deterministic_directories_first_and_hidden_free(self):
        snapshot = scan_workspace(str(self.root))
        self.assertEqual(snapshot.root, str(self.root))
        self.assertEqual([item.relative_path for item in snapshot.items], [
            "01_Drafts", "01_Drafts/Appunti.txt", "01_Drafts/Capitolo_1.md",
            "02_Research", "02_Research/figure.png",
        ])
        self.assertTrue(snapshot.by_relative_path("01_Drafts/Capitolo_1.md").internal_text)
        self.assertFalse(snapshot.by_relative_path("02_Research/figure.png").internal_text)

    def test_root_and_containment_fail_closed(self):
        with self.assertRaises(WorkspaceError):
            normalize_workspace_root("")
        self.assertTrue(path_is_within_root(str(self.root), str(self.root / "01_Drafts/Capitolo_1.md")))
        self.assertFalse(path_is_within_root(str(self.root), str(Path(self.tmp.name) / "outside.txt")))

    def test_symlink_is_listed_but_not_traversed(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        (outside / "secret.md").write_text("secret", encoding="utf-8")
        try:
            os.symlink(outside, self.root / "outside-link")
        except OSError:
            self.skipTest("symlinks unavailable")
        snapshot = scan_workspace(str(self.root))
        link = snapshot.by_relative_path("outside-link")
        self.assertIsNotNone(link)
        self.assertTrue(link.is_symlink)
        self.assertIsNone(snapshot.by_relative_path("outside-link/secret.md"))

    def test_scan_bounds_are_explicit(self):
        snapshot = scan_workspace(str(self.root), max_items=2)
        self.assertEqual(len(snapshot.items), 2)
        self.assertTrue(snapshot.diagnostics)


if __name__ == "__main__":
    unittest.main()
