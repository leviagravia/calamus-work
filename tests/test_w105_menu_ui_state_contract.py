from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CALAMUS = str(ROOT / "calamus")
if CALAMUS not in sys.path:
    sys.path.insert(0, CALAMUS)

from calamus_application_components import (  # noqa: E402
    NavigatorCompositionInput,
    UiStateCompositionInput,
    WorkspaceCompositionInput,
)
from calamus_menu_model import CHECK_COMMAND_IDS, DYNAMIC_SLOT_IDS  # noqa: E402

BASELINE = "e16cc21b8a900298406ae8cc4776f6f1ec658e93"


class W105MenuUiStateContractTests(unittest.TestCase):
    def test_identity_is_exact_w105(self):
        version = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        self.assertIn('DEVELOPMENT_BUILD_LABEL = "Development build"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W108"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Thin GTK Shell"', version)
        self.assertIn(f'PUBLISHED_BASELINE = "{BASELINE}"', version)

    def test_w105_core_modules_are_gtk_free(self):
        for rel in (
            "calamus/calamus_menu_model.py",
            "calamus/calamus_ui_state.py",
            "calamus/calamus_ui_state_composition.py",
            "calamus/calamus_workspace_menu.py",
        ):
            source = (ROOT / rel).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports), rel)
            for token in ("Gtk.", "Gdk.", "Pango.", "PangoCairo."):
                self.assertNotIn(token, source, rel)

    def test_global_menu_widgets_are_owned_only_by_menu_gtk_adapter(self):
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        for forbidden in (
            "self.research_item", "self.navigator_item", "self.workspace_item",
            "self.typewriter_item", "self.word_wrap_item", "self.transparent_item",
            "self.top_item", "self.white_item", "self.dark_item", "self.line_item",
            "_syncing_appearance_items", "_syncing_opacity_item", "_syncing_line_number_item",
            "_syncing_typewriter_item",
        ):
            self.assertNotIn(forbidden, launcher)
        ui = (ROOT / "calamus/calamus_ui.py").read_text(encoding="utf-8")
        self.assertIn("class MenuGtkAdapter", ui)
        self.assertIn("def project(self, snapshot: UiStateSnapshot)", ui)
        self.assertIn("widget.set_sensitive(state.enabled)", ui)
        self.assertIn("widget.set_active(bool(state.checked))", ui)
        self.assertIn("self._projection_depth", ui)

    def test_global_state_projection_is_not_duplicated_outside_ui_adapter(self):
        allowed = ROOT / "calamus/calamus_ui.py"
        violations = []
        for path in [ROOT / "bin/calamus", *sorted((ROOT / "calamus").glob("*.py"))]:
            if path == allowed:
                continue
            source = path.read_text(encoding="utf-8")
            for token in (
                ".research_item.set_active", ".navigator_item.set_active", ".workspace_item.set_active",
                ".typewriter_item.set_active", ".word_wrap_item.set_active", ".transparent_item.set_active",
                ".top_item.set_active", ".white_item.set_active", ".dark_item.set_active", ".line_item.set_active",
                ".workspace_new_file_item.set_sensitive", ".workspace_new_folder_item.set_sensitive",
                ".workspace_rename_item.set_sensitive", ".workspace_duplicate_item.set_sensitive",
                ".workspace_trash_item.set_sensitive",
            ):
                if token in source:
                    violations.append(f"{path.relative_to(ROOT)}:{token}")
        self.assertEqual(violations, [])

    def test_panel_runtime_composition_has_no_menu_item_dependency(self):
        for rel, class_name in (
            ("calamus/calamus_research_panel.py", "ResearchPanelRuntime"),
            ("calamus/calamus_navigator_panel.py", "NavigatorPanelRuntime"),
            ("calamus/calamus_workspace_panel.py", "WorkspacePanelRuntime"),
        ):
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
            cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
            init = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
            names = {arg.arg for arg in init.args.args + init.args.kwonlyargs}
            self.assertNotIn("menu_item", names, rel)
        for rel in ("calamus/calamus_navigator_composition.py", "calamus/calamus_workspace_composition.py"):
            self.assertNotIn("menu_item", (ROOT / rel).read_text(encoding="utf-8"), rel)
        self.assertIn("on_visibility_changed", NavigatorCompositionInput.__dataclass_fields__)
        self.assertNotIn("navigator_menu_item", NavigatorCompositionInput.__dataclass_fields__)
        self.assertNotIn("workspace_menu_item", WorkspaceCompositionInput.__dataclass_fields__)

    def test_gateways_do_not_reach_through_to_menu_widgets(self):
        for rel in (
            "calamus/calamus_appearance_gateway.py",
            "calamus/calamus_opacity_gateway.py",
            "calamus/calamus_line_numbers_gateway.py",
        ):
            source = (ROOT / rel).read_text(encoding="utf-8")
            for token in ("white_item", "dark_item", "transparent_item", "line_item", "set_active"):
                self.assertNotIn(token, source, rel)
            self.assertIn("refresh_ui_state", source, rel)

    def test_same_snapshot_drives_command_availability_and_gtk_projection(self):
        state = (ROOT / "calamus/calamus_ui_state.py").read_text(encoding="utf-8")
        self.assertIn("self._availability.set_enabled(command_id, state.enabled)", state)
        self.assertIn("self._projector.project(snapshot)", state)
        application = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        self.assertIn("def ui_state_facts(self):", application)
        self.assertIn("def refresh_ui_state(self):", application)
        self.assertIn("return self.ui_state_controller.refresh(self.ui_state_facts())", application)

    def test_shortcut_toggles_use_logical_state_not_menu_widgets(self):
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        self.assertIn("set_word_wrap(not self.word_wrap)", launcher)
        self.assertIn("self.opacity_percent < MAX_OPACITY_PERCENT", launcher)
        self.assertIn("not self.always_on_top", launcher)
        self.assertIn("not self.line_numbers_enabled", launcher)
        for forbidden in (
            "not self.word_wrap_item.get_active()", "not self.transparent_item.get_active()",
            "not self.top_item.get_active()", "not self.line_item.get_active()",
        ):
            self.assertNotIn(forbidden, launcher)

    def test_dynamic_application_menus_are_row_projection_only(self):
        self.assertEqual(DYNAMIC_SLOT_IDS, ("templates", "recent-files", "recent-workspaces", "favourites"))
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        for function_name, slot in (
            ("populate_template_menu", "templates"),
            ("populate_recent_menu", "recent-files"),
            ("populate_favourites_menu", "favourites"),
        ):
            self.assertIn(f"def {function_name}", launcher)
            self.assertIn(f'render_dynamic("{slot}"', launcher)
        self.assertNotIn("def populate_recent_workspaces_menu", launcher)
        self.assertIn("self._components.workspace.host_runtime.populate_recent_workspaces_menu()", launcher)
        workspace_gtk = (ROOT / "calamus/calamus_workspace_host_gtk.py").read_text(encoding="utf-8")
        self.assertIn('self._menu_ui_adapter.render_dynamic(', workspace_gtk)
        self.assertIn('"recent-workspaces"', workspace_gtk)
        menu_model = (ROOT / "calamus/calamus_menu_model.py").read_text(encoding="utf-8")
        for command_id in (
            "file.template.open", "file.recent.open", "file.favourite.open",
            "file.workspace.recent.open", "file.recent.clear",
        ):
            self.assertIn(command_id, menu_model)

    def test_w104_command_identity_survives_and_w106_w107_are_not_implemented(self):
        command = (ROOT / "calamus/calamus_command_registry.py").read_text(encoding="utf-8")
        self.assertIn("class CommandAvailability", command)
        state_input = UiStateCompositionInput.__dataclass_fields__
        self.assertEqual(set(state_input), {"command_availability"})
        combined = "\n".join(
            (ROOT / rel).read_text(encoding="utf-8")
            for rel in (
                "calamus/calamus_ui_state.py",
                "calamus/calamus_menu_model.py",
                "calamus/calamus_ui_state_composition.py",
            )
        )
        # W106 persistence is now implemented, but W105 remains a distinct runtime domain.
        self.assertTrue((ROOT / "calamus/calamus_settings_repository.py").is_file())
        self.assertTrue((ROOT / "calamus/calamus_preferences.py").is_file())
        for forbidden in ("SubsystemHostPort", "WorkspaceHostPort", "ResearchHostPort"):
            self.assertNotIn(forbidden, combined)

    def test_contract_freezes_exact_check_ids(self):
        self.assertEqual(len(CHECK_COMMAND_IDS), 10)
        self.assertEqual(set(CHECK_COMMAND_IDS), {
            "research.panel", "navigate.navigator-panel", "navigate.workspace-panel",
            "writing.typewriter-mode", "options.word-wrap", "options.transparent-mode",
            "options.always-on-top", "options.appearance.light", "options.appearance.dark",
            "options.line-numbers",
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
