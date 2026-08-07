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

from calamus_menu_model import WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS
from tests.calamus_gtk_test_driver import HAVE_GTK, close_visible_dialogs, display_ready, pump
from tests.w101_isolation_helpers import runtime_environment, runtime_paths, snapshot_tree, write_settings

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("CALAMUS_W105_RUN_REAL_GTK") == "1"


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w105_menu_ui_state_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def only_widget(window, command_id):
    widgets = window.menu_ui_adapter.widgets_for_command(command_id)
    if len(widgets) != 1:
        raise AssertionError(f"expected one widget for {command_id}, got {len(widgets)}")
    return widgets[0]


def dynamic_signature(window, slot_id):
    rows = window.menu_ui_adapter.dynamic_widgets(slot_id)
    return tuple((getattr(row, "get_label", lambda: None)(), row.get_sensitive()) for row in rows)


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W105 menu/UI-state GTK lane")
class W105MenuUiStateRealAppE2E(unittest.TestCase):
    def test_true_app_single_snapshot_projection_dynamic_rows_and_normal_close(self):
        real_home = Path(os.environ.get("CALAMUS_REAL_HOME", os.environ.get("HOME", str(Path.home())))).resolve()
        real_config_dir = real_home / ".config" / "calamus"
        real_before = snapshot_tree(real_config_dir)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"; workspace.mkdir()
            document = workspace / "UiState.md"
            document.write_text("# W105 UI State\n\nalpha beta gamma\n", encoding="utf-8")
            paths = runtime_paths(home)
            write_settings(paths.calamus_config_dir, workspace, document)
            window = None
            with patch.dict(os.environ, runtime_environment(paths), clear=False):
                window = load_app().App(); window.show_all(); pump()
                try:
                    adapter = window.menu_ui_adapter
                    controller = window.ui_state_controller
                    self.assertIsNotNone(adapter)
                    self.assertIsNotNone(controller)

                    # One immutable snapshot is projected to both logical availability and GTK.
                    snapshot = window.refresh_ui_state(); pump()
                    for command_id in (
                        "research.panel", "navigate.navigator-panel", "navigate.workspace-panel",
                        "writing.typewriter-mode", "options.word-wrap", "options.transparent-mode",
                        "options.always-on-top", "options.appearance.light", "options.appearance.dark",
                        "options.line-numbers",
                    ):
                        widget = only_widget(window, command_id)
                        self.assertEqual(bool(widget.get_active()), bool(snapshot.checked(command_id)))

                    # Menu-style explicit state and shortcut-style toggle converge on the same state.
                    research_widget = only_widget(window, "research.panel")
                    initial = bool(controller.snapshot.checked("research.panel"))
                    research_widget.set_active(not initial); pump()
                    self.assertEqual(bool(window.research_panel_runtime.is_visible), not initial)
                    self.assertEqual(bool(controller.snapshot.checked("research.panel")), not initial)
                    self.assertEqual(bool(research_widget.get_active()), not initial)
                    self.assertTrue(window.invoke_command("research.panel", source="shortcut-test").success); pump()
                    self.assertEqual(bool(window.research_panel_runtime.is_visible), initial)
                    self.assertEqual(bool(controller.snapshot.checked("research.panel")), initial)
                    self.assertEqual(bool(research_widget.get_active()), initial)

                    wrap_widget = only_widget(window, "options.word-wrap")
                    wrap_initial = bool(window.word_wrap)
                    self.assertTrue(window.invoke_command("options.word-wrap", source="shortcut-test").success); pump()
                    self.assertEqual(bool(window.word_wrap), not wrap_initial)
                    self.assertEqual(bool(wrap_widget.get_active()), not wrap_initial)
                    wrap_widget.set_active(wrap_initial); pump()
                    self.assertEqual(bool(window.word_wrap), wrap_initial)
                    self.assertEqual(bool(controller.snapshot.checked("options.word-wrap")), wrap_initial)

                    # Workspace-root availability and GTK sensitivity are the same projection.
                    self.assertTrue(window.workspace_root)
                    for command_id in WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS:
                        self.assertTrue(window.command_actions.availability.is_enabled(command_id))
                        self.assertTrue(only_widget(window, command_id).get_sensitive())
                    window.on_workspace_root_changed(None); pump()
                    for command_id in WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS:
                        self.assertFalse(window.command_actions.availability.is_enabled(command_id))
                        self.assertFalse(only_widget(window, command_id).get_sensitive())
                    window.on_workspace_root_changed(str(workspace)); pump()
                    for command_id in WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS:
                        self.assertTrue(window.command_actions.availability.is_enabled(command_id))
                        self.assertTrue(only_widget(window, command_id).get_sensitive())

                    # Dynamic application menus replace one immutable slot snapshot; they do not append stale rows.
                    for slot_id, populate in (
                        ("recent-files", window.populate_recent_menu),
                        ("favourites", window.populate_favourites_menu),
                        ("recent-workspaces", window.populate_recent_workspaces_menu),
                    ):
                        populate(); pump(); first = dynamic_signature(window, slot_id)
                        populate(); pump(); second = dynamic_signature(window, slot_id)
                        self.assertEqual(first, second, slot_id)

                    window.document_session.mark_clean(window.buffer_text())
                    window.may_continue = lambda: True
                    self.assertTrue(window.request_application_close()); pump()
                    self.assertTrue(window.application_lifecycle.is_shutdown)
                    print("W105_MENU_UI_STATE_TRUE_APP=PASS")
                finally:
                    close_visible_dialogs()
                    if window is not None and not window.application_lifecycle.is_shutdown:
                        window.destroy()
                    pump()

        self.assertEqual(real_before, snapshot_tree(real_config_dir))
        print("W105_REAL_CONFIG_UNCHANGED=PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
