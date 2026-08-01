from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class W96ManualFixtureTests(unittest.TestCase):
    def test_package_entry_point_builds_complete_isolated_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            data = base / "data"
            config = base / "config"
            cache = base / "cache"
            for path in (home, data, config, cache):
                path.mkdir(parents=True)
            document = base / "validation" / "W96.md"
            env = os.environ.copy()
            env.update(
                HOME=str(home),
                XDG_DATA_HOME=str(data),
                XDG_CONFIG_HOME=str(config),
                XDG_CACHE_HOME=str(cache),
                PYTHONPATH=f"{ROOT / 'calamus'}:{ROOT}",
                PYTHONNOUSERSITE="1",
                PYTHONDONTWRITEBYTECODE="1",
            )
            completed = subprocess.run(
                [str(ROOT / "scripts/create-w96-manual-fixture.sh"), str(document)],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stdout)
            self.assertIn("W96_MANUAL_FIXTURE_GENERATOR=PASS", completed.stdout)
            references = data / "calamus/research/references.md"
            sets = data / "calamus/research/reference-sets.md"
            notes = Path(str(document) + ".source-notes.md")
            settings = home / ".config/calamus/settings.json"
            for path in (document, references, sets, notes, settings):
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 0)
            self.assertEqual(str(document.resolve()), json.loads(settings.read_text())["last_file"])


if __name__ == "__main__":
    unittest.main()
