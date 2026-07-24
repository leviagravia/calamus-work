import os
import unittest

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk
    HAVE_GTK = True
except Exception:
    HAVE_GTK = False

from pathlib import Path
import tempfile

def _gtk_display_ready():
    if not HAVE_GTK:
        return False, "PyGObject/GTK unavailable"
    try:
        result = Gtk.init_check()
    except TypeError:
        result = Gtk.init_check(None)
    ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
    if not ok:
        return False, "Gtk.init_check() failed"
    display = Gdk.Display.get_default()
    if display is None:
        return False, "Gdk.Display.get_default() returned None"
    backend = getattr(getattr(display, "__gtype__", None), "name", type(display).__name__)
    name = display.get_name() if hasattr(display, "get_name") else "unknown"
    return True, f"backend={backend} name={name}"


class WorkspaceGtkSemanticsTests(unittest.TestCase):
    def test_real_tree_row_activation_emits_semantic_file_event(self):
        ready, detail = _gtk_display_ready()
        if not ready:
            self.skipTest(f"GTK display unavailable: {detail}; DISPLAY={os.environ.get('DISPLAY')!r}; WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY')!r}")
        print(f"W79_GTK_DISPLAY=PASS {detail}")
        from calamus_workspace import scan_workspace
        from calamus_workspace_tree import WorkspaceTreeView
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "doc.md").write_text("hello", encoding="utf-8")
            tree = WorkspaceTreeView()
            tree.render(scan_workspace(str(root)))
            events = []
            tree.connect("file-activated", lambda _tree, item: events.append(item.relative_path))
            path = tree.path_for_relative("doc.md")
            self.assertIsNotNone(path)
            tree.emit("row-activated", path, tree.get_column(0))
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            self.assertEqual(events, ["doc.md"])
            model, tree_iter = tree.selection.get_selected()
            self.assertIsNotNone(tree_iter)
            self.assertEqual(model[tree_iter][1], "doc.md")

    def test_refresh_preserves_expanded_folder_and_selection(self):
        ready, detail = _gtk_display_ready()
        if not ready:
            self.skipTest(f"GTK display unavailable: {detail}")
        from calamus_workspace import scan_workspace
        from calamus_workspace_tree import WorkspaceTreeView
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "Drafts"
            folder.mkdir()
            (folder / "chapter.md").write_text("hello", encoding="utf-8")
            tree = WorkspaceTreeView()
            snapshot = scan_workspace(str(root))
            tree.render(snapshot)
            folder_path = tree.path_for_relative("Drafts")
            file_path = tree.path_for_relative("Drafts/chapter.md")
            self.assertIsNotNone(folder_path)
            self.assertIsNotNone(file_path)
            tree.expand_row(folder_path, False)
            tree.selection.select_path(file_path)
            tree.render(scan_workspace(str(root)))
            refreshed_folder = tree.path_for_relative("Drafts")
            self.assertTrue(tree.row_expanded(refreshed_folder))
            self.assertEqual(tree.selected_item().relative_path, "Drafts/chapter.md")

if __name__ == "__main__":
    unittest.main(verbosity=2)
