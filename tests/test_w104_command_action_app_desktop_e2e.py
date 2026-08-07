from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

from tests.calamus_gtk_test_driver import HAVE_GTK, close_visible_dialogs, display_ready, pump
from tests.w101_isolation_helpers import runtime_environment, runtime_paths, snapshot_tree, write_settings

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("CALAMUS_W104_RUN_REAL_GTK") == "1"


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w104_command_action_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def buffer_text(window):
    buffer = window.text.get_buffer(); start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W104 command/action GTK lane")
class W104CommandActionRealAppE2E(unittest.TestCase):
    def test_true_app_stable_dispatch_parameterization_and_normal_close(self):
        real_home = Path(os.environ.get("CALAMUS_REAL_HOME", os.environ.get("HOME", str(Path.home())))).resolve()
        real_config_dir = real_home / ".config" / "calamus"
        real_before = snapshot_tree(real_config_dir)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"; workspace.mkdir()
            document = workspace / "Commands.md"
            document.write_text("alpha beta\nduplicate me\n", encoding="utf-8")
            paths = runtime_paths(home)
            write_settings(paths.calamus_config_dir, workspace, document)
            window = None
            with patch.dict(os.environ, runtime_environment(paths), clear=False):
                window = load_app().App(); window.show_all(); pump()
                try:
                    self.assertEqual(len(window.command_actions.registry), 118)
                    self.assertEqual(len(window.command_actions.binding_ids()), 117)
                    self.assertNotIn("view.clip-wrap-auto", window.command_actions.binding_ids())

                    buf = window.text.get_buffer()
                    start = buf.get_iter_at_offset(6); end = buf.get_iter_at_offset(10)
                    buf.select_range(start, end)
                    result = window.invoke_command("edit.uppercase", source="test")
                    self.assertTrue(result.success); pump()
                    self.assertEqual(buffer_text(window).splitlines()[0], "alpha BETA")
                    self.assertTrue(window.invoke_command("edit.undo", source="test").success); pump()
                    self.assertEqual(buffer_text(window).splitlines()[0], "alpha beta")

                    self.assertTrue(window.invoke_command(
                        "options.opacity.set", source="test", data={"percent": 88}
                    ).success); pump()
                    self.assertEqual(window.opacity_percent, 88)

                    invalid = window.invoke_command(
                        "options.opacity.set", source="test", data={"percent": 89}
                    )
                    self.assertFalse(invalid.success)
                    self.assertEqual(window.opacity_percent, 88)

                    window.document_session.mark_clean(buffer_text(window))
                    window.may_continue = lambda: True
                    self.assertTrue(window.request_application_close()); pump()
                    self.assertTrue(window.application_lifecycle.is_shutdown)
                    print("W104_COMMAND_ACTION_TRUE_APP=PASS")
                finally:
                    close_visible_dialogs()
                    if window is not None and not window.application_lifecycle.is_shutdown:
                        window.destroy()
                    pump()

        self.assertEqual(real_before, snapshot_tree(real_config_dir))
        print("W104_REAL_CONFIG_UNCHANGED=PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
