"""Independent true-App/GTK smoke lane for W89 runtime identity dialogs."""
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

from calamus_gtk_test_driver import (
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
RUN_REAL_GTK = os.environ.get("CALAMUS_W89_RUN_IDENTITY_GTK") == "1"


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w89_identity_{uuid.uuid4().hex}"
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
    "set CALAMUS_W89_RUN_IDENTITY_GTK=1 on a real GTK desktop",
)
class W89IdentityRealAppE2E(unittest.TestCase):
    def test_real_about_and_system_info_owned_identity(self):
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
                        view = named_widget(
                            dialog,
                            "calamus-about-text",
                            Gtk.TextView,
                        )
                        body = _text(view)
                        self.assertEqual(body.splitlines()[0], "Calamus")
                        self.assertNotIn("Calamus-Working-Copy", body)
                        dialog.response(Gtk.ResponseType.CLOSE)
                        return True

                    about_driver = ModalDriver([check_about])
                    about_driver.start()
                    win.on_about()
                    pump()
                    about_driver.assert_complete()
                    self.assertIsNone(visible_dialog("About Calamus"))

                    def check_system_info() -> bool:
                        dialog = visible_dialog("System Info")
                        if dialog is None:
                            return False
                        self.assertEqual(
                            dialog.get_name(),
                            "calamus-system-info-dialog",
                        )
                        view = named_widget(
                            dialog,
                            "calamus-system-info-text",
                            Gtk.TextView,
                        )
                        body = _text(view)
                        self.assertIn("Calamus: Development build", body)
                        self.assertIn("Work item: W89", body)
                        self.assertIn(
                            "Published baseline: "
                            "569dd742abd607bb55a1e6bf9efbad1fdba1684c",
                            body,
                        )
                        self.assertNotIn("Calamus: 1.7.0", body)
                        dialog.response(Gtk.ResponseType.CLOSE)
                        return True

                    info_driver = ModalDriver([check_system_info])
                    info_driver.start()
                    win.on_system_info()
                    pump()
                    info_driver.assert_complete()
                    self.assertIsNone(visible_dialog("System Info"))
                    print("W89_REAL_ABOUT_IDENTITY=PASS")
                    print("W89_REAL_SYSTEM_INFO_IDENTITY=PASS")
                    print("W89_REAL_IDENTITY_DIALOG_OWNERSHIP=PASS")
                finally:
                    close_visible_dialogs()
                    win.destroy()
                    pump()


if __name__ == "__main__":
    unittest.main(verbosity=2)
