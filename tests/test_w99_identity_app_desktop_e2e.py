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

from calamus_version import (
    DEVELOPMENT_BUILD_LABEL,
    DEVELOPMENT_WORK_ITEM,
    DEVELOPMENT_WORK_ITEM_DESCRIPTION,
    PUBLISHED_BASELINE,
)
from tests.calamus_gtk_test_driver import (
    HAVE_GTK,
    Gtk,
    ModalDriver,
    close_visible_dialogs,
    display_ready,
    named_widget,
    pump,
    visible_dialog,
)


ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("CALAMUS_W99_RUN_REAL_GTK") == "1"
EXPECTED = (
    "Development build",
    "W99",
    "Retrospective GTK-free and Lifecycle Audit",
    "fb54cd3bb96bbea024966db2a059c755aef45d95",
)


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w99_identity_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def text_view_body(view):
    buffer = view.get_buffer()
    start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W99 GTK lane")
class W99IdentityRealAppE2E(unittest.TestCase):
    def test_exact_current_identity_and_stable_about(self):
        self.assertEqual(
            EXPECTED,
            (
                DEVELOPMENT_BUILD_LABEL,
                DEVELOPMENT_WORK_ITEM,
                DEVELOPMENT_WORK_ITEM_DESCRIPTION,
                PUBLISHED_BASELINE,
            ),
        )
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
                def close_about():
                    dialog = visible_dialog("About Calamus")
                    if dialog is None:
                        return False
                    body = text_view_body(named_widget(dialog, "calamus-about-text", Gtk.TextView))
                    self.assertEqual(body.splitlines()[0], "Calamus")
                    self.assertNotIn(EXPECTED[2], body)
                    dialog.response(Gtk.ResponseType.CLOSE)
                    return True

                driver = ModalDriver([close_about])
                driver.start()
                window.on_about()
                pump()
                driver.assert_complete()

                def close_system_info():
                    dialog = visible_dialog("System Info")
                    if dialog is None:
                        return False
                    body = text_view_body(
                        named_widget(dialog, "calamus-system-info-text", Gtk.TextView)
                    )
                    for line in (
                        f"Calamus: {EXPECTED[0]}",
                        f"Work item: {EXPECTED[1]}",
                        f"Work item description: {EXPECTED[2]}",
                        f"Published baseline: {EXPECTED[3]}",
                    ):
                        self.assertIn(line, body)
                    dialog.response(Gtk.ResponseType.CLOSE)
                    return True

                driver = ModalDriver([close_system_info])
                driver.start()
                window.on_system_info()
                pump()
                driver.assert_complete()
                print("W99_CURRENT_IDENTITY=PASS")
            finally:
                close_visible_dialogs()
                if not window.application_lifecycle.is_shutdown:
                    window.destroy()
                pump()


if __name__ == "__main__":
    unittest.main(verbosity=2)
