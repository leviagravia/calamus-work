from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "e16cc21b8a900298406ae8cc4776f6f1ec658e93"


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def app_class():
    text = source("bin/calamus")
    tree = ast.parse(text)
    return text, next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "App")


class W108ThinGtkShellContractTests(unittest.TestCase):
    def test_identity_contract_and_roadmap_hold_are_exact(self):
        version = source("calamus/calamus_version.py")
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W108"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Thin GTK Shell"', version)
        self.assertIn(f'PUBLISHED_BASELINE = "{BASELINE}"', version)
        contract = source("docs/canonical/CALAMUS_W108_THIN_GTK_SHELL_CONTRACT.md")
        self.assertIn(BASELINE, contract)
        self.assertIn("Thin GTK Shell", contract)
        hold = source("docs/canonical/CALAMUS_POST_W108_ROADMAP_HOLD.txt")
        self.assertIn("W108", hold)
        self.assertIn("post-W108", hold)

    def test_baseline_39_whole_app_seams_are_closed_not_renamed(self):
        rows = list(csv.DictReader(
            source("docs/canonical/CALAMUS_W108_BASELINE_39_WHOLE_APP_SEAMS.tsv").splitlines(),
            delimiter="\t",
        ))
        self.assertEqual(len(rows), 39)
        current_app_args = []
        by_function = {}
        for path in sorted((ROOT / "calamus").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                args = [a.arg for a in node.args.args + node.args.kwonlyargs]
                if "app" in args:
                    current_app_args.append((path.name, node.name))
                by_function.setdefault((path.name, node.name), []).append(args)
        self.assertEqual(current_app_args, [])
        broad_names = {"app", "app_host", "application_context", "application_services", "services", "service_locator"}
        for row in rows:
            key = (Path(row["path"]).name, row["function"])
            for args in by_function.get(key, []):
                self.assertTrue(broad_names.isdisjoint(args), (key, args))

    def test_core_composition_is_typed_app_free_and_two_phase(self):
        components = source("calamus/calamus_application_components.py")
        composition = source("calamus/calamus_application_composition.py")
        launcher, app = app_class()
        self.assertIn("@dataclass(frozen=True)\nclass CoreApplicationCompositionInput", components)
        self.assertIn("def compose_core_application_components(\n    inputs: CoreApplicationCompositionInput", composition)
        self.assertNotIn("app.", composition)
        self.assertIn("composition_complete=False", composition)
        self.assertIn("def complete_core_application_components(", composition)
        self.assertIn("composition_complete=True", composition)
        init = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        segment = ast.get_source_segment(launcher, init) or ""
        order = [
            segment.index("core_components = compose_core_application_components("),
            segment.index("self.history = core_components.editor.history"),
            segment.index("core_components = complete_core_application_components("),
            segment.index("self._components = core_components"),
            segment.index("self._components.workspace.host_runtime.populate_recent_workspaces_menu()"),
        ]
        self.assertEqual(order, sorted(order))
        self.assertEqual(segment.count("self._components = core_components"), 1)

    def test_w101_24_alias_ledger_is_preserved_in_concrete_shell(self):
        ledger = json.loads(source("docs/canonical/CALAMUS_W101_COMPATIBILITY_ALIAS_LEDGER.json"))
        self.assertEqual(ledger["removal_work_item"], "W111")
        expected = [(item["app_attribute"], item["bundle_path"]) for item in ledger["aliases"]]
        self.assertEqual(len(expected), 24)
        launcher, app = app_class()
        init = next(n for n in app.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
        actual = []
        for stmt in init.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            value = stmt.value
            if not (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self"):
                continue
            parts = []
            cursor = value
            while isinstance(cursor, ast.Attribute):
                parts.append(cursor.attr); cursor = cursor.value
            if isinstance(cursor, ast.Name) and cursor.id == "core_components":
                actual.append((target.attr, ".".join(reversed(parts))))
        self.assertEqual([item for item in actual if item in expected], expected)

    def test_command_layer_is_app_free_and_retains_exact_117_bindings(self):
        commands = source("calamus/calamus_application_commands.py")
        self.assertIn("@dataclass(frozen=True)\nclass ApplicationCommandPorts", commands)
        self.assertIn("def build_application_command_layer(ports: ApplicationCommandPorts)", commands)
        tree = ast.parse(commands)
        builder = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_application_command_layer")
        segment = ast.get_source_segment(commands, builder) or ""
        self.assertNotIn("app.", segment)
        self.assertNotIn("getattr(", segment)
        launcher = source("bin/calamus")
        for family in ("EditCommandPorts(", "FileCommandPorts(", "HelpCommandPorts(", "NavigateCommandPorts(",
                       "OptionsCommandPorts(", "ResearchCommandPorts(", "ToolsCommandPorts(", "ViewCommandPorts(",
                       "WritingCommandPorts("):
            self.assertIn(family, launcher)
        # W104 remains the authority for exact application binding cardinality.
        self.assertIn("self.assertEqual(len(binding_ids), 117)", source("tests/test_w104_command_action_contract.py"))

        # R1 FAIL 1/2 exposed two historical true-App oracles that still called
        # W107 forwarding methods retired by W108.  Historical GTK proofs must
        # now cross the stable command boundary (or an explicit owner for
        # non-command projection) rather than recreate App facades.
        authoring_e2e = source("tests/test_authoring_bridge_app_desktop_e2e.py")
        for retired in (
            "win.show_authoring_bridge(",
            "win.on_create_source_note_from_selection(",
            "win.on_insert_link_to_heading(",
        ):
            self.assertNotIn(retired, authoring_e2e)
        for command_id in (
            "research.authoring-bridge",
            "research.create-source-note",
            "research.insert-heading-link",
        ):
            self.assertIn(f'win.invoke_command(\n                        "{command_id}"', authoring_e2e)
        w105_e2e = source("tests/test_w105_menu_ui_state_app_desktop_e2e.py")
        self.assertNotIn("window.populate_recent_workspaces_menu", w105_e2e)
        self.assertNotIn("_components.workspace.host_runtime", w105_e2e)
        self.assertIn("window.workspace_application_runtime.open_root(str(second_workspace))", w105_e2e)

    def test_root_aggregate_records_are_confined_to_composition_root_and_fixtures(self):
        aggregate_names = (
            "CoreApplicationCompositionInput", "ApplicationCommandPorts",
            "EditCommandPorts", "FileCommandPorts", "HelpCommandPorts",
            "NavigateCommandPorts", "OptionsCommandPorts", "ResearchCommandPorts",
            "ToolsCommandPorts", "ViewCommandPorts", "WritingCommandPorts",
        )
        allowed_production = {
            "bin/calamus",
            "calamus/calamus_application_components.py",
            "calamus/calamus_application_composition.py",
            "calamus/calamus_application_commands.py",
        }
        for path in sorted((ROOT / "calamus").glob("*.py")):
            rel = str(path.relative_to(ROOT))
            if rel in allowed_production:
                continue
            text = path.read_text(encoding="utf-8")
            for name in aggregate_names:
                self.assertNotIn(name, text, (rel, name))
        launcher = source("bin/calamus")
        for forbidden in (
            "self.core_application_composition_input", "self.application_command_ports",
            "self.command_ports", "self.composition_input",
        ):
            self.assertNotIn(forbidden, launcher)
        # Root records are values passed immediately into their builders, not retained owners.
        self.assertIn("compose_core_application_components(\n            CoreApplicationCompositionInput(", launcher)
        self.assertIn("build_application_command_layer(\n            ApplicationCommandPorts(", launcher)

    def test_menu_and_shortcut_projection_are_app_free(self):
        ui = source("calamus/calamus_ui.py")
        self.assertIn("class MenuGtkAdapter", ui)
        self.assertIn("def build_menu(\n    menubar", ui)
        self.assertIn("invoke_command", ui[ui.index("def build_menu("):ui.index("def shortcut_bindings")])
        self.assertIn("def shortcut_bindings(invoke_command)", ui)
        self.assertIn("def add_shortcuts(window, invoke_command)", ui)
        for forbidden in ("def build_menu(app", "def shortcut_bindings(app", "def add_shortcuts(app", "def top_menu(app", "def add_command_item"):
            self.assertNotIn(forbidden, ui)

    def test_legacy_gateway_modules_are_narrow_and_no_generic_host_exists(self):
        combined = "\n".join(source(str(path.relative_to(ROOT))) for path in sorted((ROOT / "calamus").glob("*.py")))
        for forbidden in (
            "class AppHost", "class ApplicationContext", "class AppServices", "class ApplicationServices",
            "class ServiceLocator", "class ServiceRegistry", "class EventBus",
        ):
            self.assertNotIn(forbidden, combined)
        for relative in (
            "calamus/calamus_clip_runtime.py", "calamus/calamus_typewriter_app.py",
            "calamus/calamus_scratchpad_gateway.py", "calamus/calamus_writing_app.py",
            "calamus/calamus_document_dossier_app.py", "calamus/calamus_application_lifecycle_app.py",
        ):
            text = source(relative)
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args + node.args.kwonlyargs]
                    self.assertNotIn("app", args, (relative, node.name))

    def test_character_map_is_a_dedicated_gtk_adapter_not_app_method(self):
        launcher, app = app_class()
        methods = {n.name for n in app.body if isinstance(n, ast.FunctionDef)}
        adapter = source("calamus/calamus_character_map_dialog.py")
        self.assertNotIn("on_character_map", methods)
        self.assertIn("def present_character_map(parent, text_view, *, replace_selection, execute_command)", adapter)
        self.assertIn("Gtk.Dialog", adapter)
        self.assertIn("replace_selection", adapter)
        self.assertIn("execute_command", adapter)
        self.assertIn("on_character_map=partial(", launcher)
        self.assertIn("present_character_map,", launcher)

    def test_shell_surface_is_strictly_smaller_without_moving_monolith(self):
        launcher, app = app_class()
        methods = [n for n in app.body if isinstance(n, ast.FunctionDef)]
        app_lines = app.end_lineno - app.lineno + 1
        self.assertLess(app_lines, 2355)
        self.assertLess(len(methods), 296)
        self.assertLess(len(launcher.splitlines()), 2494)
        # No replacement mega-host/module may absorb the deleted shell.
        for path in sorted((ROOT / "calamus").glob("*.py")):
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
                self.assertNotIn(cls.name, {"AppHost", "ApplicationContext", "ApplicationServices", "AppServices"})

    def test_w102_through_w107_authorities_remain_present(self):
        launcher = source("bin/calamus")
        self.assertIn("self.document_session = core_components.document_session.session", launcher)
        self.assertIn("self.editor_transaction = core_components.editor_transaction.controller", launcher)
        self.assertIn("self.command_actions = build_application_command_layer(\n            ApplicationCommandPorts(", launcher)
        self.assertIn("self.ui_state_components = build_ui_state_components(", launcher)
        self.assertIn("self.persistence = build_preferences_application_state_components(CONFIG_DIR)", launcher)
        self.assertIn("self._w107_subsystems = build_subsystem_host_components(", launcher)
        self.assertNotIn("self.state =", launcher)

    def test_provenance_tracks_new_character_map_adapter(self):
        provenance = source("scripts/prove-source-provenance.sh")
        self.assertIn('"calamus_character_map_dialog"', provenance)


if __name__ == "__main__":
    unittest.main(verbosity=2)
