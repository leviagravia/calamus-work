import os
import unittest


def _source_root():
    env_root = os.environ.get("CALAMUS_SOURCE_ROOT")
    if env_root:
        return os.path.abspath(env_root)
    test_dir = os.path.abspath(os.path.dirname(__file__))
    installed_like = os.path.abspath(os.path.join(test_dir, "..", "..", ".."))
    source_like = os.path.abspath(os.path.join(test_dir, ".."))
    if os.path.exists(os.path.join(source_like, "bin", "calamus")):
        return source_like
    return installed_like

def _launcher(name):
    root = _source_root()
    if os.path.exists(os.path.join(root, "bin", name)):
        return os.path.join(root, "bin", name)
    return os.path.join(root, "usr", "bin", name)

def _lib_dir():
    root = _source_root()
    if os.path.exists(os.path.join(root, "calamus")):
        return os.path.join(root, "calamus")
    return os.path.join(root, "usr", "lib", "calamus")


class ReleaseRegressionTests(unittest.TestCase):
    def test_expected_modules_are_present(self):
        lib = _lib_dir()
        expected = [
            "calamus_model.py", "calamus_commands.py", "calamus_ui.py", "calamus_state.py",
            "calamus_file_lifecycle.py", "calamus_recent_files.py", "calamus_writing.py", "calamus_clips.py", "calamus_audit.py",
        ]
        missing = [name for name in expected if not os.path.exists(os.path.join(lib, name))]
        self.assertEqual(missing, [])

    def test_launcher_is_executable(self):
        launcher = _launcher("calamus")
        self.assertTrue(os.path.exists(launcher))
        self.assertTrue(os.access(launcher, os.X_OK))

    def test_selftest_is_executable(self):
        launcher = _launcher("calamus-selftest")
        self.assertTrue(os.path.exists(launcher))
        self.assertTrue(os.access(launcher, os.X_OK))

    def test_clip_collection_toggle_uses_lazy_attach_remove(self):
        launcher = _launcher("calamus")
        with open(launcher, "r", encoding="utf-8") as f:
            source = f.read()
        self.assertIn("self.body_paned.pack2(self.clip_panel, False, False)", source)
        self.assertIn("self.body_paned.remove(self.clip_panel)", source)
        self.assertIn("self.clip_panel_attached = False", source)
        self.assertIn("self.clip_panel.show_all()", source)

    def test_clip_collection_starts_hidden(self):
        launcher = _launcher("calamus")
        with open(launcher, "r", encoding="utf-8") as f:
            source = f.read()
        self.assertIn("self.clip_panel_attached = False", source)
        self.assertIn("# Clip panel starts detached and is attached lazily on demand.", source)
        self.assertIn("self.body_paned.pack2(self.clip_panel, False, False)", source)

    def test_clip_collection_double_click_not_enter_activation(self):
        launcher = _launcher("calamus")
        with open(launcher, "r", encoding="utf-8") as f:
            source = f.read()
        self.assertIn('self.clip_list.connect("button-press-event", self.on_clip_list_button_press)', source)
        self.assertIn("def on_clip_list_button_press", source)
        self.assertIn("Gdk.EventType._2BUTTON_PRESS", source)
        self.assertIn("get_row_at_y", source)
        self.assertNotIn('self.clip_list.connect("row-activated"', source)
        self.assertNotIn("def on_clip_row_activated", source)
        self.assertNotIn("on_clip_row_button_press", source)


if __name__ == "__main__":
    unittest.main()
