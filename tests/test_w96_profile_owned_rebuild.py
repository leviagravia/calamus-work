"""Architecture contracts for the independent W96 profile-owned rebuild line."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/calamus_release_test_profiles.json"
RUNNER = ROOT / "scripts/calamus-release-profiles.py"


class W96ProfileOwnedRebuildTests(unittest.TestCase):
    def test_retired_skip_oracles_are_absent(self):
        self.assertFalse((ROOT / "tests/calamus_full_suite_skip_policy.json").exists())
        self.assertFalse((ROOT / "scripts/validate-calamus-unittest-report.py").exists())
        source = RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("approved skip", source.casefold())
        self.assertNotIn("skip reason", source.casefold())

    def test_manifest_declares_zero_skip_release_profiles(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], 1)
        self.assertEqual(
            data["published_baseline"],
            "ca1a9774085d81d087f7a257dbffbbaa858a3889",
        )
        release = {
            name: profile
            for name, profile in data["profiles"].items()
            if profile.get("release_gate")
        }
        self.assertTrue(release)
        for name, profile in release.items():
            self.assertTrue(profile.get("zero_skips"), name)

    def test_headless_core_owns_no_display_or_lane_flags(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        profile = data["profiles"]["headless-core"]
        self.assertIn("DISPLAY", profile["unset_env"])
        self.assertIn("WAYLAND_DISPLAY", profile["unset_env"])
        self.assertEqual(profile["capabilities"], [])
        self.assertGreater(len(profile["test_ids"]), 1000)

    def test_release_profiles_own_noninteractive_terminal_fallback(self):
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn('env.setdefault("TERM", "dumb")', source)

    def test_special_capabilities_have_named_profiles(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        profiles = data["profiles"]
        required = {
            "w97-headless-focused",
            "gio-real",
            "pandoc-real",
            "gtk-components",
            "workspace-e2e-real",
            "w86-w87-real-fixtures",
            "historical-w89-w94",
            "historical-w95extra",
            "historical-w96-product",
            "historical-w97-product",
            "w98-headless-focused",
            "w98-identity-smoke",
            "w98-product-smoke",
            "w99-headless-focused",
            "w99-identity-smoke",
            "w99-lifecycle-smoke",
            "manual-desktop",
        }
        self.assertTrue(required.issubset(profiles))

    def test_release_runner_uses_discovery_only_for_inventory(self):
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("def discover_test_ids", source)
        self.assertIn("loadTestsFromNames", source)
        self.assertIn("if result.skipped", source)
        self.assertNotIn("defaultTestLoader.discover(TEST_DIR)", source)

    def test_inventory_and_profile_imports_use_distinct_processes(self):
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("def validate_inventory_in_subprocess", source)
        self.assertIn('"--inventory"', source)
        self.assertIn("validate_inventory_in_subprocess()", source)
        self.assertNotIn("validate_inventory(data)\n        run_profile(args.run_profile, data)", source)

    def test_mo_anti_recurrence_ledger_is_canonical(self):
        document = ROOT / "docs/canonical/CALAMUS_W96_PROFILE_OWNED_REBUILD_CONTRACT.md"
        text = document.read_text(encoding="utf-8")
        for token in (
            "W96-TEST-TOPOLOGY-01",
            "CALAMUS-CANDIDATE-PREFLIGHT-01",
            "CALAMUS-TEST-SKIP-PROFILE-01",
            "CALAMUS-TEST-PROFILE-OWNERSHIP-01",
            "CALAMUS-PROFILE-IMPORT-STATE-01",
            "CALAMUS-SIMULATED-ENVIRONMENT-EVIDENCE-01",
            "CALAMUS-DOCUMENT-OVERVIEW-CATEGORY-ROW-LIFECYCLE-01",
            "zero skips",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
