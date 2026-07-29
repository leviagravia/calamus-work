from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class W94GtkGateContractTests(unittest.TestCase):
    def test_diagnostic_scanner_accepts_clean_log_and_rejects_blocking_log(self) -> None:
        result = subprocess.run(
            ["bash", str(ROOT / "scripts" / "prove-w94-gtk-lanes.sh"), "--self-test-diagnostics"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("W94_GTK_DIAGNOSTIC_SCANNER_CLEAN=PASS", result.stdout)
        self.assertIn("W94_GTK_DIAGNOSTIC_SCANNER_BLOCKED=PASS", result.stdout)
        self.assertIn("W94_GTK_DIAGNOSTIC_SCANNER_SELFTEST=PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
