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

from calamus_file_lifecycle import prepare_new_plan, prepare_save_as_plan, prepare_save_plan
from tests.calamus_gtk_test_driver import HAVE_GTK, close_visible_dialogs, display_ready, pump
from tests.w101_isolation_helpers import runtime_environment, runtime_paths, snapshot_tree, write_settings

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("CALAMUS_W102_RUN_REAL_GTK") == "1"
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


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w102_document_session_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def buffer_text(window) -> str:
    buffer = window.text.get_buffer()
    start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W102 document-session GTK lane")
class W102DocumentSessionRealAppE2E(unittest.TestCase):
    def test_true_app_session_transitions_and_normal_close(self):
        real_home = Path(os.environ.get("CALAMUS_REAL_HOME", os.environ.get("HOME", str(Path.home())))).resolve()
        real_config_dir = real_home / ".config" / "calamus"
        real_config_before = snapshot_tree(real_config_dir)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"
            workspace.mkdir()
            first = workspace / "First.md"
            first.write_text("# First\n\nalpha\n", encoding="utf-8")
            second = workspace / "Second.md"
            second.write_text("# Second\n\nbeta\n", encoding="utf-8")
            saved_as = workspace / "Saved As.md"
            paths = runtime_paths(home)
            write_settings(paths.calamus_config_dir, workspace, first)

            window = None
            with patch.dict(os.environ, runtime_environment(paths), clear=False):
                window = load_app().App()
                window.show_all()
                pump()
                try:
                    components = window._components
                    self.assertEqual(components.build_order, EXPECTED_ORDER)
                    self.assertIs(window.document_session, components.document_session.session)
                    self.assertIs(window.document_session_controller, components.document_session.controller)
                    self.assertIs(window.document, window.document_session.document)
                    self.assertEqual(window.current_file, str(first))
                    self.assertFalse(window.modified)
                    self.assertEqual(buffer_text(window), first.read_text(encoding="utf-8"))

                    for name in ("document", "current_file", "modified", "loading"):
                        descriptor = getattr(type(window), name)
                        self.assertIsInstance(descriptor, property)
                        self.assertIsNone(descriptor.fset)
                        self.assertNotIn(name, window.__dict__)

                    # A real Gtk.TextBuffer edit is observed by the authoritative session.
                    window.text.get_buffer().set_text("edited first")
                    pump()
                    self.assertEqual(window.document_session.text, "edited first")
                    self.assertTrue(window.modified)

                    # Save commits clean state only after persistence succeeds.
                    plan = prepare_save_plan(window.current_file, buffer_text(window), trim_trailing_on_save=False)
                    self.assertTrue(window.execute_save_plan(plan))
                    self.assertEqual(first.read_text(encoding="utf-8"), "edited first")
                    self.assertFalse(window.modified)

                    # New commits a clean untitled identity after buffer replacement.
                    self.assertTrue(window.execute_new_plan(prepare_new_plan()))
                    self.assertIsNone(window.current_file)
                    self.assertEqual(buffer_text(window), "")
                    self.assertFalse(window.modified)

                    # Open commits the selected path after read and replacement succeed.
                    self.assertTrue(window.open_path(str(second)))
                    self.assertEqual(window.current_file, str(second))
                    self.assertEqual(buffer_text(window), second.read_text(encoding="utf-8"))
                    self.assertFalse(window.modified)

                    # Save As commits the new identity only after write success.
                    window.text.get_buffer().set_text("saved-as body")
                    pump()
                    save_as_plan = prepare_save_as_plan(str(saved_as), buffer_text(window), trim_trailing_on_save=False)
                    self.assertIsNotNone(save_as_plan)
                    self.assertTrue(window.execute_save_plan(save_as_plan))
                    self.assertEqual(window.current_file, str(saved_as))
                    self.assertEqual(saved_as.read_text(encoding="utf-8"), "saved-as body")
                    self.assertFalse(window.modified)

                    # Workspace-facing rebind/detach semantics are authoritative.
                    window.document_session.rebind_path(str(workspace / "Renamed.md"))
                    self.assertEqual(window.current_file, str(workspace / "Renamed.md"))
                    window.document_session.detach(buffer_text(window))
                    self.assertIsNone(window.current_file)
                    self.assertTrue(window.modified)
                    window.document_session.mark_clean(buffer_text(window))
                    self.assertFalse(window.document_session.requires_save_confirmation())

                    window.may_continue = lambda: True
                    self.assertTrue(window.request_application_close())
                    pump()
                    report = window.application_lifecycle.shutdown_report
                    self.assertIsNotNone(report)
                    self.assertTrue(report.ok)
                    self.assertTrue(window.application_lifecycle.is_shutdown)
                    print("W102_DOCUMENT_SESSION_TRUE_APP=PASS")
                finally:
                    close_visible_dialogs()
                    if window is not None and not window.application_lifecycle.is_shutdown:
                        window.destroy()
                    pump()

        self.assertEqual(real_config_before, snapshot_tree(real_config_dir))
        print("W102_REAL_CONFIG_UNCHANGED=PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
