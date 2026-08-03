from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "9a80b266cbdb41b499efdb296ff2a312cf85656f"


class W100IdentityGateContractTests(unittest.TestCase):
    def test_current_identity_is_exact(self):
        version = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        for token in (
            'DEVELOPMENT_WORK_ITEM = "W100"',
            'DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Monolith Decomposition Contract"',
            f'PUBLISHED_BASELINE = "{BASELINE}"',
        ):
            self.assertIn(token, version)

    def test_release_manifest_owns_w100_profiles_and_w99_identity_is_not_release_gate(self):
        data = json.loads((ROOT / "tests/calamus_release_test_profiles.json").read_text(encoding="utf-8"))
        self.assertEqual(data["published_baseline"], BASELINE)
        self.assertIn("W100", data["lineage"])
        for profile in ("w100-headless-focused", "w100-identity-smoke"):
            self.assertTrue(data["profiles"][profile]["release_gate"])
        self.assertFalse(data["profiles"]["w99-identity-smoke"]["release_gate"])

    def test_gtk_lane_runs_current_identity_then_historical_lifecycle(self):
        text = (ROOT / "scripts/prove-w100-monolith-contract-gtk-lanes.sh").read_text(encoding="utf-8")
        self.assertLess(text.index("w100-identity-smoke"), text.index("w99-lifecycle-smoke"))
        self.assertIn("W100_CURRENT_IDENTITY_TRUE_APP=PASS", text)
        self.assertIn("W100_MONOLITH_CONTRACT_GTK_LANES=PASS", text)

    def test_release_runner_scrubs_w100_flags(self):
        text = (ROOT / "scripts/calamus-release-profiles.py").read_text(encoding="utf-8")
        self.assertIn('"CALAMUS_W100_"', text)
        self.assertIn(BASELINE, text)


if __name__ == "__main__":
    unittest.main()
