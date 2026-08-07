from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "9a80b266cbdb41b499efdb296ff2a312cf85656f"


class W100MonolithDecompositionContractTests(unittest.TestCase):
    def setUp(self):
        self.launcher_path = ROOT / "bin" / "calamus"
        self.launcher = self.launcher_path.read_text(encoding="utf-8")
        self.tree = ast.parse(self.launcher)
        self.app = next(n for n in self.tree.body if isinstance(n, ast.ClassDef) and n.name == "App")
        self.methods = [n for n in self.app.body if isinstance(n, ast.FunctionDef)]

    def load(self, name):
        return json.loads((ROOT / "docs" / "canonical" / name).read_text(encoding="utf-8"))

    def test_baseline_metrics_are_exact_and_growth_is_blocked(self):
        metrics = self.load("CALAMUS_W100_BASELINE_METRICS.json")
        self.assertEqual(metrics["baseline_commit"], BASELINE)
        self.assertEqual(metrics["launcher_lines"], 3298)
        self.assertEqual(metrics["app_lines"], 3066)
        self.assertEqual(metrics["app_method_count"], 266)
        self.assertEqual(metrics["unique_calamus_import_modules"], 92)
        self.assertEqual(metrics["assigned_self_attribute_count"], 94)
        self.assertEqual(metrics["calamus_ui_unique_app_attributes"], 156)
        # W101 supersedes the frozen W100 ceilings only by decreasing the
        # launcher/App surface through the accepted composition extraction.
        self.assertLess(len(self.launcher.splitlines()), metrics["launcher_lines"])
        self.assertLess(self.app.end_lineno - self.app.lineno + 1, metrics["app_lines"])
        # W101-W105 may add bounded compatibility gateways while preserving
        # strict launcher/App line-count reduction from the W100 monolith.
        self.assertEqual(len(self.methods), 295)
        method_names = {node.name for node in self.methods}
        for name in (
            "document", "current_file", "modified", "loading",
            "_read_buffer_text_raw", "_replace_buffer_text_raw",
            "finalize_open_transition", "restoring_undo",
            "_invalidate_editor_views", "_project_committed_editor_change",
            "_project_history_restore",
        ):
            self.assertIn(name, method_names)
        self.assertLess(len(self.launcher.splitlines()), metrics["launcher_lines"])

    def test_every_app_method_is_assigned_once(self):
        data = self.load("CALAMUS_W100_APP_METHOD_RESPONSIBILITY_INVENTORY.json")
        records = data["methods"]
        names = [r["name"] for r in records]
        self.assertEqual(len(names), 266)
        self.assertEqual(len(names), len(set(names)))
        allowed = {f"W{i}" for i in range(101, 109)}
        for record in records:
            self.assertIn(record["migration_work_item"], allowed)
            self.assertNotIn("UNASSIGNED", json.dumps(record))
            if record["command_surface_review"] is not None:
                self.assertEqual(record["command_surface_review"], "W104")
        self.assertIn("build_clip_collection", names)
        self.assertNotIn("build_clip_collection", {m.name for m in self.methods})

    def test_every_assigned_app_attribute_is_assigned_once(self):
        data = self.load("CALAMUS_W100_APP_ATTRIBUTE_RESPONSIBILITY_INVENTORY.json")
        records = data["attributes"]
        names = [r["name"] for r in records]
        self.assertEqual(len(names), 94)
        self.assertEqual(len(names), len(set(names)))
        for record in records:
            self.assertRegex(record["migration_work_item"], r"^W10[1-8]$")
        self.assertIn("workspace_controller", names)
        self.assertIn("research_coordinator", names)

    def test_whole_app_coupling_inventory_is_exact(self):
        data = self.load("CALAMUS_W100_WHOLE_APP_COUPLING_INVENTORY.json")
        records = data["couplings"]
        actual = {(r["path"], r["function"], r["start_line"]) for r in records}
        self.assertEqual(len(records), 35)
        self.assertEqual(len(actual), 35)
        self.assertTrue(all(r["migration_work_item"] in {"W105", "W107"} for r in records))
        # W101 added the root entry. W104 added explicit application-bound
        # command/UI adapters; W105 removes the old check-menu compatibility
        # entry while command/UI-state cores themselves remain App-free.
        current = []
        for path in sorted((ROOT / "calamus").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                args = [a.arg for a in node.args.args + node.args.kwonlyargs]
                if "app" in args:
                    current.append((path.name, node.name))
        self.assertEqual(len(current), 39)
        w104_entries = {item for item in current if item in {
            ("calamus_application_commands.py", "invoke_check_command"),
            ("calamus_application_commands.py", "build_application_command_layer"),
            ("calamus_ui.py", "add_command_item"),
            ("calamus_ui.py", "connect_check_command"),
        }}
        self.assertEqual(len(w104_entries), 3)
        self.assertEqual(
            [item for item in current if item[1] == "compose_core_application_components"],
            [("calamus_application_composition.py", "compose_core_application_components")],
        )

    def test_roadmap_is_exact_and_feature_work_is_deferred(self):
        text = (ROOT / "docs/canonical/CALAMUS_W100_W110_BINDING_DECOMPOSITION_ROADMAP.md").read_text(encoding="utf-8")
        ordered = [
            "W100 — Monolith Decomposition Contract",
            "W101 — Application Composition Root Extraction",
            "W102 — Document Session Extraction",
            "W103 — Editor Transaction Extraction",
            "W104 — Command and Action Architecture",
            "W105 — Menu and UI-State Decoupling",
            "W106 — Preferences and Application State Extraction",
            "W107 — Subsystem Host-Port Migration",
            "W108 — Thin GTK Shell",
            "W109 — Monolith Closure Gate",
            "W110 — Source Code Cleanup",
            "W111 — Product Roadmap Rebaseline",
        ]
        positions = [text.index(item) for item in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("W111 is the first point", text)
        self.assertTrue((ROOT / "docs/canonical/CALAMUS_W101_W112_BINDING_ROADMAP.md").is_file())

    def test_contract_forbids_false_decomposition_mechanisms(self):
        text = (ROOT / "docs/canonical/CALAMUS_W100_MONOLITH_DECOMPOSITION_CONTRACT.md").read_text(encoding="utf-8").casefold()
        for token in ("service locator", "event bus", "plugin framework", "dynamic di container", "*_app.py"):
            self.assertIn(token, text)

    def test_mature_source_audit_records_exact_sources_and_decisions(self):
        text = (ROOT / "docs/canonical/CALAMUS_W100_MATURE_SOURCE_COMPOSITION_DECISION_AUDIT.md").read_text(encoding="utf-8")
        for token in (
            "xed/xed-app.c", "gedit/gedit-app.c", "editor-session.c",
            "pluma/pluma-application.c", "kateapp.cpp", "src/libmain.c",
            "NotepadNextApplication", "atom-application.js", "core/init.lua",
            "ADOPT", "ADAPT", "REJECT",
        ):
            self.assertIn(token, text)

    def test_no_product_or_launcher_behavior_was_changed_by_w100(self):
        metrics = self.load("CALAMUS_W100_BASELINE_METRICS.json")
        self.assertEqual(metrics["launcher_lines"], 3298)
        contract = (ROOT / "docs/canonical/CALAMUS_W100_MONOLITH_DECOMPOSITION_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("must not change user-visible product behavior", " ".join(contract.split()))
        self.assertIn("compose_core_application_components", self.launcher)
        self.assertNotIn("ServiceLocator", self.launcher)


if __name__ == "__main__":
    unittest.main()
