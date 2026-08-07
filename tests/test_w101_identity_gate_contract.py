from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
W101_BASELINE = "fb003223643d9da5f81ddaa3f3e0e4a9304f3903"
W102_BASELINE = "17b409a05f356477173b2bdd348a67a4cf01f43c"


class W101IdentityGateContractTests(unittest.TestCase):
    def test_current_identity_is_exact(self):
        current = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        for token in (
            'DEVELOPMENT_BUILD_LABEL = "Development build"',
            'DEVELOPMENT_WORK_ITEM = "W102"',
            'DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Document Session Extraction"',
            f'PUBLISHED_BASELINE = "{W102_BASELINE}"',
        ):
            self.assertIn(token, current)

    def test_release_manifest_owns_current_profiles_and_historical_identity_is_not_release(self):
        data = json.loads((ROOT / "tests/calamus_release_test_profiles.json").read_text(encoding="utf-8"))
        self.assertEqual(data["published_baseline"], W102_BASELINE)
        self.assertEqual(data["lineage"], "W102 Document Session Extraction Candidate R1")
        for profile in ("w102-headless-focused", "w102-identity-smoke", "w102-document-session-smoke"):
            self.assertIn(profile, data["profiles"])
            self.assertTrue(data["profiles"][profile]["release_gate"])
        self.assertTrue(data["profiles"]["w101-headless-focused"]["release_gate"])
        self.assertTrue(data["profiles"]["w101-core-composition-smoke"]["release_gate"])
        self.assertFalse(data["profiles"]["w101-identity-smoke"]["release_gate"])
        self.assertFalse(data["profiles"]["w100-identity-smoke"]["release_gate"])
        self.assertFalse(data["profiles"]["w99-identity-smoke"]["release_gate"])

        rebuild = (ROOT / "docs/canonical/CALAMUS_W101_ISOLATION_CONTRACT_REBUILD.md").read_text(encoding="utf-8")
        for token in (
            "Isolation-Contract Rebuild Candidate R1",
            "Candidate R1 and Candidate R2 are retired",
            "`$HOME/.config/calamus/settings.json`",
            "The user's real `$HOME/.config/calamus` is snapshotted read-only",
            "No production persistence resolver or migration is changed in W101",
        ):
            self.assertIn(token, rebuild)

    def test_gtk_lane_order_is_current_then_product_then_historical_lifecycle(self):
        text = (ROOT / "scripts/prove-w101-core-composition-gtk-lanes.sh").read_text(encoding="utf-8")
        order = (
            "w101-identity-smoke",
            "w101-core-composition-smoke",
            "w99-lifecycle-smoke",
            "w98-product-smoke",
        )
        positions = [text.index(item) for item in order]
        self.assertEqual(positions, sorted(positions))
        for marker in (
            "W101_CURRENT_IDENTITY_TRUE_APP=PASS",
            "W101_CORE_COMPOSITION_TRUE_APP=PASS",
            "W101_HISTORICAL_W99_LIFECYCLE=PASS",
            "W101_HISTORICAL_W98_RESEARCH=PASS",
            "W101_CORE_COMPOSITION_GTK_LANES=PASS",
        ):
            self.assertIn(marker, text)

    def test_headless_lane_runs_current_then_w100_w99_and_w98(self):
        text = (ROOT / "scripts/prove-w101-core-composition-headless.sh").read_text(encoding="utf-8")
        profiles = (
            "w101-headless-focused",
            "w100-headless-focused",
            "w99-headless-focused",
            "w98-headless-focused",
        )
        positions = [text.index(item) for item in profiles]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("W101_CORE_COMPOSITION_HEADLESS=PASS", text)

    def test_release_runner_scrubs_w101_flags_and_requires_current_baseline(self):
        text = (ROOT / "scripts/calamus-release-profiles.py").read_text(encoding="utf-8")
        self.assertIn('"CALAMUS_W101_"', text)
        self.assertIn(W102_BASELINE, text)

        provenance = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
        contract_position = provenance.index('gi.require_version(namespace, version)')
        module_inventory_position = provenance.index('modules = [')
        import_loop_position = provenance.index('for name in modules:')
        self.assertLess(contract_position, module_inventory_position)
        self.assertLess(module_inventory_position, import_loop_position)
        for token in (
            '("Gtk", "3.0")',
            '("Gdk", "3.0")',
            '("Pango", "1.0")',
            '("PangoCairo", "1.0")',
            'SOURCE_PROVENANCE_GTK_CONTRACT=GTK3',
        ):
            self.assertIn(token, provenance)


if __name__ == "__main__":
    unittest.main()
