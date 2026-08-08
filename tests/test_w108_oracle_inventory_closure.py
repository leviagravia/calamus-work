from __future__ import annotations

import ast
import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/canonical/CALAMUS_W108_ORACLE_INVENTORY.tsv"

AFFECTED_GTK_FILES = {
    "tests/test_w108_identity_app_desktop_e2e.py",
    "tests/test_w108_thin_gtk_shell_app_desktop_e2e.py",
    "tests/test_authoring_bridge_app_desktop_e2e.py",
    "tests/test_w105_menu_ui_state_app_desktop_e2e.py",
    "tests/test_w107_subsystem_host_port_app_desktop_e2e.py",
    "tests/test_w98_research_panel_app_desktop_e2e.py",
}

CURRENT_W108_FORBIDDEN_TEXT = (
    "docs/canonical",
    "COMPATIBILITY_ALIAS_LEDGER",
    "_components",
    "_w107_subsystems",
    "_research_components",
    "composition_complete",
    "binding_ids()",
    'binding_ids())',
    'hasattr(window',
    'hasattr(win',
)

RETIRED_APP_CALLS = (
    "show_authoring_bridge",
    "on_create_source_note_from_selection",
    "on_insert_link_to_heading",
    "populate_recent_workspaces_menu",
    "replace_all_literal",
    "activate_workspace_path",
    "toggle_research_panel",
    "publish_research_invalidation",
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def direct_app_calls(text: str):
    tree = ast.parse(text)
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        owner = node.func.value
        if isinstance(owner, ast.Name) and owner.id in {"window", "win"}:
            calls.append((owner.id, node.func.attr, node.lineno))
    return calls


class W108OracleInventoryClosureTests(unittest.TestCase):
    def inventory_rows(self):
        rows = list(csv.DictReader(INVENTORY.read_text(encoding="utf-8").splitlines(), delimiter="\t"))
        self.assertTrue(rows)
        return rows

    def test_inventory_covers_every_w108_affected_real_gtk_file(self):
        rows = self.inventory_rows()
        classified = {row["file"] for row in rows}
        self.assertEqual(classified, AFFECTED_GTK_FILES)
        allowed = {"STATIC", "HEADLESS", "BEHAVIORAL-GTK", "HISTORICAL-FROZEN"}
        for row in rows:
            self.assertIn(row["classification"], allowed)
            self.assertTrue(row["primary_authority"].strip())
            self.assertTrue(row["replacement_or_exception"].strip())
            self.assertTrue((ROOT / row["file"]).is_file(), row["file"])

    def test_current_w108_gtk_lane_has_zero_structural_oracle_leakage(self):
        text = read("tests/test_w108_thin_gtk_shell_app_desktop_e2e.py")
        for forbidden in CURRENT_W108_FORBIDDEN_TEXT:
            self.assertNotIn(forbidden, text, forbidden)
        # Current GTK authority invokes stable commands and observes live effects.
        for command_id in (
            "edit.select-all", "file.save", "help.about", "navigate.navigator-panel",
            "options.word-wrap", "research.panel", "tools.system-info",
            "view.character-map", "writing.typewriter-mode", "file.quit",
        ):
            self.assertIn(f'window.invoke_command("{command_id}"', text, command_id)
        self.assertIn("window.on_drag_data_received(", text)
        self.assertIn("W108_CHARACTER_MAP_TRUE_GTK=PASS", text)
        self.assertIn("W108_NAVIGATOR_PANEL_TRUE_GTK=PASS", text)
        self.assertIn("W108_CLEAN_DROP_TRUE_GTK=PASS", text)
        self.assertIn("W108_DIRTY_DROP_CANCEL_TRUE_GTK=PASS", text)

    def test_w88_supersession_uses_stable_commands_without_private_replacement(self):
        text = read("tests/test_authoring_bridge_app_desktop_e2e.py")
        for method in (
            "show_authoring_bridge", "on_create_source_note_from_selection", "on_insert_link_to_heading",
        ):
            self.assertNotIn(f"win.{method}(", text)
        for command_id in (
            "research.authoring-bridge", "research.create-source-note", "research.insert-heading-link",
        ):
            self.assertIn(command_id, text)
        for private in ("_components", "_w107_subsystems", "_research_components"):
            self.assertNotIn(private, text)

    def test_w105_recent_workspaces_uses_natural_event_not_private_projection(self):
        text = read("tests/test_w105_menu_ui_state_app_desktop_e2e.py")
        self.assertNotIn("window.populate_recent_workspaces_menu", text)
        self.assertNotIn("_components.workspace.host_runtime", text)
        self.assertIn("window.workspace_application_runtime.open_root(str(second_workspace))", text)
        self.assertIn('dynamic_signature(window, "recent-workspaces")', text)

    def test_historical_allowlist_is_exact_and_no_unclassified_retired_app_call_remains(self):
        # W107 explicitly certifies these private owners; W98 has one recorded narrow-owner
        # invalidation exception. No other affected GTK file may acquire those private seams.
        private_allow = {
            "tests/test_w107_subsystem_host_port_app_desktop_e2e.py": {"_components", "_w107_subsystems", "_research_components"},
            "tests/test_w98_research_panel_app_desktop_e2e.py": {"_research_components"},
        }
        for relative in sorted(AFFECTED_GTK_FILES):
            text = read(relative)
            allowed = private_allow.get(relative, set())
            for private in ("_components", "_w107_subsystems", "_research_components"):
                if private not in allowed:
                    self.assertNotIn(f".{private}", text, (relative, private))

        # Direct App/window calls to retired facades are forbidden. Narrow-owner calls in
        # W107/W98 are not direct App calls and are covered by the explicit allowlist above.
        allowed_direct = {
            # Synthetic DnD is a genuine top-level GTK endpoint intentionally retained.
            ("tests/test_w108_thin_gtk_shell_app_desktop_e2e.py", "on_drag_data_received"),
        }
        for relative in sorted(AFFECTED_GTK_FILES):
            for owner, method, lineno in direct_app_calls(read(relative)):
                if method in RETIRED_APP_CALLS:
                    self.fail(f"stale retired App call {relative}:{lineno}: {owner}.{method}()")
                if method.startswith("on_drag_data_received"):
                    self.assertIn((relative, method), allowed_direct)


    def test_modal_transition_inventory_is_complete_unique_and_bounded(self):
        inventory = ROOT / "docs/canonical/CALAMUS_W108_MODAL_TRANSITION_INVENTORY.tsv"
        rows = list(csv.DictReader(inventory.read_text(encoding="utf-8").splitlines(), delimiter="\t"))
        expected = {
            "help.about", "view.character-map", "tools.system-info",
            "file.open-drop.clean", "file.open-drop.dirty-cancel", "file.quit.clean",
        }
        self.assertEqual({row["operation"] for row in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        for row in rows:
            for field in ("precondition", "modal_expected", "driver_contract", "terminal_receipt", "primary_authority"):
                self.assertTrue(row[field].strip(), (row["operation"], field))
        by_operation = {row["operation"]: row for row in rows}
        self.assertEqual(by_operation["file.open-drop.clean"]["modal_expected"], "NONE")
        self.assertEqual(by_operation["file.quit.clean"]["modal_expected"], "NONE")
        self.assertEqual(by_operation["file.open-drop.dirty-cancel"]["modal_expected"], "Save changes?")
        self.assertIn("Cancel", by_operation["file.open-drop.dirty-cancel"]["driver_contract"])

    def test_clean_drop_is_recleaned_through_public_save_before_replacement(self):
        text = read("tests/test_w108_thin_gtk_shell_app_desktop_e2e.py")
        character = text.index('print("W108_CHARACTER_MAP_TRUE_GTK=PASS")')
        save_after_undo = text.index('window.invoke_command("file.save", source="w108-true-app")', character)
        clean_drop = text.index('print("W108_CLEAN_DROP_TRUE_GTK=PASS")', save_after_undo)
        self.assertLess(character, save_after_undo)
        self.assertLess(save_after_undo, clean_drop)
        clean_block = text[save_after_undo:clean_drop]
        self.assertIn('(True, False, 77)', clean_block)
        self.assertIn('dropped.resolve()', clean_block)
        self.assertNotIn('ModalDriver(', clean_block)

    def test_dirty_drop_cancel_is_explicit_lossless_and_fail_closed(self):
        text = read("tests/test_w108_thin_gtk_shell_app_desktop_e2e.py")
        clean_drop = text.index('print("W108_CLEAN_DROP_TRUE_GTK=PASS")')
        dirty_drop = text.index('print("W108_DIRTY_DROP_CANCEL_TRUE_GTK=PASS")', clean_drop)
        block = text[clean_drop:dirty_drop]
        for token in (
            'window.invoke_command("writing.insert-date", source="w108-true-app")',
            'self.assertNotEqual(dirty_text, clean_dropped_text)',
            '"Save changes?"',
            'button_with_label(dialog, "Cancel")',
            'ModalDriver([cancel_dirty_drop])',
            '(False, False, 78)',
            'self.assertEqual(Path(window.document_session.file_path).resolve(), dropped.resolve())',
            'self.assertEqual(buffer_text(window), dirty_text)',
        ):
            self.assertIn(token, block, token)

    def test_current_w108_close_has_no_dirty_or_may_continue_bypass(self):
        text = read("tests/test_w108_thin_gtk_shell_app_desktop_e2e.py")
        self.assertNotIn('window.document_session.mark_clean(', text)
        self.assertNotIn('window.may_continue =', text)
        dirty_receipt = text.index('print("W108_DIRTY_DROP_CANCEL_TRUE_GTK=PASS")')
        final_save = text.index('window.invoke_command("file.save", source="w108-true-app")', dirty_receipt)
        quit_call = text.index('window.invoke_command("file.quit", source="w108-true-app")', final_save)
        shutdown = text.index('self.assertTrue(window.application_lifecycle.is_shutdown)', quit_call)
        self.assertLess(dirty_receipt, final_save)
        self.assertLess(final_save, quit_call)
        self.assertLess(quit_call, shutdown)


if __name__ == "__main__":
    unittest.main(verbosity=2)
