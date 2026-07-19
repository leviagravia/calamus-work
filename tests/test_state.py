import os
import tempfile
import unittest

from calamus_state import StateManager


class StateManagerTests(unittest.TestCase):
    def test_settings_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            state = StateManager(td)
            self.assertTrue(state.save_settings({"font_size": 12}))
            self.assertEqual(state.load_settings()["font_size"], 12)

    def test_legacy_session_file_is_left_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            legacy = os.path.join(td, "session.json")
            payload = '{"legacy": true}\n'
            with open(legacy, "w", encoding="utf-8") as handle:
                handle.write(payload)
            StateManager(td)
            with open(legacy, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), payload)

    def test_recent_and_favourites_are_deduped_existing_paths(self):
        with tempfile.TemporaryDirectory() as td:
            state = StateManager(td)
            existing = os.path.join(td, "note.txt")
            with open(existing, "w", encoding="utf-8"):
                pass
            state.add_recent_file(existing)
            state.add_recent_file(existing)
            self.assertEqual(state.load_recent_files(), [os.path.abspath(existing)])
            self.assertTrue(state.save_favourites([existing, existing, os.path.join(td, "missing")]))
            self.assertEqual(state.load_favourites(), [os.path.abspath(existing)])

    def test_clips_roundtrip_through_state(self):
        with tempfile.TemporaryDirectory() as td:
            state = StateManager(td)
            self.assertTrue(state.save_clips([{"title": "A", "text": "Body", "created": ""}]))
            self.assertEqual(state.load_clips()[0]["text"], "Body")
            self.assertTrue(state.templates_dir.endswith("templates"))


if __name__ == "__main__":
    unittest.main()

class StateRegressionExtraTests(unittest.TestCase):
    def test_bad_json_falls_back_safely(self):
        with tempfile.TemporaryDirectory() as td:
            state = StateManager(td)
            with open(state.settings_file, "w", encoding="utf-8") as f:
                f.write("{broken")
            self.assertIsInstance(state.load_settings(), dict)

    def test_templates_directory_is_created(self):
        with tempfile.TemporaryDirectory() as td:
            state = StateManager(td)
            self.assertTrue(os.path.isdir(state.templates_dir))
