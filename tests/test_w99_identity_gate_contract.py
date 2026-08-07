"""Historical W99 identity/lifecycle gate contract under current W100 identity."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
W99_BASELINE = "fb54cd3bb96bbea024966db2a059c755aef45d95"
CURRENT_BASELINE = "aa73cc830b2c2120e26fd7ffb5d21b56c95e709b"


class W99IdentityGateContractTests(unittest.TestCase):
    def test_w99_identity_oracle_is_preserved_but_not_a_current_release_gate(self):
        text = (ROOT / "tests/test_w99_identity_app_desktop_e2e.py").read_text(encoding="utf-8")
        for token in ('"W99"', '"Retrospective GTK-free and Lifecycle Audit"', f'"{W99_BASELINE}"', 'print("W99_CURRENT_IDENTITY=PASS")'):
            self.assertIn(token, text)
        data = json.loads((ROOT / "tests/calamus_release_test_profiles.json").read_text(encoding="utf-8"))
        self.assertFalse(data["profiles"]["w99-identity-smoke"]["release_gate"])

    def test_w99_lifecycle_remains_a_historical_release_gate(self):
        data = json.loads((ROOT / "tests/calamus_release_test_profiles.json").read_text(encoding="utf-8"))
        self.assertTrue(data["profiles"]["w99-lifecycle-smoke"]["release_gate"])
        self.assertEqual(data["published_baseline"], CURRENT_BASELINE)

    def test_w99_script_retains_historical_lane_order(self):
        text = (ROOT / "scripts/prove-w99-retrospective-gtk-lanes.sh").read_text(encoding="utf-8")
        self.assertLess(text.index("w99-identity-smoke"), text.index("w99-lifecycle-smoke"))
        self.assertIn("W99_RETROSPECTIVE_GTK_LANES=PASS", text)


if __name__ == "__main__":
    unittest.main()
