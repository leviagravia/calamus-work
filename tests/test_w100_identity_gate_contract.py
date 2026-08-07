from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
W100_BASELINE = "9a80b266cbdb41b499efdb296ff2a312cf85656f"
W101_BASELINE = "fb003223643d9da5f81ddaa3f3e0e4a9304f3903"
W102_BASELINE = "17b409a05f356477173b2bdd348a67a4cf01f43c"
W104_BASELINE = "92aa832c6b72cb7a81a5a44c656890ec602d9d41"


class W100IdentityGateContractTests(unittest.TestCase):
    def test_current_identity_is_exact(self):
        historical = (ROOT / "tests/test_w100_identity_app_desktop_e2e.py").read_text(encoding="utf-8")
        for token in (
            '"W100"',
            '"Monolith Decomposition Contract"',
            W100_BASELINE,
        ):
            self.assertIn(token, historical)
        current = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W105"', current)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Menu and UI-State Decoupling"', current)
        self.assertIn(f'PUBLISHED_BASELINE = "{W104_BASELINE}"', current)

    def test_release_manifest_owns_w100_profiles_and_w99_identity_is_not_release_gate(self):
        data = json.loads((ROOT / "tests/calamus_release_test_profiles.json").read_text(encoding="utf-8"))
        self.assertEqual(data["published_baseline"], W104_BASELINE)
        self.assertIn("W105", data["lineage"])
        self.assertTrue(data["profiles"]["w100-headless-focused"]["release_gate"])
        self.assertFalse(data["profiles"]["w100-identity-smoke"]["release_gate"])
        self.assertFalse(data["profiles"]["w99-identity-smoke"]["release_gate"])

    def test_gtk_lane_runs_current_identity_then_historical_lifecycle(self):
        text = (ROOT / "scripts/prove-w100-monolith-contract-gtk-lanes.sh").read_text(encoding="utf-8")
        self.assertLess(text.index("w100-identity-smoke"), text.index("w99-lifecycle-smoke"))
        self.assertIn("W100_CURRENT_IDENTITY_TRUE_APP=PASS", text)
        self.assertIn("W100_MONOLITH_CONTRACT_GTK_LANES=PASS", text)
        current = (ROOT / "scripts/prove-w101-core-composition-gtk-lanes.sh").read_text(encoding="utf-8")
        self.assertLess(current.index("w101-identity-smoke"), current.index("w101-core-composition-smoke"))
        self.assertLess(current.index("w101-core-composition-smoke"), current.index("w99-lifecycle-smoke"))

    def test_release_runner_scrubs_w100_flags(self):
        text = (ROOT / "scripts/calamus-release-profiles.py").read_text(encoding="utf-8")
        self.assertIn('"CALAMUS_W100_"', text)
        self.assertIn('"CALAMUS_W101_"', text)
        self.assertIn('"CALAMUS_W102_"', text)
        self.assertIn('"CALAMUS_W104_"', text)
        self.assertIn('"CALAMUS_W105_"', text)
        self.assertIn(W104_BASELINE, text)


if __name__ == "__main__":
    unittest.main()
