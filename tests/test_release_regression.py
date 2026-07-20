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
            "calamus_file_lifecycle.py", "calamus_recent_files.py", "calamus_writing.py",
            "calamus_clips.py", "calamus_clip_collection.py", "calamus_clip_panel.py",
            "calamus_right_panel.py", "calamus_audit.py",
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

    def test_right_panel_host_owns_lazy_attach_remove(self):
        lib = _lib_dir()
        with open(os.path.join(lib, "calamus_right_panel.py"), "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("self._paned.pack2(widget, False, False)", source)
        self.assertIn("self._paned.remove(widget)", source)
        self.assertIn("self._active_section = None", source)

    def test_clip_collection_starts_registered_but_detached(self):
        launcher = _launcher("calamus")
        with open(launcher, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("self.right_panel_host = RightPanelHost", source)
        self.assertIn('self.right_panel_host.register(', source)
        self.assertNotIn("self.clip_panel_attached", source)
        self.assertNotIn("self.body_paned.pack2(self.clip_panel", source)

    def test_clip_collection_double_click_left_app(self):
        launcher = _launcher("calamus")
        with open(launcher, "r", encoding="utf-8") as handle:
            launcher_source = handle.read()
        with open(os.path.join(_lib_dir(), "calamus_clip_panel.py"), "r", encoding="utf-8") as handle:
            panel_source = handle.read()
        self.assertNotIn("def on_clip_list_button_press", launcher_source)
        self.assertNotIn("Gdk.EventType._2BUTTON_PRESS", launcher_source)
        self.assertIn("def on_button_press", panel_source)
        self.assertIn("double_click_type=Gdk.EventType._2BUTTON_PRESS", panel_source)
        self.assertIn('clip_list.connect("button-press-event", adapter.on_button_press)', panel_source)
        self.assertNotIn('row-activated', panel_source)


if __name__ == "__main__":
    unittest.main()
