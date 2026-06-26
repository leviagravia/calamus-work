import os
import tempfile
import unittest
from unittest import mock

import calamus_config as cfg


class ConfigTests(unittest.TestCase):
    def test_clamp_int_bounds_and_default(self):
        self.assertEqual(cfg.clamp_int("7", 0, 1, 5), 5)
        self.assertEqual(cfg.clamp_int("bad", 3, 1, 5), 3)
        self.assertEqual(cfg.clamp_int(-2, 0, 1, 5), 1)

    def test_json_roundtrip_and_bad_json_default(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "settings.json")
            self.assertTrue(cfg.save_json_file(path, {"font": "Monospace 11"}))
            self.assertEqual(cfg.load_json_file(path, {}), {"font": "Monospace 11"})
            with open(path, "w", encoding="utf-8") as f:
                f.write("{broken")
            self.assertEqual(cfg.load_json_file(path, {"safe": True}), {"safe": True})

    def test_recent_files_are_absolute_unique_and_existing(self):
        with tempfile.TemporaryDirectory() as td:
            recent = os.path.join(td, "recent.json")
            existing = os.path.join(td, "note.txt")
            with open(existing, "w", encoding="utf-8"):
                pass
            with mock.patch.object(cfg, "RECENT_FILE", recent):
                items = cfg.add_recent_file(existing)
                items = cfg.add_recent_file(existing)
            self.assertEqual(items, [os.path.abspath(existing)])


if __name__ == "__main__":
    unittest.main()
