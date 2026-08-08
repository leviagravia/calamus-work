from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "fb003223643d9da5f81ddaa3f3e0e4a9304f3903"
CURRENT_BASELINE = "e16cc21b8a900298406ae8cc4776f6f1ec658e93"
NEW_MODULES = (
    "calamus_application_components.py",
    "calamus_editor_composition.py",
    "calamus_navigator_composition.py",
    "calamus_workspace_composition.py",
    "calamus_clip_composition.py",
    "calamus_application_composition.py",
    "calamus_editor_transaction_composition.py",
)
BUILDERS = NEW_MODULES[1:5] + ("calamus_document_session_composition.py", "calamus_editor_transaction_composition.py")
EXPECTED_ORDER = (
    "document-session",
    "editor-infrastructure",
    "editor-transaction",
    "navigator-and-left-panel-host",
    "workspace",
    "right-panel-host",
    "clip-collection",
    "workspace-startup-binding",
)
EXPECTED_BUNDLE_FIELDS = {
    "EditorInfrastructureComponents": (
        "history", "viewport_runtime", "history_runtime", "typewriter_runtime",
        "search_controller", "misspelling_tag", "search_tag", "current_line_tag",
        "signal_connections",
    ),
    "NavigatorComponents": (
        "navigation_controller", "left_panel_host", "panel_view", "panel_host",
        "panel_runtime",
    ),
    "WorkspaceComponents": (
        "controller", "panel_view", "application_runtime", "mutation_controller",
        "mutation_runtime", "panel_host", "panel_runtime", "host_runtime", "startup_visible",
    ),
    "ClipCollectionComponents": ("view", "controller", "runtime"),
    "CoreApplicationComponents": (
        "document_session", "editor", "editor_transaction", "navigator", "workspace", "right_panel_host", "clips",
        "build_order", "composition_complete",
    ),
}


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def dotted(node: ast.AST) -> str | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


class W101CoreCompositionContractTests(unittest.TestCase):
    def setUp(self):
        self.calamus = ROOT / "calamus"
        self.launcher_path = ROOT / "bin" / "calamus"
        self.launcher_text = self.launcher_path.read_text(encoding="utf-8")
        self.launcher_tree = parse(self.launcher_path)
        self.app = next(
            node for node in self.launcher_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "App"
        )
        self.root_path = self.calamus / "calamus_application_composition.py"
        self.root_tree = parse(self.root_path)
        self.root_text = self.root_path.read_text(encoding="utf-8")

    def load_json(self, name: str):
        return json.loads((ROOT / "docs" / "canonical" / name).read_text(encoding="utf-8"))

    def test_identity_scope_and_contract_are_exact(self):
        version = (self.calamus / "calamus_version.py").read_text(encoding="utf-8")
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W108"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Thin GTK Shell"', version)
        self.assertIn(f'PUBLISHED_BASELINE = "{CURRENT_BASELINE}"', version)
        contract = (ROOT / "docs/canonical/CALAMUS_W101_CORE_COMPOSITION_CONTRACT.md").read_text(encoding="utf-8")
        self.assertIn("Candidate R1", contract)
        self.assertIn("W101: extract core composition boundary", contract)
        for deferred in ("Research composition", "Document Overview", "application lifecycle registration"):
            self.assertIn(deferred, contract)

    def test_required_modules_and_frozen_bundle_fields_are_exact(self):
        provenance = (ROOT / "scripts" / "prove-source-provenance.sh").read_text(encoding="utf-8")
        for name in NEW_MODULES:
            self.assertTrue((self.calamus / name).is_file(), name)
            self.assertIn(name.removesuffix(".py"), provenance)
        tree = parse(self.calamus / "calamus_application_components.py")
        classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
        for name, expected in EXPECTED_BUNDLE_FIELDS.items():
            node = classes[name]
            decorators = [dotted(item.func if isinstance(item, ast.Call) else item) for item in node.decorator_list]
            self.assertIn("dataclass", decorators, name)
            dataclass_call = next(item for item in node.decorator_list if isinstance(item, ast.Call) and dotted(item.func) == "dataclass")
            frozen = next((kw.value for kw in dataclass_call.keywords if kw.arg == "frozen"), None)
            self.assertIsInstance(frozen, ast.Constant)
            self.assertIs(frozen.value, True)
            fields = tuple(
                stmt.target.id for stmt in node.body
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
            )
            self.assertEqual(fields, expected)

    def test_root_import_direction_is_closed_and_builders_are_local(self):
        imported = set()
        for node in self.root_tree.body:
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        self.assertEqual(imported, {
            "__future__",
            "dataclasses",
            "calamus_application_components",
            "calamus_clip_composition",
            "calamus_document",
            "calamus_document_session_composition",
            "calamus_editor_composition",
            "calamus_editor_transaction_composition",
            "calamus_navigator_composition",
            "calamus_workspace_composition",
            "calamus_workspace_host_gtk",
        })
        for name in BUILDERS:
            tree = parse(self.calamus / name)
            modules = {
                node.module for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            }
            self.assertFalse(
                any(module.endswith("_composition") for module in modules),
                f"cross-builder import in {name}: {sorted(modules)}",
            )
            functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            for function in functions:
                args = [arg.arg for arg in function.args.args + function.args.kwonlyargs]
                self.assertNotIn("app", args, f"whole-App input in {name}:{function.name}")
            self.assertFalse(
                any(isinstance(node, ast.Name) and node.id == "app" for node in ast.walk(tree)),
                f"ambient App name in {name}",
            )
        composition_importers = []
        for path in sorted(self.calamus.glob("*.py")):
            if path.name in NEW_MODULES:
                continue
            tree = parse(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith("_composition"):
                    composition_importers.append((path.name, node.module))
        self.assertEqual(composition_importers, [])

    def test_no_ambient_authority_or_dynamic_projection_exists(self):
        forbidden_calls = {"getattr", "setattr", "globals", "locals", "vars", "__import__"}
        forbidden_names = {"ServiceLocator", "ServiceRegistry", "ApplicationContext", "EventBus", "PluginManager"}
        for name in NEW_MODULES:
            tree = parse(self.calamus / name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self.assertNotIn(dotted(node.func), forbidden_calls, f"{name}:{getattr(node, 'lineno', '?')}")
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.Name)):
                    value = getattr(node, "name", getattr(node, "id", ""))
                    self.assertNotIn(value, forbidden_names)
            for stmt in tree.body:
                if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                    value = stmt.value
                    if name == "calamus_application_composition.py" and isinstance(value, ast.Tuple):
                        continue
                    self.fail(f"mutable/ambient module assignment in {name}:{stmt.lineno}")

    def test_only_one_whole_app_entry_and_one_app_bundle_assignment_exist(self):
        whole_app = []
        for path in sorted(self.calamus.glob("*.py")):
            tree = parse(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args + node.args.kwonlyargs]
                    if "app" in args:
                        whole_app.append((path.name, node.name))
        # W108 supersedes the W101/W107 structural allowance for whole-App
        # reusable seams: all production calamus/*.py functions are narrow.
        self.assertEqual(whole_app, [])
        component_assignments = []
        compose_calls = []
        for node in ast.walk(self.app):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if dotted(target) == "self._components":
                        component_assignments.append(node)
            if isinstance(node, ast.Call) and dotted(node.func) == "compose_core_application_components":
                compose_calls.append(node)
        self.assertEqual(len(component_assignments), 1)
        self.assertEqual(len(compose_calls), 1)

    def test_static_compatibility_aliases_match_the_w111_ledger(self):
        ledger = self.load_json("CALAMUS_W101_COMPATIBILITY_ALIAS_LEDGER.json")
        self.assertEqual(ledger["baseline_commit"], BASELINE)
        self.assertEqual(ledger["removal_work_item"], "W111")
        expected = [(item["app_attribute"], item["bundle_path"]) for item in ledger["aliases"]]
        init = next(node for node in self.app.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        actual = []
        for stmt in init.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = dotted(stmt.targets[0])
            value = dotted(stmt.value)
            if target and target.startswith("self.") and value and value.startswith("core_components."):
                actual.append((target.removeprefix("self."), value.removeprefix("core_components.")))
        normalized = [item for item in actual if item in expected]
        self.assertEqual(normalized, expected)
        self.assertEqual(len(normalized), 24)
        self.assertFalse(any(isinstance(node, (ast.For, ast.While)) for node in init.body))
        # Reusable composition must not know about or mutate the concrete App.
        self.assertNotIn("app.", self.root_text)

    def test_moved_constructor_inventory_is_exact_and_absent_from_app(self):
        inventory = self.load_json("CALAMUS_W101_MOVED_CONSTRUCTOR_INVENTORY.json")
        self.assertEqual(inventory["baseline_commit"], BASELINE)
        self.assertEqual(len(inventory["entries"]), 21)
        launcher_calls = {
            dotted(node.func) for node in ast.walk(self.app) if isinstance(node, ast.Call)
        }
        for item in inventory["entries"]:
            destination = self.calamus / item["destination"]
            self.assertTrue(destination.is_file())
            tree = parse(destination)
            names = {dotted(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
            self.assertTrue(
                item["symbol"] in names or item["symbol"] in destination.read_text(encoding="utf-8"),
                item,
            )
            self.assertNotIn(item["symbol"], launcher_calls)
        self.assertNotIn("def build_clip_collection", self.launcher_text)

    def test_named_set_once_cycles_are_bounded_and_complete(self):
        expected = {
            "calamus_navigator_composition.py": 1,
            "calamus_workspace_composition.py": 3,
            "calamus_clip_composition.py": 1,
        }
        for name, count in expected.items():
            tree = parse(self.calamus / name)
            creations = [
                node for node in ast.walk(tree)
                if isinstance(node, ast.Call) and dotted(node.func) == "SetOnceReference"
            ]
            self.assertEqual(len(creations), count, name)
            calls = [dotted(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
            self.assertGreaterEqual(calls.count("runtime_reference.set") + calls.count("application_reference.set") + calls.count("panel_reference.set") + calls.count("host_reference.set"), count)
            self.assertTrue(any(value and value.endswith(".require") for value in calls), name)
        components = (self.calamus / "calamus_application_components.py").read_text(encoding="utf-8")
        self.assertIn("used before assignment", components)
        self.assertIn("already assigned", components)

    def test_editor_signal_inventory_and_lifetime_are_exact(self):
        tree = parse(self.calamus / "calamus_editor_composition.py")
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and dotted(node.func) == "_connect"]
        actual = []
        for node in calls:
            signal = node.args[1].value
            after = any(kw.arg == "after" and isinstance(kw.value, ast.Constant) and kw.value.value is True for kw in node.keywords)
            actual.append((signal, after))
        self.assertEqual(actual, [
            ("changed", False),
            ("begin-user-action", False),
            ("end-user-action", False),
            ("notify::cursor-position", False),
            ("key-press-event", False),
            ("key-release-event", True),
            ("move-cursor", True),
            ("button-press-event", False),
            ("motion-notify-event", True),
            ("button-release-event", True),
            ("scroll-event", False),
            ("focus-out-event", False),
        ])
        ledger = self.load_json("CALAMUS_W101_RESOURCE_OWNERSHIP_LEDGER.json")
        self.assertEqual(len(ledger["owners"]), 9)
        first = ledger["owners"][0]
        self.assertEqual(first["resource"], "12 editor Gtk signal handlers")
        self.assertEqual(first["teardown"], "Gtk widget destruction")

    def test_build_topology_and_composition_complete_barrier_are_exact(self):
        order_assign = next(
            node for node in self.root_tree.body
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CORE_BUILD_ORDER" for t in node.targets)
        )
        self.assertEqual(tuple(item.value for item in order_assign.value.elts), EXPECTED_ORDER)
        compose = next(
            node for node in self.root_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "compose_core_application_components"
        )
        calls = [dotted(node.func) for node in ast.walk(compose) if isinstance(node, ast.Call)]
        expected_calls = [
            "build_document_session_components",
            "build_editor_infrastructure",
            "build_editor_transaction_components",
            "build_navigator_components",
            "build_workspace_components",
            "build_right_panel_host",
            "build_clip_collection_components",
        ]
        positions = [calls.index(name) for name in expected_calls]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("bind_workspace_startup", calls)
        returned = next(node for node in ast.walk(compose) if isinstance(node, ast.Return)).value
        complete = next(kw.value for kw in returned.keywords if kw.arg == "composition_complete")
        self.assertIsInstance(complete, ast.Constant)
        self.assertIs(complete.value, False)

        finish = next(
            node for node in self.root_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "complete_core_application_components"
        )
        finish_calls = [dotted(node.func) for node in ast.walk(finish) if isinstance(node, ast.Call)]
        self.assertEqual(finish_calls.count("bind_workspace_startup"), 1)
        self.assertIn("replace", finish_calls)
        finish_text = ast.get_source_segment(self.root_text, finish) or ""
        self.assertIn("composition_complete=True", finish_text)

        init = next(node for node in self.app.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        init_text = ast.get_source_segment(self.launcher_text, init) or ""
        compose_pos = init_text.index("core_components = compose_core_application_components(")
        first_ledger_alias = init_text.index("self.history = core_components.editor.history")
        finish_pos = init_text.index("core_components = complete_core_application_components(")
        assignment_pos = init_text.index("self._components = core_components")
        recent_projection_pos = init_text.index("self._components.workspace.host_runtime.populate_recent_workspaces_menu()")
        self.assertLess(compose_pos, first_ledger_alias)
        self.assertLess(first_ledger_alias, finish_pos)
        self.assertLess(finish_pos, assignment_pos)
        self.assertLess(assignment_pos, recent_projection_pos)

    def test_research_document_overview_and_lifecycle_remain_in_app_boundary(self):
        build_research = next(node for node in self.app.body if isinstance(node, ast.FunctionDef) and node.name == "build_research_panel")
        research_calls = {dotted(node.func) for node in ast.walk(build_research) if isinstance(node, ast.Call)}
        self.assertIn("build_research_subsystem", research_calls)
        research_composition = parse(self.calamus / "calamus_research_composition.py")
        self.assertTrue(any(
            isinstance(node, ast.Call) and dotted(node.func) == "ResearchPanelCoordinator"
            for node in ast.walk(research_composition)
        ))
        init = next(node for node in self.app.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        init_calls = [dotted(node.func) for node in ast.walk(init) if isinstance(node, ast.Call)]
        self.assertIn("self.build_research_panel", init_calls)
        self.assertIn("document_dossier_app.build_document_overview", init_calls)
        self.assertIn("self.configure_application_lifecycle", init_calls)
        lifecycle_tree = parse(self.calamus / "calamus_application_lifecycle_app.py")
        lifecycle_function = next(node for node in lifecycle_tree.body if isinstance(node, ast.FunctionDef) and node.name == "configure_application_lifecycle")
        registered = []
        for node in ast.walk(lifecycle_function):
            if isinstance(node, ast.Call) and dotted(node.func) == "lifecycle.register_final":
                registered.append((node.lineno, node.args[0].value))
        self.assertEqual([name for _line, name in sorted(registered)], [
            "application-sources", "navigator-panel", "research-panel-view",
            "research-coordinator", "document-overview", "typewriter", "history", "viewport",
        ])

    def test_structural_budgets_are_exact_and_w100_is_strictly_reduced(self):
        methods = [node for node in self.app.body if isinstance(node, ast.FunctionDef)]
        imports = set()
        for node in self.launcher_tree.body:
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("calamus_"):
                imports.add(node.module)
            elif isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names if alias.name.startswith("calamus_"))
        # W108 Thin GTK Shell must strictly reduce the W107 published shell
        # without weakening the original W100 reduction requirement.
        self.assertLess(len(methods), 296)
        self.assertLess(self.app.end_lineno - self.app.lineno + 1, 2355)
        self.assertLess(len(self.launcher_text.splitlines()), 2494)
        metrics = self.load_json("CALAMUS_W100_BASELINE_METRICS.json")
        self.assertLess(self.app.end_lineno - self.app.lineno + 1, metrics["app_lines"])
        self.assertLess(len(self.launcher_text.splitlines()), metrics["launcher_lines"])
        self.assertGreater(len(imports), 0)

    def test_clip_builder_uses_only_narrow_gateway_after_w108_supersession(self):
        builder = (self.calamus / "calamus_clip_composition.py").read_text(encoding="utf-8")
        runtime = (self.calamus / "calamus_clip_runtime.py").read_text(encoding="utf-8")
        self.assertIn("selected_document_text_from_view(inputs.text_view)", builder)
        self.assertIn("insert_clip_expansion_through_gateway", builder)
        self.assertNotIn("def selected_document_text(app", runtime)
        self.assertNotIn("def insert_clip_expansion(app", runtime)
        self.assertIn("def selected_document_text_from_view", runtime)
        self.assertIn("def insert_clip_expansion_through_gateway", runtime)

    def test_roadmap_and_mature_source_decisions_are_specific(self):
        roadmap = (ROOT / "docs/canonical/CALAMUS_W101_W112_BINDING_ROADMAP.md").read_text(encoding="utf-8")
        ordered = [f"W{i}" for i in range(100, 113)]
        positions = [roadmap.index(item) for item in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Research, Document Overview and lifecycle root", roadmap)
        audit = (ROOT / "docs/canonical/CALAMUS_W101_MATURE_SOURCE_DECISION_AUDIT.md").read_text(encoding="utf-8")
        for source in ("GNOME Text Editor", "Airpad", "Helix", "NotepadNext", "Geany", "Kate", "Pluma/gedit", "Bluefish", "Micro", "Neovim", "Monaco"):
            self.assertIn(source, audit)
        for decision in ("ADOPT", "ADAPT", "REJECT", "DEFER"):
            self.assertIn(decision, audit)


if __name__ == "__main__":
    unittest.main()
