"""Exact current W97 runtime identity proof on the real App/GTK dialogs."""
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
RUN_REAL_GTK = os.environ.get("CALAMUS_W97_RUN_REAL_GTK") == "1"
EXPECTED_BUILD_LABEL = "Development build"
EXPECTED_WORK_ITEM = "W97"
EXPECTED_DESCRIPTION = "Bibliography Manager Core"
EXPECTED_BASELINE = "199459fb023e4862407f7eb60318192f276d3239"


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w97_identity_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _set_isolated_config(root: Path) -> None:
    import calamus_config

    config = root / "config" / "calamus"
    calamus_config.CONFIG_DIR = str(config)
    calamus_config.SETTINGS_FILE = str(config / "settings.json")
    calamus_config.RECENT_FILE = str(config / "recent.json")
    calamus_config.FAVOURITES_FILE = str(config / "favourites.json")


def _environment(root: Path) -> dict[str, str]:
    return {
        "HOME": str(root),
        "XDG_DATA_HOME": str(root / "data"),
        "XDG_CONFIG_HOME": str(root / "config"),
    }


def _text(view) -> str:
    buffer = view.get_buffer()
    start, end = buffer.get_bounds()
    return buffer.get_text(start, end, True)


@unittest.skipUnless(
    RUN_REAL_GTK and HAVE_GTK and display_ready(),
    "set CALAMUS_W97_RUN_REAL_GTK=1 on a real GTK desktop",
)
class W97CurrentIdentityRealAppE2E(unittest.TestCase):
    def test_exact_current_identity_and_stable_about(self):
        self.assertEqual(DEVELOPMENT_BUILD_LABEL, EXPECTED_BUILD_LABEL)
        self.assertEqual(DEVELOPMENT_WORK_ITEM, EXPECTED_WORK_ITEM)
        self.assertEqual(DEVELOPMENT_WORK_ITEM_DESCRIPTION, EXPECTED_DESCRIPTION)
        self.assertEqual(PUBLISHED_BASELINE, EXPECTED_BASELINE)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, _environment(root), clear=False):
                _set_isolated_config(root)
                module = _load_app_module()
                win = module.App()
                try:
                    win.show_all()
                    pump()

                    def check_about() -> bool:
                        dialog = visible_dialog("About Calamus")
                        if dialog is None:
                            return False
                        self.assertEqual(dialog.get_name(), "calamus-about-dialog")
                        view = named_widget(dialog, "calamus-about-text", Gtk.TextView)
                        body = _text(view)
                        self.assertEqual(body.splitlines()[0], "Calamus")
                        self.assertNotIn("Calamus-Working-Copy", body)
                        self.assertNotIn(EXPECTED_DESCRIPTION, body)
                        dialog.response(Gtk.ResponseType.CLOSE)
                        return True

                    about_driver = ModalDriver([check_about])
                    about_driver.start()
                    win.on_about()
                    pump()
                    about_driver.assert_complete()

                    def check_system_info() -> bool:
                        dialog = visible_dialog("System Info")
                        if dialog is None:
                            return False
                        self.assertEqual(dialog.get_name(), "calamus-system-info-dialog")
                        view = named_widget(dialog, "calamus-system-info-text", Gtk.TextView)
                        body = _text(view)
                        self.assertIn(f"Calamus: {EXPECTED_BUILD_LABEL}", body)
                        self.assertIn(f"Work item: {EXPECTED_WORK_ITEM}", body)
                        self.assertIn(
                            f"Work item description: {EXPECTED_DESCRIPTION}", body
                        )
                        self.assertIn(
                            f"Published baseline: {EXPECTED_BASELINE}", body
                        )
                        self.assertNotIn("Work item: W95EXTRA", body)
                        dialog.response(Gtk.ResponseType.CLOSE)
                        return True

                    info_driver = ModalDriver([check_system_info])
                    info_driver.start()
                    win.on_system_info()
                    pump()
                    info_driver.assert_complete()

                    print("W97_CURRENT_ABOUT_STABLE_IDENTITY=PASS")
                    print("W97_CURRENT_SYSTEM_INFO_EXACT_IDENTITY=PASS")
                    print("W97_CURRENT_IDENTITY_DIALOG_OWNERSHIP=PASS")
                finally:
                    close_visible_dialogs()
                    win.destroy()
                    pump()


if __name__ == "__main__":
    unittest.main(verbosity=2)
