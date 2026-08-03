"""Headless gate contract for the W99 current identity and GTK lane order."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "fb54cd3bb96bbea024966db2a059c755aef45d95"


class W99IdentityGateContractTests(unittest.TestCase):
    def test_w99_current_identity_gate_is_exact(self):
        text = (ROOT / "tests" / "test_w99_identity_app_desktop_e2e.py").read_text(
            encoding="utf-8"
        )
        for token in (
            '"W99"',
            '"Retrospective GTK-free and Lifecycle Audit"',
            f'"{BASELINE}"',
            'print("W99_CURRENT_IDENTITY=PASS")',
        ):
            self.assertIn(token, text)

    def test_w99_identity_precedes_lifecycle_true_app_gate(self):
        text = (ROOT / "scripts" / "prove-w99-retrospective-gtk-lanes.sh").read_text(
            encoding="utf-8"
        )
        self.assertLess(text.index("w99-identity-smoke"), text.index("w99-lifecycle-smoke"))
        self.assertIn("W99_CURRENT_IDENTITY_TRUE_APP=PASS", text)
        self.assertIn("W99_RETROSPECTIVE_GTK_LANES=PASS", text)

    def test_release_manifest_owns_w99_baseline_and_profiles(self):
        data = json.loads(
            (ROOT / "tests" / "calamus_release_test_profiles.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(data["published_baseline"], BASELINE)
        self.assertIn("W99", data["lineage"])
        for profile in (
            "w99-headless-focused",
            "w99-identity-smoke",
            "w99-lifecycle-smoke",
        ):
            self.assertIn(profile, data["profiles"])

    def test_release_runner_scrubs_and_owns_w99_lane_flags(self):
        text = (ROOT / "scripts" / "calamus-release-profiles.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"CALAMUS_W99_"', text)
        self.assertIn(BASELINE, text)


if __name__ == "__main__":
    unittest.main()
