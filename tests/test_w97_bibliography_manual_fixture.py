from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class W97BibliographyManualFixtureTests(unittest.TestCase):
    def test_package_entry_point_builds_complete_isolated_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            home, data, config, cache = (base / name for name in ("home", "data", "config", "cache"))
            for path in (home, data, config, cache):
                path.mkdir(parents=True)
            document = base / "validation/W97_Bibliography_Manager_Core.md"
            env = os.environ.copy()
            env.update(
                HOME=str(home), XDG_DATA_HOME=str(data), XDG_CONFIG_HOME=str(config),
                XDG_CACHE_HOME=str(cache), PYTHONPATH=f"{ROOT / 'calamus'}:{ROOT}",
                PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", TERM="dumb",
            )
            result = subprocess.run(
                [str(ROOT / "scripts/create-w97-bibliography-manual-fixture.sh"), str(document)],
                cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, timeout=60, check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout)
            self.assertIn("W97_BIBLIOGRAPHY_MANUAL_FIXTURE=PASS", result.stdout)
            references = data / "calamus/research/references.md"
            sets = data / "calamus/research/reference-sets.md"
            notes = Path(str(document) + ".source-notes.md")
            local_file = document.parent / "Alpha_Local_File.pdf"
            settings = home / ".config/calamus/settings.json"
            for path in (document, references, sets, notes, local_file, settings):
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 0)
            self.assertTrue(local_file.read_bytes().startswith(b"%PDF-1.4"))
            self.assertEqual(str(document.resolve()), json.loads(settings.read_text())['last_file'])
            text = references.read_text(encoding="utf-8")
            self.assertIn("Custom: Patristics", text)
            self.assertIn("Missing_Gamma_File.pdf", text)


if __name__ == "__main__":
    unittest.main()
