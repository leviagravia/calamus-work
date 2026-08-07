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
RUN = os.environ.get("CALAMUS_W103_RUN_REAL_GTK") == "1"
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
    name = "w103_editor_transaction_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def buffer_text(window):
    buffer = window.text.get_buffer()
    start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W103 editor-transaction GTK lane")
class W103EditorTransactionRealAppE2E(unittest.TestCase):
    def test_true_app_transaction_rollback_undo_redo_and_normal_close(self):
        real_home = Path(os.environ.get("CALAMUS_REAL_HOME", os.environ.get("HOME", str(Path.home())))).resolve()
        real_config_dir = real_home / ".config" / "calamus"
        real_config_before = snapshot_tree(real_config_dir)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"
            workspace.mkdir()
            document = workspace / "Transaction.md"
            document.write_text("alpha", encoding="utf-8")
            paths = runtime_paths(home)
            write_settings(paths.calamus_config_dir, workspace, document)

            window = None
            with patch.dict(os.environ, runtime_environment(paths), clear=False):
                window = load_app().App(); window.show_all(); pump()
                try:
                    self.assertEqual(window._components.build_order, EXPECTED_ORDER)
                    self.assertIs(window.editor_transaction, window._components.editor_transaction.controller)
                    self.assertIs(window.editor_buffer_adapter, window._components.editor_transaction.buffer_adapter)
                    self.assertFalse(window.restoring_undo)
                    self.assertIsNone(getattr(type(window), "restoring_undo").fset)

                    buffer = window.text.get_buffer()
                    buffer.place_cursor(buffer.get_end_iter())

                    def insert_x(buf):
                        buf.insert(buf.get_end_iter(), "X")
                    self.assertTrue(window.execute_command("Insert X", insert_x))
                    pump()
                    self.assertEqual(buffer_text(window), "alphaX")
                    self.assertEqual(window.document_session.text, "alphaX")
                    self.assertTrue(window.modified)
                    self.assertTrue(window.history.can_undo)

                    window.on_undo(); pump()
                    self.assertEqual(buffer_text(window), "alpha")
                    window.on_redo(); pump()
                    self.assertEqual(buffer_text(window), "alphaX")

                    before_text = buffer_text(window)
                    before_undo = tuple(window.history.undo_stack)
                    before_redo = tuple(window.history.redo_stack)
                    before_session = window.document_session.snapshot()

                    def broken(buf):
                        buf.insert(buf.get_end_iter(), "BROKEN")
                        raise RuntimeError("forced W103 rollback")

                    with self.assertRaisesRegex(RuntimeError, "forced W103 rollback"):
                        window.execute_command("Broken", broken)
                    pump()
                    self.assertEqual(buffer_text(window), before_text)
                    self.assertEqual(tuple(window.history.undo_stack), before_undo)
                    self.assertEqual(tuple(window.history.redo_stack), before_redo)
                    after_session = window.document_session.snapshot()
                    self.assertEqual(after_session.text, before_session.text)
                    self.assertEqual(after_session.modified, before_session.modified)
                    self.assertFalse(window.editor_transaction.programmatic_active)
                    self.assertFalse(window.restoring_undo)

                    window.document_session.mark_clean(buffer_text(window))
                    window.may_continue = lambda: True
                    self.assertTrue(window.request_application_close())
                    pump()
                    self.assertTrue(window.application_lifecycle.is_shutdown)
                    print("W103_EDITOR_TRANSACTION_TRUE_APP=PASS")
                finally:
                    close_visible_dialogs()
                    if window is not None and not window.application_lifecycle.is_shutdown:
                        window.destroy()
                    pump()

        self.assertEqual(real_config_before, snapshot_tree(real_config_dir))
        print("W103_REAL_CONFIG_UNCHANGED=PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
