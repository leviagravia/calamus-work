from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CALAMUS = str(ROOT / "calamus")
if CALAMUS not in sys.path:
    sys.path.insert(0, CALAMUS)

from calamus_command_catalog import build_command_registry  # noqa: E402
from calamus_menu_model import (  # noqa: E402
    APPLICATION_MENU_MODEL,
    CHECK_COMMAND_IDS,
    DYNAMIC_SLOT_IDS,
    TOP_LEVEL_MENU_ORDER,
    WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS,
    DynamicMenuRow,
    command_nodes,
    dynamic_slots,
    favourite_rows,
    recent_file_rows,
    recent_workspace_rows,
    template_rows,
    validate_menu_model,
)
from calamus_ui_state import (  # noqa: E402
    ActionUiState,
    UiStateController,
    UiStateFacts,
    UiStateSnapshot,
    derive_ui_state,
)


class _Availability:
    def __init__(self):
        self.values = {}
        self.calls = []

    def set_enabled(self, command_id, enabled):
        value = bool(enabled)
        self.calls.append((command_id, value))
        self.values[command_id] = value


class _Projector:
    def __init__(self):
        self.snapshots = []

    def project(self, snapshot):
        self.snapshots.append(snapshot)


class W105MenuUiStateTests(unittest.TestCase):
    def test_menu_model_is_exact_and_catalog_backed(self):
        self.assertEqual(
            TOP_LEVEL_MENU_ORDER,
            ("File", "Edit", "Research", "Navigate", "Writing", "Revise", "View", "Options", "Tools", "Help"),
        )
        registry = build_command_registry()
        validate_menu_model(registry.command_ids())
        nodes = command_nodes(APPLICATION_MENU_MODEL)
        self.assertEqual(len(nodes), 120)
        self.assertTrue({node.command_id for node in nodes} <= set(registry.command_ids()))
        self.assertEqual(dynamic_slots(), DYNAMIC_SLOT_IDS)
        self.assertEqual(
            CHECK_COMMAND_IDS,
            (
                "research.panel", "navigate.navigator-panel", "navigate.workspace-panel",
                "writing.typewriter-mode", "options.word-wrap", "options.transparent-mode",
                "options.always-on-top", "options.appearance.light", "options.appearance.dark",
                "options.line-numbers",
            ),
        )

    def test_dynamic_row_builders_are_immutable_parameterized_projections(self):
        self.assertEqual(template_rows(()), (DynamicMenuRow("No templates", enabled=False),))
        rows = template_rows((("Article", "/tmp/a.md"),))
        self.assertEqual(rows[0].command_id, "file.template.open")
        self.assertEqual(rows[0].data(), {"path": "/tmp/a.md"})

        self.assertEqual(recent_file_rows(()), (DynamicMenuRow("No recent files", enabled=False),))
        rows = recent_file_rows(("/tmp/alpha.md", "/tmp/beta.md"))
        self.assertEqual([row.label for row in rows[:2]], ["alpha.md", "beta.md"])
        self.assertEqual(rows[0].command_id, "file.recent.open")
        self.assertEqual(rows[0].tooltip, "/tmp/alpha.md")
        self.assertTrue(rows[-2].separator)
        self.assertEqual(rows[-1].command_id, "file.recent.clear")

        self.assertEqual(favourite_rows(()), (DynamicMenuRow("No favourites", enabled=False),))
        fav = favourite_rows(("/tmp/favourite.md",))[0]
        self.assertEqual((fav.label, fav.command_id, fav.data()), ("favourite.md", "file.favourite.open", {"path": "/tmp/favourite.md"}))

        self.assertEqual(recent_workspace_rows(()), (DynamicMenuRow("No recent workspaces", enabled=False),))
        ws = recent_workspace_rows(("/tmp/work",))[0]
        self.assertEqual((ws.label, ws.command_id, ws.data()), ("/tmp/work", "file.workspace.recent.open", {"path": "/tmp/work"}))

        with self.assertRaises(FrozenInstanceError):
            rows[0].label = "changed"

    def test_ui_state_snapshot_derives_exact_checked_and_workspace_availability(self):
        facts = UiStateFacts(
            research_panel_visible=True,
            navigator_panel_visible=False,
            workspace_panel_visible=True,
            typewriter_enabled=True,
            word_wrap=False,
            opacity_percent=88,
            always_on_top=True,
            appearance_mode="dark",
            line_numbers_enabled=True,
            workspace_root_present=False,
        )
        snapshot = derive_ui_state(facts)
        self.assertEqual(len(snapshot.states), 15)
        expected_checked = {
            "research.panel": True,
            "navigate.navigator-panel": False,
            "navigate.workspace-panel": True,
            "writing.typewriter-mode": True,
            "options.word-wrap": False,
            "options.transparent-mode": True,
            "options.always-on-top": True,
            "options.appearance.light": False,
            "options.appearance.dark": True,
            "options.line-numbers": True,
        }
        self.assertEqual(
            {command_id: snapshot.checked(command_id) for command_id in CHECK_COMMAND_IDS},
            expected_checked,
        )
        self.assertTrue(all(not snapshot.enabled(cid) for cid in WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS))

        with_root = derive_ui_state(UiStateFacts(workspace_root_present=True))
        self.assertTrue(all(with_root.enabled(cid) for cid in WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS))
        self.assertEqual(snapshot.state_for("unknown"), ActionUiState())
        with self.assertRaises(TypeError):
            snapshot.states["research.panel"] = ActionUiState()

    def test_ui_state_facts_validate_nonpresentation_domain(self):
        with self.assertRaises(TypeError):
            UiStateFacts(opacity_percent=True)
        with self.assertRaises(ValueError):
            UiStateFacts(opacity_percent=101)
        with self.assertRaises(ValueError):
            UiStateFacts(appearance_mode="purple")

    def test_controller_drives_availability_and_projector_from_same_snapshot(self):
        availability = _Availability()
        projector = _Projector()
        controller = UiStateController(availability, projector)
        snapshot = controller.refresh(UiStateFacts(word_wrap=False, workspace_root_present=False))
        self.assertIs(controller.snapshot, snapshot)
        self.assertIs(projector.snapshots[-1], snapshot)
        for command_id in WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS:
            self.assertFalse(availability.values[command_id])
        self.assertTrue(availability.values["options.word-wrap"])
        self.assertEqual(controller.requested_toggle("options.word-wrap"), True)
        with self.assertRaisesRegex(ValueError, "no checked state"):
            controller.requested_toggle("file.workspace.rename")

    def test_late_projector_binding_replays_current_snapshot_once(self):
        availability = _Availability()
        controller = UiStateController(availability)
        snapshot = controller.refresh(UiStateFacts(research_panel_visible=True))
        projector = _Projector()
        controller.bind_projector(projector)
        self.assertEqual(projector.snapshots, [snapshot])

    def test_snapshot_requires_typed_state_values(self):
        with self.assertRaises(TypeError):
            UiStateSnapshot({"x": True})
        with self.assertRaises(ValueError):
            UiStateSnapshot({"": ActionUiState()})


if __name__ == "__main__":
    unittest.main(verbosity=2)
