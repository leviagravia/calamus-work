import os
import unittest

from calamus_shortcuts import conflicts, shortcut_rows


def _source_root():
    env_root = os.environ.get("CALAMUS_SOURCE_ROOT")
    if env_root:
        return os.path.abspath(env_root)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _launcher():
    return os.path.join(_source_root(), "bin", "calamus")


class Stable4RegressionTests(unittest.TestCase):
    def test_stable4_shortcuts_are_conflict_free(self):
        self.assertEqual(conflicts(), {})

    def test_revise_menu_and_bookmark_ui_are_exposed(self):
        rows = shortcut_rows()
        self.assertIn(("Revise", "Insert Bookmark Here", "Ctrl+F2"), rows)
        self.assertIn(("Revise", "Manage Bookmarks", "menu"), rows)
        self.assertIn(("Revise", "Title Case", "Ctrl+Alt+Y"), rows)
        self.assertNotIn(("Revise", "Title Case", "Ctrl+Alt+T"), rows)

    def test_line_numbers_use_viewport_aligned_drawing_gutter(self):
        with open(os.path.join(_source_root(), "calamus", "calamus_editor.py"), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("line_gutter_widget = Gtk.DrawingArea()", source)
        self.assertIn('line_gutter_widget.set_name("line-gutter")', source)
        self.assertIn('line_gutter_widget.connect("draw", draw_line_gutter)', source)
        self.assertNotIn("line_scroller = Gtk.ScrolledWindow()", source)
        self.assertNotIn("sync_gutter_scroll", source)

    def test_window_geometry_uses_minimum_only(self):
        with open(_launcher(), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("DEFAULT_WINDOW_WIDTH = 900", source)
        self.assertIn("apply_window_geometry_hints", source)
        self.assertIn("self.apply_window_geometry_hints()", source)
        self.assertIn("Gdk.WindowHints.MIN_SIZE", source)
        self.assertNotIn("Gdk.WindowHints.MAX_SIZE", source)
        self.assertNotIn("on_window_size_allocate", source)

    def test_undo_redo_caret_estimation_exists(self):
        with open(_launcher(), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("estimate_history_cursor", source)
        self.assertIn("set_text_from_history(text, self.estimate_history_cursor", source)


if __name__ == "__main__":
    unittest.main()


class Stable43GeometryChainTests(unittest.TestCase):
    def test_paned_children_use_explicit_resize_policy(self):
        with open(_launcher(), encoding="utf-8") as f:
            source = f.read()
        self.assertIn("self.body_paned.pack1(self.editor_box, True, True)", source)
        self.assertIn("self.body_paned.pack2(self.clip_panel, False, False)", source)
        self.assertNotIn("self.body_paned.add1(self.editor_box)", source)

    def test_command_finalize_is_not_duplicated(self):
        with open(_launcher(), encoding="utf-8") as f:
            source = f.read()
        block = source[source.index("def execute_command"):source.index("def perform_buffer_edit")]
        self.assertEqual(block.count("self.finalize_command_edit("), 1)
