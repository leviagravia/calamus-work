from pathlib import Path
import tempfile
import unittest

from calamus_workspace_controller import WorkspaceController
from calamus_workspace_application import WorkspaceApplicationRuntime


class FakeView:
    def __init__(self):
        self.snapshot = None
        self.selected = None
    def render(self, snapshot): self.snapshot = snapshot
    def selected_item(self): return self.selected

class FakeRecentWorkspaces:
    def __init__(self): self.recent=[]
    def add(self, path): self.recent.insert(0,path)


class WorkspaceApplicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/"Workspace"; self.root.mkdir()
        (self.root/"doc.md").write_text("body",encoding="utf-8")
        (self.root/"image.png").write_bytes(b"png")
        self.view=FakeView(); self.recent=FakeRecentWorkspaces(); self.calls=[]; self.errors=[]; self.roots=[]
        self.runtime=WorkspaceApplicationRuntime(
            WorkspaceController(), self.view, self.recent,
            may_continue=lambda: True,
            open_document=lambda path: self.calls.append(("internal",path)) or True,
            open_external=lambda path: self.calls.append(("external",path)) or True,
            reveal_external=lambda path: self.calls.append(("reveal",path)) or True,
            record_workspace_root=lambda root: self.roots.append(root) or True,
            report_error=self.errors.append,
            on_root_changed=lambda root: self.calls.append(("root",root)),
            on_recent_changed=lambda: self.calls.append(("recent",None)),
        )
        self.runtime.open_root(str(self.root))

    def tearDown(self): self.tmp.cleanup()

    def test_open_root_is_persist_after_valid_scan(self):
        self.assertEqual(self.view.snapshot.root,str(self.root))
        self.assertEqual(self.recent.recent,[str(self.root)])
        self.assertIn(str(self.root), self.roots)

    def test_activation_routes_to_distinct_gateways(self):
        self.runtime.activate_item(self.view.snapshot.by_relative_path("doc.md"))
        self.runtime.activate_item(self.view.snapshot.by_relative_path("image.png"))
        self.assertIn(("internal",str(self.root/"doc.md")),self.calls)
        self.assertIn(("external",str(self.root/"image.png")),self.calls)

    def test_unsaved_gate_precedes_internal_open(self):
        blocked=WorkspaceApplicationRuntime(
            WorkspaceController(), self.view, self.recent,
            may_continue=lambda: False,
            open_document=lambda path: self.fail("must not open"),
            open_external=lambda path: True,
            reveal_external=lambda path: True,
            record_workspace_root=lambda root: True,
            report_error=self.errors.append,
            on_root_changed=lambda root: None,
            on_recent_changed=lambda: None,
        )
        blocked.open_root(str(self.root),persist=False)
        self.assertFalse(blocked.activate_item(blocked._controller.snapshot.by_relative_path("doc.md")))


if __name__ == "__main__": unittest.main()
