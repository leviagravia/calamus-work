from __future__ import annotations

import ast
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CALAMUS = ROOT / "calamus"


PURE_ROLE_SUFFIXES = (
    "_controller",
    "_gateway",
    "_store",
    "_model",
    "_planning",
    "_operations",
    "_coordination",
    "_lifecycle",
    "_results",
)
BOUNDARY_IMPORT_TOKENS = (
    "_view",
    "_dialogs",
    "_panel",
    "_gio",
    "_gtk",
)


def imports_for(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return tuple(names)


class W99GtkFreeArchitectureTests(unittest.TestCase):
    def test_pure_roles_do_not_import_gi_or_gtk(self):
        offenders = []
        for path in sorted(CALAMUS.glob("calamus_*.py")):
            if not path.stem.endswith(PURE_ROLE_SUFFIXES):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported = imports_for(path)
            uses_gtk_name = any(
                isinstance(node, ast.Name) and node.id in {"Gtk", "Gdk", "GLib", "Gio"}
                for node in ast.walk(tree)
            )
            if any(name == "gi" or name.startswith("gi.") for name in imported) or uses_gtk_name:
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_pure_roles_do_not_import_concrete_ui_or_gio_boundaries(self):
        offenders = []
        for path in sorted(CALAMUS.glob("calamus_*.py")):
            if not path.stem.endswith(PURE_ROLE_SUFFIXES):
                continue
            for module in imports_for(path):
                if module.startswith("calamus_") and any(
                    token in module for token in BOUNDARY_IMPORT_TOKENS
                ):
                    offenders.append(f"{path.name} -> {module}")
        self.assertEqual(offenders, [])

    def test_workspace_mutation_depends_on_injected_protocol_not_gio(self):
        source = (CALAMUS / "calamus_workspace_mutation.py").read_text(encoding="utf-8")
        self.assertNotIn("calamus_workspace_gio", source)
        self.assertNotIn("WorkspaceGioAdapter", source)
        self.assertIn("adapter does not implement the Workspace mutation protocol", source)
        launcher = (ROOT / "bin" / "calamus").read_text(encoding="utf-8")
        self.assertIn("WorkspaceGioAdapter()", launcher)

    def test_every_glib_source_has_an_explicit_cancellation_owner(self):
        source_pattern = re.compile(r"(?:GLib|self\.(?:glib|_GLib))\.(?:idle_add|timeout_add|timeout_add_seconds)\(")
        inventory = {}
        candidates = [ROOT / "bin" / "calamus", *sorted(CALAMUS.glob("*.py"))]
        for candidate in candidates:
                source = candidate.read_text(encoding="utf-8")
                count = len(source_pattern.findall(source))
                if count:
                    inventory[str(candidate.relative_to(ROOT))] = count

        self.assertEqual(
            inventory,
            {
                "bin/calamus": 3,
                "calamus/calamus_history_runtime.py": 1,
                "calamus/calamus_navigator_panel_view.py": 2,
                "calamus/calamus_pandoc_runtime.py": 1,
                "calamus/calamus_reference_panel.py": 1,
                "calamus/calamus_research_panel_view.py": 1,
                "calamus/calamus_tags_panel.py": 1,
                "calamus/calamus_viewport_runtime.py": 4,
            },
        )

        ownership_markers = {
            "bin/calamus": (
                "self._wrap_reflow_source",
                "self.word_count_source",
                "self.search_controller.schedule_highlight",
            ),
            "calamus/calamus_history_runtime.py": (
                "self.snapshot_source",
                "def shutdown",
                "self.cancel_snapshot()",
            ),
            "calamus/calamus_navigator_panel_view.py": (
                "self._refresh_source",
                "self._cursor_source",
                "def cancel_pending",
            ),
            "calamus/calamus_pandoc_runtime.py": (
                "session.register_source",
                "def shutdown",
            ),
            "calamus/calamus_reference_panel.py": (
                "self._search_dispatcher",
                "def dispose",
            ),
            "calamus/calamus_research_panel_view.py": (
                "self._reset_source",
                "def dispose",
                "def shutdown",
            ),
            "calamus/calamus_tags_panel.py": (
                "self._selection_source_id",
                "def cancel_deferred_actions",
            ),
            "calamus/calamus_viewport_runtime.py": (
                "self._layout_guard_source",
                "self.scroll_source",
                "def shutdown",
            ),
        }
        for relative, markers in ownership_markers.items():
            source = (ROOT / relative).read_text(encoding="utf-8")
            for marker in markers:
                self.assertIn(marker, source, f"{relative} lacks {marker}")

        boundary = (CALAMUS / "calamus_application_lifecycle_app.py").read_text(encoding="utf-8")
        for owner in (
            "application-sources",
            "navigator-panel",
            "research-panel-view",
            "research-coordinator",
            "history",
            "viewport",
        ):
            self.assertIn(f'"{owner}"', boundary)

    def test_contract_freezes_scope_owner_inventory_and_mature_decisions(self):
        contract = (
            ROOT
            / "docs"
            / "canonical"
            / "CALAMUS_W99_RETROSPECTIVE_GTK_FREE_AND_LIFECYCLE_AUDIT_CONTRACT.md"
        ).read_text(encoding="utf-8")
        direct = (
            ROOT / "docs" / "canonical" / "CALAMUS_W99_DIRECT_SOURCE_AUDIT.md"
        ).read_text(encoding="utf-8")
        mature = (
            ROOT
            / "docs"
            / "canonical"
            / "CALAMUS_W99_MATURE_SOURCE_DECISION_AUDIT.md"
        ).read_text(encoding="utf-8")
        for token in (
            "not a product feature",
            "pandoc-export",
            "application-sources",
            "research-coordinator",
            "Every GLib source has an explicit owner",
            "DESKTOP VALIDATION PENDING",
        ):
            self.assertIn(token, contract)
        for token in (
            "fourteen scheduling calls",
            "WorkspaceMutationController",
            "SearchController",
            "ResearchPanelCoordinator.shutdown",
        ):
            self.assertIn(token, direct)
        for token in ("ADOPT", "ADAPT", "REJECT", "No web source was substituted"):
            self.assertIn(token, mature)

    def test_lifecycle_coordinator_is_gtk_free(self):
        source = (CALAMUS / "calamus_application_lifecycle.py").read_text(encoding="utf-8")
        self.assertNotIn("import gi", source)
        self.assertNotIn("from gi.repository", source)
        self.assertNotIn("Gtk.", source)
        self.assertNotIn("GLib.", source)


if __name__ == "__main__":
    unittest.main()
