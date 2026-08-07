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
from calamus_command_catalog import shortcut_bindings
from tests.w101_isolation_helpers import runtime_environment, runtime_paths, snapshot_tree, write_settings

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("CALAMUS_W107_RUN_REAL_GTK") == "1"


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w107_subsystem_host_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def buffer_text(window):
    buf = window.text.get_buffer(); start, end = buf.get_bounds()
    return buf.get_text(start, end, True)


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W107 subsystem host-port GTK lane")
class W107SubsystemHostPortRealAppE2E(unittest.TestCase):
    def test_true_app_narrow_subsystem_owners_search_workspace_research_and_normal_close(self):
        real_home = Path(os.environ.get("CALAMUS_REAL_HOME", os.environ.get("HOME", str(Path.home())))).resolve()
        real_config_dir = real_home / ".config" / "calamus"
        real_before = snapshot_tree(real_config_dir)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"; workspace.mkdir()
            document = workspace / "HostPorts.md"
            document.write_text("# W107 Host Ports\n\nalpha alpha gamma\n", encoding="utf-8")
            paths = runtime_paths(home)
            write_settings(paths.calamus_config_dir, workspace, document)
            window = None
            with patch.dict(os.environ, runtime_environment(paths), clear=False):
                window = load_app().App(); window.show_all(); pump()
                try:
                    # W107 authorities are private typed bundles.  Broad App/state/runtime aliases do not return.
                    self.assertTrue(hasattr(window, "_w107_subsystems"))
                    self.assertTrue(hasattr(window, "_research_components"))
                    self.assertFalse(hasattr(window, "state"))
                    for forbidden in ("search_runtime", "spellcheck_runtime", "print_runtime", "research_application_runtime", "workspace_host_runtime"):
                        self.assertFalse(hasattr(window, forbidden), forbidden)
                    host = window._components.workspace.host_runtime
                    self.assertFalse(hasattr(host, "components"))
                    self.assertFalse(hasattr(host, "_components"))
                    self.assertIs(host._application_runtime, window._components.workspace.application_runtime)
                    self.assertIs(host._mutation_controller, window._components.workspace.mutation_controller)
                    self.assertIs(host._mutation_runtime, window._components.workspace.mutation_runtime)
                    self.assertIs(host._panel_view, window._components.workspace.panel_view)
                    self.assertIs(host._panel_runtime, window._components.workspace.panel_runtime)

                    # Search mutation flows through the W107 runtime and W103 transaction authority.
                    before = buffer_text(window)
                    window.search_controller.configure("alpha", match_case=True, whole_word=True, wrap=True)
                    replaced = window.replace_all_literal("beta")
                    pump()
                    self.assertEqual(replaced, 2)
                    self.assertEqual(buffer_text(window), before.replace("alpha", "beta"))
                    self.assertTrue(window.document_session.modified)
                    self.assertTrue(window.document_session.requires_save_confirmation())
                    window.on_undo(); pump()
                    self.assertEqual(buffer_text(window), before)

                    # Workspace host owns command flow while W102 remains document identity authority.
                    self.assertEqual(host.root, str(workspace.resolve()))
                    self.assertTrue(window.workspace_application_runtime.close_root()); pump()
                    self.assertIsNone(host.root)
                    self.assertTrue(window.activate_workspace_path(str(workspace))); pump()
                    self.assertEqual(host.root, str(workspace.resolve()))

                    # Research composition is a separate typed bundle but visible command behavior is unchanged.
                    initial = bool(window.research_panel_runtime.is_visible)
                    window.toggle_research_panel(); pump()
                    self.assertEqual(bool(window.research_panel_runtime.is_visible), not initial)
                    window.toggle_research_panel(); pump()
                    self.assertEqual(bool(window.research_panel_runtime.is_visible), initial)

                    # Line Numbers command remains; Linux-Mint-conflicting Ctrl+Alt+L has no GTK binding/menu display.
                    line_widgets = window.menu_ui_adapter.widgets_for_command("options.line-numbers")
                    self.assertEqual(len(line_widgets), 1)
                    self.assertNotIn("Ctrl+Alt+L", line_widgets[0].get_label() or "")
                    self.assertFalse(any(
                        accelerator == "<Control><Alt>L"
                        for accelerator, _command_id, _data in shortcut_bindings()
                    ))
                    line_before = bool(window.line_numbers_enabled)
                    self.assertTrue(window.invoke_command("options.line-numbers", source="w107-true-app").success); pump()
                    self.assertEqual(bool(window.line_numbers_enabled), not line_before)
                    self.assertTrue(window.invoke_command("options.line-numbers", source="w107-true-app").success); pump()
                    self.assertEqual(bool(window.line_numbers_enabled), line_before)

                    window.document_session.mark_clean(window.buffer_text())
                    window.may_continue = lambda: True
                    self.assertTrue(window.request_application_close()); pump()
                    self.assertTrue(window.application_lifecycle.is_shutdown)
                    print("W107_SUBSYSTEM_HOST_PORT_TRUE_APP=PASS")
                finally:
                    close_visible_dialogs()
                    if window is not None and not window.application_lifecycle.is_shutdown:
                        window.destroy()
                    pump()

        self.assertEqual(real_before, snapshot_tree(real_config_dir))
        print("W107_REAL_CONFIG_UNCHANGED=PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
