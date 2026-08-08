from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from calamus_command_catalog import command_spec, shortcut_bindings, shortcut_guide_entries

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "e16cc21b8a900298406ae8cc4776f6f1ec658e93"


def source(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def class_method_source(relative, class_name, method_name):
    text = source(relative)
    tree = ast.parse(text)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method_name)
    return ast.get_source_segment(text, node) or ""


class W107SubsystemHostPortContractTests(unittest.TestCase):
    def test_identity_is_exact_under_w108_thin_shell(self):
        version = source("calamus/calamus_version.py")
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W108"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Thin GTK Shell"', version)
        self.assertIn(f'PUBLISHED_BASELINE = "{BASELINE}"', version)
        true_app = source("tests/test_w107_subsystem_host_port_app_desktop_e2e.py")
        self.assertNotIn("document_session.dirty", true_app)
        self.assertIn("document_session.modified", true_app)
        self.assertIn("document_session.requires_save_confirmation()", true_app)

    def test_no_generic_application_context_service_locator_or_event_bus(self):
        combined = "\n".join(source(path.relative_to(ROOT)) for path in sorted((ROOT / "calamus").glob("*.py")))
        for forbidden in (
            "class AppHost", "class ApplicationContext", "class AppServices",
            "class ServiceLocator", "class ServiceRegistry", "class EventBus",
        ):
            self.assertNotIn(forbidden, combined)
        for module in (
            "calamus_search_runtime.py",
            "calamus_spellcheck_runtime.py",
            "calamus_workspace_host_runtime.py",
            "calamus_research_application.py",
        ):
            text = source("calamus/" + module)
            self.assertNotIn("from gi", text, module)
            self.assertNotIn("import gi", text, module)
            self.assertNotIn("Gtk.", text, module)

    def test_workspace_host_runtime_has_no_window_or_dialog_authority(self):
        runtime = source("calamus/calamus_workspace_host_runtime.py")
        self.assertIn("class WorkspaceHostPorts", runtime)
        self.assertNotIn("calamus_dialogs", runtime)
        self.assertNotIn("calamus_menu_model", runtime)
        self.assertNotIn("dialog_parent", runtime)
        self.assertNotIn("self._parent", runtime)
        self.assertNotIn("bind_components", runtime)
        self.assertNotIn("self._components", runtime)
        self.assertNotIn("def components(", runtime)
        composition = source("calamus/calamus_workspace_composition.py")
        root_composition = source("calamus/calamus_application_composition.py")
        self.assertIn('SetOnceReference("workspace-host-runtime")', composition)
        self.assertIn("host_reference.set(host_runtime)", composition)
        self.assertIn("WorkspaceHostRuntime(", composition)
        self.assertIn("WorkspaceHostPorts(", composition)
        self.assertNotIn("WorkspaceHostRuntime(", root_composition)
        self.assertNotIn("WorkspaceHostPorts(", root_composition)
        self.assertIn("WorkspaceHostGtkAdapter", root_composition)

    def test_recent_workspace_projection_waits_for_core_composition_barrier(self):
        init = class_method_source("bin/calamus", "App", "__init__")
        ui_builder = source("calamus/calamus_ui.py")
        self.assertNotIn("populate_recent_workspaces_menu", ui_builder)
        compose = init.index("core_components = compose_core_application_components(")
        alias = init.index("self.history = core_components.editor.history")
        startup = init.index("core_components = complete_core_application_components(")
        assignment = init.index("self._components = core_components")
        projection = init.index("self._components.workspace.host_runtime.populate_recent_workspaces_menu()")
        self.assertLess(compose, alias)
        self.assertLess(alias, startup)
        self.assertLess(startup, assignment)
        self.assertLess(assignment, projection)

    def test_research_composition_is_outside_app_and_bundle_owned(self):
        app = source("bin/calamus")
        method = class_method_source("bin/calamus", "App", "build_research_panel")
        composition = source("calamus/calamus_research_composition.py")
        self.assertIn("build_research_subsystem(", method)
        self.assertIn("self._research_components", method)
        for constructor in (
            "MarkdownReferenceStore(", "ReferencePanelRuntime(", "SourceNotePanelRuntime(",
            "ScratchpadRuntime(", "ResearchPanelCoordinator(", "BibtexController(",
            "PandocExportController(",
        ):
            self.assertNotIn(constructor, method)
            self.assertIn(constructor, composition)
        self.assertNotIn("self.research_application_runtime", app)
        self.assertNotIn("self.research_components", app)

    def test_search_spell_print_use_one_private_typed_bundle(self):
        app = source("bin/calamus")
        self.assertIn("self._w107_subsystems = build_subsystem_host_components(", app)
        for public_alias in ("self.search_runtime =", "self.spellcheck_runtime =", "self.print_runtime ="):
            self.assertNotIn(public_alias, app)
        init = class_method_source("bin/calamus", "App", "__init__")
        self.assertIn("search_runtime = self._w107_subsystems.search", init)
        self.assertIn("spellcheck_runtime = self._w107_subsystems.spellcheck", init)
        self.assertIn("print_runtime = self._w107_subsystems.printer", init)
        self.assertIn("on_find_replace=search_runtime.on_find_replace", init)
        self.assertIn("on_check=spellcheck_runtime.on_check", init)
        self.assertIn("on_print=print_runtime.on_print", init)

    def test_w108_collapses_w107_facades_but_keeps_bounded_shell_endpoints(self):
        inventory = json.loads(source("docs/canonical/CALAMUS_W100_APP_METHOD_RESPONSIBILITY_INVENTORY.json"))
        names = [r["name"] for r in inventory["methods"] if r["migration_work_item"] == "W107"]
        tree = ast.parse(source("bin/calamus"))
        app = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "App")
        methods = {n.name: n for n in app.body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(len(names), 117)
        self.assertNotIn("build_clip_collection", methods)
        present = [name for name in names if name in methods]
        self.assertEqual(present, [
            "build_research_panel",
            "on_navigator_item_toggled", "toggle_navigator_panel", "hide_navigator_panel",
            "on_go_to_line", "on_go_to_section", "on_next_heading", "on_previous_heading",
            "select_range", "shortcut_rows", "on_user_guide", "on_keyboard_shortcuts",
            "on_about", "info", "large_info", "error",
        ])
        self.assertEqual(len(present), 16)
        long = {name: methods[name].end_lineno - methods[name].lineno + 1 for name in present if methods[name].end_lineno - methods[name].lineno + 1 > 6}
        self.assertEqual(set(long), {"build_research_panel"})
        self.assertLessEqual(long["build_research_panel"], 45)

    def test_ctrl_alt_l_is_removed_from_authoritative_projections_without_replacement(self):
        spec = command_spec("options.line-numbers")
        self.assertEqual(spec.shortcuts, ())
        self.assertEqual(spec.guide_entries, ())
        self.assertFalse(any(command_id == "options.line-numbers" for _accel, command_id, _data in shortcut_bindings()))
        self.assertFalse(any(row.command == "Line Numbers" for row in shortcut_guide_entries()))
        self.assertNotIn("Ctrl+Alt+L", source("calamus/calamus_menu_model.py"))
        self.assertNotIn("Ctrl+Alt+L", source("share/doc/calamus/USER_GUIDE.md"))
        self.assertIn("Line Numbers", source("calamus/calamus_menu_model.py"))

    def test_app_state_is_not_restored(self):
        app = source("bin/calamus")
        self.assertNotIn("self.state =", app)
        self.assertNotIn("def state(", app)
        self.assertIn("self.persistence = build_preferences_application_state_components(CONFIG_DIR)", app)


if __name__ == "__main__":
    unittest.main()
