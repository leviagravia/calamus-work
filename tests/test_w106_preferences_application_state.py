import json
import os
import tempfile
from pathlib import Path
import unittest
from unittest import mock

from calamus_application_state import ApplicationStateSnapshot, decode_application_state
from calamus_persistent_collections import RecentFileStore
from calamus_preferences import PreferencesSnapshot, decode_preferences
from calamus_preferences_controller import PreferenceProjectionError, PreferencesController
from calamus_settings_repository import SettingsCodec, SettingsRepository


class W106PreferencesApplicationStateTests(unittest.TestCase):
    def test_strict_persisted_booleans_do_not_truthify_strings(self):
        prefs = decode_preferences({
            "always_on_top": "false",
            "trim_trailing_on_save": "true",
        })
        app = decode_application_state({"workspace_visible": "false"})
        self.assertFalse(prefs.always_on_top)
        self.assertFalse(prefs.trim_trailing_on_save)
        self.assertFalse(app.workspace_visible)

    def test_codec_separates_preferences_from_application_state(self):
        snap = SettingsCodec.decode({
            "font_family": "Serif",
            "font_size": 14,
            "word_wrap": False,
            "width": 1024,
            "height": 720,
            "last_file": "/tmp/note.md",
            "workspace_visible": True,
        })
        self.assertEqual(snap.preferences.font_family, "Serif")
        self.assertFalse(snap.preferences.word_wrap)
        self.assertEqual(snap.application_state.width, 1024)
        self.assertEqual(snap.application_state.last_file, "/tmp/note.md")
        self.assertTrue(snap.application_state.workspace_visible)

    def test_preference_update_preserves_application_state_exactly(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SettingsRepository(td)
            self.assertTrue(repo.update_application_state(ApplicationStateSnapshot(
                width=1010, height=701, last_file="/tmp/a.md",
                workspace_root="/tmp/work", workspace_visible=True,
            )))
            before = repo.snapshot.application_state
            requested = repo.snapshot.preferences.updated(word_wrap=False, font_size=15)
            self.assertTrue(repo.update_preferences(requested))
            self.assertEqual(repo.snapshot.application_state, before)
            payload = json.loads(Path(repo.settings_file).read_text(encoding="utf-8"))
            self.assertEqual(payload["width"], 1010)
            self.assertEqual(payload["last_file"], "/tmp/a.md")

    def test_application_state_update_preserves_preferences_exactly(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SettingsRepository(td)
            requested = repo.snapshot.preferences.updated(font_family="Serif", opacity_percent=90)
            self.assertTrue(repo.update_preferences(requested))
            before = repo.snapshot.preferences
            self.assertTrue(repo.update_application_state(repo.snapshot.application_state.updated(last_file="/tmp/b.md")))
            self.assertEqual(repo.snapshot.preferences, before)

    def test_repository_does_not_advance_snapshot_on_write_failure(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SettingsRepository(td)
            before = repo.snapshot
            with mock.patch("calamus_settings_repository.save_json_file", return_value=False):
                self.assertFalse(repo.update_preferences(before.preferences.updated(word_wrap=False)))
            self.assertEqual(repo.snapshot, before)

    def test_projection_failure_rolls_back_file_and_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SettingsRepository(td)
            controller = PreferencesController(repo)
            before = controller.current
            calls = []
            def project(snapshot):
                calls.append(snapshot.word_wrap)
                if snapshot.word_wrap is False:
                    raise RuntimeError("GTK projection failed")
            with self.assertRaises(PreferenceProjectionError):
                controller.update(word_wrap=False, project=project)
            self.assertEqual(controller.current, before)
            self.assertEqual(calls, [False, True])
            loaded = SettingsCodec.decode(json.loads(Path(repo.settings_file).read_text(encoding="utf-8")))
            self.assertEqual(loaded.preferences, before)

    def test_recent_add_preserves_temporarily_missing_canonical_path(self):
        with tempfile.TemporaryDirectory() as td:
            store = RecentFileStore(td)
            missing = os.path.join(td, "temporarily-missing.md")
            existing = os.path.join(td, "new.md")
            Path(existing).write_text("", encoding="utf-8")
            self.assertTrue(store.save([missing]))
            store.add(existing)
            self.assertEqual(store.canonical(), [existing, missing])
            self.assertEqual(store.visible(), [existing])

    def test_settings_encode_retains_legacy_appearance_keys(self):
        snap = SettingsCodec.decode({"appearance_mode": "dark"})
        encoded = SettingsCodec.encode(snap)
        self.assertEqual(encoded["appearance_mode"], "dark")
        self.assertFalse(encoded["white_background"])
        self.assertTrue(encoded["dark_mode"])
        self.assertFalse(encoded["inline_spell"])


if __name__ == "__main__":
    unittest.main()
