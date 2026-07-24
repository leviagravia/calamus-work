import os
from pathlib import Path
import tempfile
import unittest

from calamus_workspace import scan_workspace
from calamus_workspace_controller import WorkspaceController


class WorkspaceControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Workspace"
        self.root.mkdir()
        (self.root / "doc.md").write_text("hello", encoding="utf-8")
        (self.root / "image.png").write_bytes(b"png")
        (self.root / "folder").mkdir()
        self.controller = WorkspaceController()
        self.snapshot = self.controller.bind_root(str(self.root))

    def tearDown(self):
        self.tmp.cleanup()

    def test_activation_classifies_internal_external_and_directory(self):
        self.assertEqual(self.controller.activation_for(self.snapshot.by_relative_path("doc.md")).kind, "internal")
        self.assertEqual(self.controller.activation_for(self.snapshot.by_relative_path("image.png")).kind, "external")
        self.assertEqual(self.controller.activation_for(self.snapshot.by_relative_path("folder")).kind, "directory")

    def test_stale_item_fails_closed(self):
        item = self.snapshot.by_relative_path("doc.md")
        (self.root / "doc.md").unlink()
        self.controller.refresh()
        with self.assertRaises(ValueError):
            self.controller.activation_for(item)

    def test_toctou_replacement_by_symlink_is_blocked(self):
        item = self.snapshot.by_relative_path("doc.md")
        outside = Path(self.tmp.name) / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            os.unlink(item.path)
            os.symlink(outside, item.path)
        except OSError:
            self.skipTest("symlinks unavailable")
        result = self.controller.activation_for(item)
        self.assertEqual(result.kind, "blocked")


if __name__ == "__main__":
    unittest.main()
