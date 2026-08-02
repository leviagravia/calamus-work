"""Headless contract for historical/current GTK identity separation."""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class W97IdentityGateContractTests(unittest.TestCase):
    def test_w95_historical_gate_is_not_bound_to_current_identity(self):
        text = (ROOT / "scripts/w95-true-gtk-app-gate.py").read_text(encoding="utf-8")
        self.assertNotIn("DEVELOPMENT_WORK_ITEM", text)
        self.assertNotIn("DEVELOPMENT_WORK_ITEM_DESCRIPTION", text)
        self.assertNotIn("PUBLISHED_BASELINE", text)
        self.assertIn("W95_HISTORICAL_IDENTITY_INDEPENDENT=PASS", text)

    def test_w97_current_identity_gate_is_exact(self):
        text = (ROOT / "tests/test_w97_identity_app_desktop_e2e.py").read_text(encoding="utf-8")
        self.assertIn('EXPECTED_WORK_ITEM = "W97"', text)
        self.assertIn(
            'EXPECTED_DESCRIPTION = "Bibliography Manager Core"', text
        )
        self.assertIn(
            'EXPECTED_BASELINE = "199459fb023e4862407f7eb60318192f276d3239"',
            text,
        )
        self.assertIn("W97_CURRENT_SYSTEM_INFO_EXACT_IDENTITY=PASS", text)

    def test_w97_identity_runs_before_w97_product_gate(self):
        text = (ROOT / "scripts/prove-w97-bibliography-core-gtk-lanes.sh").read_text(
            encoding="utf-8"
        )
        identity = text.index("tests.test_w97_identity_app_desktop_e2e")
        product = text.index("tests.test_w97_bibliography_app_desktop_e2e")
        self.assertLess(identity, product)
        self.assertIn("W97_CURRENT_IDENTITY_TRUE_APP=PASS", text)
        self.assertIn("W97_BIBLIOGRAPHY_MANAGER_CORE_GTK_LANES=PASS", text)

    def test_w95extra_functional_gate_remains_present(self):
        text = (ROOT / "scripts/prove-w95extra-gtk-lanes.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('w95-true-gtk-app-gate.py', text)
        self.assertIn('w95extra-true-gtk-app-gate.py', text)
        self.assertIn('W95EXTRA_GTK_LANES=PASS', text)


if __name__ == "__main__":
    unittest.main()
