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

from tests.calamus_gtk_test_driver import (
    GLib,
    HAVE_GTK,
    close_visible_dialogs,
    display_ready,
    pump,
)


ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("CALAMUS_W99_RUN_REAL_GTK") == "1"
FINAL_OWNERS = (
    "application-sources",
    "navigator-panel",
    "research-panel-view",
    "research-coordinator",
    "document-overview",
    "typewriter",
    "history",
    "viewport",
)


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w99_lifecycle_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W99 GTK lane")
class W99ApplicationLifecycleRealAppE2E(unittest.TestCase):
    def test_normal_close_cancels_app_sources_and_shuts_each_owner_once(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ,
            {
                "HOME": temp,
                "XDG_CONFIG_HOME": temp + "/config",
                "XDG_DATA_HOME": temp + "/data",
                "XDG_CACHE_HOME": temp + "/cache",
            },
            clear=False,
        ):
            window = load_app().App()
            window.show_all()
            pump()
            try:
                lifecycle = window.application_lifecycle
                self.assertEqual(lifecycle.registered_pre_destroy, ("pandoc-export",))
                self.assertEqual(lifecycle.registered_final, FINAL_OWNERS)

                window.word_count_source = GLib.timeout_add(60000, lambda: True)
                window._wrap_reflow_source = GLib.timeout_add(60000, lambda: True)
                window.search_controller.configure("lifecycle")
                self.assertTrue(
                    window.search_controller.schedule_highlight(
                        lambda _delay, callback: GLib.timeout_add(60000, callback)
                    )
                )
                self.assertTrue(window.search_controller.highlight_pending)

                window.may_continue = lambda: True
                self.assertTrue(window.request_application_close())
                pump()

                report = lifecycle.shutdown_report
                self.assertIsNotNone(report)
                self.assertTrue(report.ok)
                self.assertEqual(report.attempted, FINAL_OWNERS)
                self.assertEqual(report.completed, FINAL_OWNERS)
                self.assertEqual(window.word_count_source, None)
                self.assertEqual(window._wrap_reflow_source, None)
                self.assertFalse(window.search_controller.highlight_pending)
                self.assertIs(lifecycle.shutdown(), report)
                print("W99_APPLICATION_LIFECYCLE_TRUE_APP=PASS")
            finally:
                close_visible_dialogs()
                if not window.application_lifecycle.is_shutdown:
                    window.destroy()
                pump()


if __name__ == "__main__":
    unittest.main(verbosity=2)
