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
RUN = os.environ.get("CALAMUS_W101_RUN_REAL_GTK") == "1"
EXPECTED_ORDER = (
    "document-session",
    "editor-infrastructure",
    "editor-transaction",
    "navigator-and-left-panel-host",
    "workspace",
    "right-panel-host",
    "clip-collection",
    "workspace-startup-binding",
)
ALIASES = {
    "document_session": "document_session.session",
    "document_session_controller": "document_session.controller",
    "history": "editor.history",
    "viewport_runtime": "editor.viewport_runtime",
    "history_runtime": "editor.history_runtime",
    "editor_transaction": "editor_transaction.controller",
    "editor_buffer_adapter": "editor_transaction.buffer_adapter",
    "typewriter_runtime": "editor.typewriter_runtime",
    "search_controller": "editor.search_controller",
    "tag": "editor.misspelling_tag",
    "search_tag": "editor.search_tag",
    "current_line_tag": "editor.current_line_tag",
    "navigation_controller": "navigator.navigation_controller",
    "left_panel_host": "navigator.left_panel_host",
    "navigator_panel_view": "navigator.panel_view",
    "navigator_panel_host": "navigator.panel_host",
    "navigator_panel_runtime": "navigator.panel_runtime",
    "workspace_controller": "workspace.controller",
    "workspace_panel_view": "workspace.panel_view",
    "workspace_application_runtime": "workspace.application_runtime",
    "workspace_mutation_controller": "workspace.mutation_controller",
    "workspace_mutation_runtime": "workspace.mutation_runtime",
    "workspace_panel_host": "workspace.panel_host",
    "workspace_panel_runtime": "workspace.panel_runtime",
    "right_panel_host": "right_panel_host",
    "clip_collection_view": "clips.view",
    "clip_collection": "clips.controller",
    "clip_collection_runtime": "clips.runtime",
}


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w101_composition_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def resolve(bundle, path):
    value = bundle
    for part in path.split("."):
        value = getattr(value, part)
    return value



@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W101 core composition GTK lane")
class W101CoreCompositionRealAppE2E(unittest.TestCase):
    def test_true_app_core_wiring_and_normal_close(self):
        real_home = Path(os.environ.get("CALAMUS_REAL_HOME", os.environ.get("HOME", str(Path.home())))).resolve()
        real_config_dir = real_home / ".config" / "calamus"
        real_config_before = snapshot_tree(real_config_dir)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"
            workspace.mkdir()
            document = workspace / "Composition.md"
            document.write_text("# Composition\n\nalpha beta alpha\n", encoding="utf-8")
            paths = runtime_paths(home)
            write_settings(paths.calamus_config_dir, workspace, document)
            window = None
            with patch.dict(os.environ, runtime_environment(paths), clear=False):
                window = load_app().App()
                window.show_all()
                pump()
                try:
                    self.assertEqual(Path(window.config_dir).resolve(), paths.calamus_config_dir)
                    self.assertEqual(
                        Path(window.persistence.config_dir).resolve(),
                        paths.calamus_config_dir,
                    )
                    self.assertEqual(
                        Path(window.persistence.repository.settings_file).resolve(),
                        paths.calamus_config_dir / "settings.json",
                    )

                    components = window._components
                    self.assertTrue(components.composition_complete)
                    self.assertEqual(components.build_order, EXPECTED_ORDER)
                    self.assertEqual(len(components.editor.signal_connections), 12)
                    for attribute, path in ALIASES.items():
                        self.assertIs(getattr(window, attribute), resolve(components, path))

                    # Search is operational through the composed controller.
                    buffer = window.text.get_buffer()
                    buffer.set_text("alpha beta alpha")
                    window.search_controller.configure("alpha")
                    self.assertEqual(window.search_controller.highlight(), 2)
                    self.assertTrue(window.search_controller.find())

                    # Navigator is a real registered left-panel client.
                    self.assertFalse(window.navigator_panel_runtime.is_visible)
                    window.navigator_panel_runtime.set_visible(True)
                    pump()
                    self.assertTrue(window.navigator_panel_runtime.is_visible)
                    window.navigator_panel_runtime.hide()
                    pump()
                    self.assertFalse(window.navigator_panel_runtime.is_visible)

                    # Workspace is bound and can rescan the real temporary root.
                    self.assertEqual(window.workspace_application_runtime.root, str(workspace.resolve()))
                    self.assertTrue(window.workspace_application_runtime.refresh())
                    window.workspace_panel_runtime.set_visible(True)
                    pump()
                    self.assertTrue(window.workspace_panel_runtime.is_visible)
                    window.workspace_panel_runtime.hide()

                    # Clip authority is real and isolated under the temporary HOME resolver.
                    self.assertTrue(window.clip_collection.ensure_authority())
                    self.assertTrue(window.clip_collection.create("Composition clip", "clip body", "cc"))
                    self.assertEqual(len(window.clip_collection.clips), 1)
                    self.assertTrue(str(window.clip_collection.authority_path).startswith(str(paths.calamus_config_dir)))

                    # Research and Document Overview remain present after core composition.
                    self.assertIsNotNone(window.research_coordinator)
                    self.assertIsNotNone(window.research_panel_view)
                    self.assertIsNotNone(window.document_overview_runtime)
                    self.assertEqual(len(window.research_panel_view._clients), 7)

                    window.may_continue = lambda: True
                    self.assertTrue(window.request_application_close())
                    pump()
                    report = window.application_lifecycle.shutdown_report
                    self.assertIsNotNone(report)
                    self.assertTrue(report.ok)
                    self.assertTrue(window.application_lifecycle.is_shutdown)
                    print("W101_ISOLATED_CONFIG_DIR=PASS")
                    print("W101_CORE_COMPOSITION_TRUE_APP=PASS")
                finally:
                    close_visible_dialogs()
                    if window is not None and not window.application_lifecycle.is_shutdown:
                        window.destroy()
                    pump()

        self.assertEqual(real_config_before, snapshot_tree(real_config_dir))
        print("W101_REAL_CONFIG_UNCHANGED=PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
