"""Headless contract for historical/current GTK identity separation."""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class W96IdentityGateContractTests(unittest.TestCase):
    def test_w95_historical_gate_is_not_bound_to_current_identity(self):
        text = (ROOT / "scripts/w95-true-gtk-app-gate.py").read_text(encoding="utf-8")
        self.assertNotIn("DEVELOPMENT_WORK_ITEM", text)
        self.assertNotIn("DEVELOPMENT_WORK_ITEM_DESCRIPTION", text)
        self.assertNotIn("PUBLISHED_BASELINE", text)
        self.assertIn("W95_HISTORICAL_IDENTITY_INDEPENDENT=PASS", text)

    def test_w96_current_identity_gate_is_exact(self):
        text = (ROOT / "tests/test_w96_identity_app_desktop_e2e.py").read_text(encoding="utf-8")
        self.assertIn('EXPECTED_WORK_ITEM = "W96"', text)
        self.assertIn(
            'EXPECTED_DESCRIPTION = "Document Overview Core — Gate C"', text
        )
        self.assertIn(
            'EXPECTED_BASELINE = "792ca0f76db39525a9052bd61e43fe929988af2e"',
            text,
        )
        self.assertIn("W96_CURRENT_SYSTEM_INFO_EXACT_IDENTITY=PASS", text)

    def test_w96_identity_runs_before_w96_product_gate(self):
        text = (ROOT / "scripts/prove-w96-core-gate-c-gtk-lanes.sh").read_text(
            encoding="utf-8"
        )
        identity = text.index("tests.test_w96_identity_app_desktop_e2e")
        product = text.index("tests.test_w96_document_overview_app_desktop_e2e")
        self.assertLess(identity, product)
        self.assertIn("W96_CURRENT_IDENTITY_TRUE_APP=PASS", text)

    def test_w95extra_functional_gate_remains_present(self):
        text = (ROOT / "scripts/prove-w95extra-gtk-lanes.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('w95-true-gtk-app-gate.py', text)
        self.assertIn('w95extra-true-gtk-app-gate.py', text)
        self.assertIn('W95EXTRA_GTK_LANES=PASS', text)


if __name__ == "__main__":
    unittest.main()
