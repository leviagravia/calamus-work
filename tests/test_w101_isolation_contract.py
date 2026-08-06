from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.w101_isolation_helpers import runtime_environment, runtime_paths, snapshot_tree, write_settings

ROOT = Path(__file__).resolve().parents[1]


class W101IsolationContractTests(unittest.TestCase):
    def test_production_resolver_remains_home_dot_config_without_xdg_migration(self):
        source = (ROOT / "calamus/calamus_config.py").read_text(encoding="utf-8")
        self.assertIn('os.path.expanduser("~")', source)
        self.assertIn('".config", "calamus"', source)
        self.assertNotIn("XDG_CONFIG_HOME", source)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            home.mkdir()
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "PYTHONPATH": str(ROOT / "calamus"),
                "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            })
            output = subprocess.check_output(
                [sys.executable, "-c", "import calamus_config; print(calamus_config.CONFIG_DIR)"],
                env=env,
                text=True,
            ).strip()
            self.assertEqual(output, str(home / ".config" / "calamus"))

    def test_isolated_paths_and_fixture_match_the_actual_resolver(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"
            workspace.mkdir()
            paths = runtime_paths(home)
            self.assertEqual(paths.calamus_config_dir, home.resolve() / ".config" / "calamus")
            self.assertEqual(runtime_environment(paths), {
                "HOME": str(home.resolve()),
                "XDG_CONFIG_HOME": str(home.resolve() / ".config"),
                "XDG_DATA_HOME": str(home.resolve() / ".local" / "share"),
                "XDG_CACHE_HOME": str(home.resolve() / ".cache"),
            })
            settings = write_settings(paths.calamus_config_dir, workspace)
            payload = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(payload["workspace_root"], str(workspace.resolve()))

    def test_snapshot_tree_is_read_only_and_change_sensitive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "config"
            root.mkdir()
            target = root / "settings.json"
            target.write_text('{"value": 1}\n', encoding="utf-8")
            before = snapshot_tree(root)
            self.assertEqual(before, snapshot_tree(root))
            target.write_text('{"value": 2}\n', encoding="utf-8")
            self.assertNotEqual(before, snapshot_tree(root))

    def test_true_app_gate_enforces_config_dir_and_real_tree_integrity(self):
        source = (ROOT / "tests/test_w101_core_composition_app_desktop_e2e.py").read_text(encoding="utf-8")
        for token in (
            "real_config_before = snapshot_tree(real_config_dir)",
            "paths = runtime_paths(home)",
            "write_settings(paths.calamus_config_dir, workspace, document)",
            'with patch.dict(os.environ, runtime_environment(paths), clear=False):',
            "self.assertEqual(Path(window.state.config_dir).resolve(), paths.calamus_config_dir)",
            "self.assertEqual(real_config_before, snapshot_tree(real_config_dir))",
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
