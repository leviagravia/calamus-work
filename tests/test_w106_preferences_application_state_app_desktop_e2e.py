from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

from tests.calamus_gtk_test_driver import HAVE_GTK, display_ready, pump
from tests.w101_isolation_helpers import runtime_environment, runtime_paths, snapshot_tree

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("CALAMUS_W106_RUN_REAL_GTK") == "1"


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w106_preferences_state_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def read_settings(config_dir: Path) -> dict:
    return json.loads((config_dir / "settings.json").read_text(encoding="utf-8"))


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W106 preferences/application-state GTK lane")
class W106PreferencesApplicationStateRealAppE2E(unittest.TestCase):
    def test_true_app_typed_persistence_domain_separation_restart_and_normal_close(self):
        real_home = Path(os.environ.get("CALAMUS_REAL_HOME", os.environ.get("HOME", str(Path.home())))).resolve()
        real_config_dir = real_home / ".config" / "calamus"
        real_before = snapshot_tree(real_config_dir)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"
            workspace.mkdir()
            document = workspace / "Preferences.md"
            document.write_text("# W106 Preferences\n\nalpha beta gamma\n", encoding="utf-8")
            missing_recent = workspace / "temporarily-missing.md"
            paths = runtime_paths(home)
            paths.calamus_config_dir.mkdir(parents=True, exist_ok=True)
            settings_path = paths.calamus_config_dir / "settings.json"
            settings_path.write_text(json.dumps({
                "width": 920,
                "height": 660,
                "last_file": str(document),
                "workspace_root": str(workspace),
                "workspace_visible": "false",
                "font_family": "Monospace",
                "font_size": 13,
                "word_wrap": "false",
                "spell_lang": "it",
                "inline_spell": True,
                "always_on_top": "false",
                "appearance_mode": "light",
                "white_background": True,
                "dark_mode": False,
                "opacity": 88,
                "line_numbers": False,
                "trim_trailing_on_save": "false",
            }, indent=2) + "\n", encoding="utf-8")
            (paths.calamus_config_dir / "recent.json").write_text(
                json.dumps([str(missing_recent), str(document)], indent=2) + "\n", encoding="utf-8"
            )

            env = runtime_environment(paths)
            env["CALAMUS_REAL_HOME"] = str(real_home)
            with patch.dict(os.environ, env, clear=False):
                module = load_app()
                window = module.App(); window.show_all(); pump()
                try:
                    # Malformed strings do not become truthy.  Existing typed defaults win.
                    self.assertTrue(window.word_wrap)
                    self.assertFalse(window.always_on_top)
                    self.assertFalse(window.trim_trailing_on_save)
                    self.assertFalse(window.workspace_visible)
                    self.assertEqual(window.font_family, "Monospace")
                    self.assertEqual(window.font_size, 13)
                    self.assertEqual(window.opacity_percent, 88)
                    self.assertFalse(window.line_numbers_enabled)
                    self.assertEqual(window.current_file, str(document))

                    before_app = window.persisted_application_state
                    self.assertTrue(window.update_preferences(word_wrap=False, font_size=14))
                    after_pref = read_settings(paths.calamus_config_dir)
                    self.assertFalse(after_pref["word_wrap"])
                    self.assertEqual(after_pref["font_size"], 14)
                    self.assertEqual(after_pref["last_file"], before_app.last_file)
                    self.assertEqual(after_pref["workspace_root"], before_app.workspace_root)
                    self.assertEqual(after_pref["workspace_visible"], before_app.workspace_visible)
                    self.assertEqual(after_pref["width"], before_app.width)
                    self.assertEqual(after_pref["height"], before_app.height)

                    # Application-state update preserves the exact preference snapshot.
                    pref_before_state = window.preference_snapshot
                    self.assertTrue(window.application_state.record_workspace_visible(True))
                    self.assertEqual(window.preference_snapshot, pref_before_state)
                    after_state = read_settings(paths.calamus_config_dir)
                    self.assertTrue(after_state["workspace_visible"])
                    self.assertFalse(after_state["word_wrap"])
                    self.assertEqual(after_state["font_size"], 14)

                    # Canonical recent identity survives temporary filesystem unavailability.
                    self.assertIn(str(missing_recent.resolve()), window.recent_file_store.canonical())
                    another = workspace / "Another.md"; another.write_text("another\n", encoding="utf-8")
                    window.recent_file_store.add(str(another))
                    self.assertIn(str(missing_recent.resolve()), window.recent_file_store.canonical())
                    self.assertNotIn(str(missing_recent.resolve()), window.recent_file_store.visible())

                    # Close is clean and explicitly records application state.
                    self.assertTrue(window.request_application_close()); pump()
                    window = None

                    # Restart the same isolated XDG: persisted preference/state authorities restore.
                    restarted = module.App(); restarted.show_all(); pump()
                    try:
                        self.assertFalse(restarted.word_wrap)
                        self.assertEqual(restarted.font_size, 14)
                        self.assertTrue(restarted.persisted_application_state.workspace_visible)
                        self.assertEqual(restarted.persisted_application_state.last_file, str(document))
                        self.assertEqual(restarted.persisted_application_state.workspace_root, str(workspace))
                        self.assertIn(str(missing_recent.resolve()), restarted.recent_file_store.canonical())
                        print("W106_PREFERENCES_APPLICATION_STATE_TRUE_APP=PASS")
                    finally:
                        restarted.destroy(); pump()
                finally:
                    if window is not None:
                        window.destroy(); pump()

        self.assertEqual(real_before, snapshot_tree(real_config_dir))
        print("W106_REAL_CONFIG_UNCHANGED=PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
