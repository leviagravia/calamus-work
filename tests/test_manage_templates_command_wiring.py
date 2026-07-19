import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
DIALOGS = ROOT / "calamus" / "calamus_dialogs.py"
TEMPLATES = ROOT / "calamus" / "calamus_templates.py"


def _method_node(name):
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return source, node
    raise AssertionError(f"method {name!r} not found")


def _method_source(name):
    source, node = _method_node(name)
    return ast.get_source_segment(source, node) or ""


def _compiled_method(name, namespace=None):
    _source, node = _method_node(name)
    isolated = copy.deepcopy(node)
    module = ast.Module(body=[isolated], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class ManageTemplatesWiringTests(unittest.TestCase):
    def test_menu_places_manage_templates_after_save_template_before_favorites(self):
        ui = UI.read_text(encoding="utf-8")
        save_at = ui.index('add_item(filem, "Save as Template…", app.on_save_as_template)')
        manage_at = ui.index('add_item(filem, "Manage Templates…", app.on_manage_templates)')
        favorites_at = ui.index('app.favourites_item = Gtk.MenuItem(label="Favorites")')
        self.assertLess(save_at, manage_at)
        self.assertLess(manage_at, favorites_at)
        self.assertNotIn("Manage Templates…\\t", ui)

    def test_template_manager_domain_remains_gtk_free(self):
        source = TEMPLATES.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports))
        for symbol in (
            "ManagedTemplateEntry",
            "RenameTemplatePlan",
            "DeleteTemplatePlan",
            "list_managed_templates",
            "prepare_rename_template_plan",
            "rename_template_file",
            "prepare_delete_template_plan",
            "delete_template_file",
        ):
            self.assertIn(symbol, source)

    def test_manager_dialog_is_dedicated_and_bounded(self):
        dialogs = DIALOGS.read_text(encoding="utf-8")
        self.assertIn('title="Manage Templates"', dialogs)
        self.assertIn('Gtk.Button(label="Rename…")', dialogs)
        self.assertIn('Gtk.Button(label="Delete…")', dialogs)
        self.assertIn('"Default" if item.protected else ""', dialogs)
        self.assertIn("dialog.hide()", dialogs)
        self.assertIn("dialog.show_all()", dialogs)
        tree = ast.parse(dialogs)
        node = next(
            item for item in ast.walk(tree)
            if isinstance(item, ast.FunctionDef) and item.name == "run_manage_templates_dialog"
        )
        self.assertNotIn("TextView", ast.get_source_segment(dialogs, node) or "")

    def test_entrypoint_loads_entries_and_delegates_to_dialog_callbacks(self):
        method = _method_source("on_manage_templates")
        self.assertIn("list_managed_templates(self.state.config_dir)", method)
        self.assertIn("run_manage_templates_dialog(", method)
        self.assertIn("self.rename_managed_template", method)
        self.assertIn("self.delete_managed_template", method)
        for forbidden in ("current_file", "document.file_path", "modified =", "reset_undo", "save_settings"):
            self.assertNotIn(forbidden, method)

    def test_manager_load_failure_reports_error_without_opening_dialog(self):
        events = []
        method = _compiled_method(
            "on_manage_templates",
            {
                "list_managed_templates": lambda _config: (_ for _ in ()).throw(OSError("store unavailable")),
                "run_manage_templates_dialog": lambda *_args: events.append("dialog"),
                "OSError": OSError,
            },
        )

        class State:
            config_dir = "/tmp/config"

        class App:
            state = State()

            def error(self, message):
                events.append(("error", message))

        self.assertFalse(method(App()))
        self.assertEqual(events, [("error", "store unavailable")])

    def test_rename_success_orders_mutation_refresh_notification_and_relist(self):
        events = []
        plan = type("Plan", (), {"target_name": "renamed.md"})()
        refreshed = [object()]
        method = _compiled_method(
            "rename_managed_template",
            {
                "prepare_rename_template_plan": lambda config, source, name: events.append(("plan", config, source, name)) or plan,
                "rename_template_file": lambda actual: events.append(("rename", actual)),
                "list_managed_templates": lambda config: events.append(("list", config)) or refreshed,
                "OSError": OSError,
            },
        )

        class State:
            config_dir = "/tmp/config"

        class App:
            state = State()

            def populate_template_menu(self):
                events.append("refresh")

            def info(self, message):
                events.append(("info", message))

            def error(self, message):
                events.append(("error", message))

        self.assertIs(method(App(), "/tmp/old.txt", "renamed.md"), refreshed)
        self.assertEqual(
            events,
            [
                ("plan", "/tmp/config", "/tmp/old.txt", "renamed.md"),
                ("rename", plan),
                "refresh",
                ("info", "Template renamed: renamed.md"),
                ("list", "/tmp/config"),
            ],
        )

    def test_rename_noop_or_failure_never_refreshes(self):
        for planner in (
            lambda *_args: None,
            lambda *_args: (_ for _ in ()).throw(ValueError("bad name")),
        ):
            events = []
            method = _compiled_method(
                "rename_managed_template",
                {
                    "prepare_rename_template_plan": planner,
                    "rename_template_file": lambda _plan: events.append("rename"),
                    "list_managed_templates": lambda _config: events.append("list"),
                    "OSError": OSError,
                },
            )

            class State:
                config_dir = "/tmp/config"

            class App:
                state = State()

                def populate_template_menu(self):
                    events.append("refresh")

                def info(self, message):
                    events.append(("info", message))

                def error(self, message):
                    events.append(("error", message))

            self.assertIsNone(method(App(), "/tmp/old.txt", "bad"))
            self.assertNotIn("refresh", events)
            self.assertNotIn("rename", events)

    def test_delete_success_orders_mutation_refresh_notification_and_relist(self):
        events = []
        plan = type("Plan", (), {"target_name": "old.txt"})()
        refreshed = [object()]
        method = _compiled_method(
            "delete_managed_template",
            {
                "prepare_delete_template_plan": lambda config, target: events.append(("plan", config, target)) or plan,
                "delete_template_file": lambda actual: events.append(("delete", actual)),
                "list_managed_templates": lambda config: events.append(("list", config)) or refreshed,
                "OSError": OSError,
            },
        )

        class State:
            config_dir = "/tmp/config"

        class App:
            state = State()

            def populate_template_menu(self):
                events.append("refresh")

            def info(self, message):
                events.append(("info", message))

            def error(self, message):
                events.append(("error", message))

        self.assertIs(method(App(), "/tmp/old.txt"), refreshed)
        self.assertEqual(
            events,
            [
                ("plan", "/tmp/config", "/tmp/old.txt"),
                ("delete", plan),
                "refresh",
                ("info", "Template deleted: old.txt"),
                ("list", "/tmp/config"),
            ],
        )

    def test_delete_failure_reports_error_without_refresh_or_success(self):
        events = []
        method = _compiled_method(
            "delete_managed_template",
            {
                "prepare_delete_template_plan": lambda *_args: (_ for _ in ()).throw(ValueError("protected")),
                "delete_template_file": lambda _plan: events.append("delete"),
                "list_managed_templates": lambda _config: events.append("list"),
                "OSError": OSError,
            },
        )

        class State:
            config_dir = "/tmp/config"

        class App:
            state = State()

            def populate_template_menu(self):
                events.append("refresh")

            def info(self, message):
                events.append(("info", message))

            def error(self, message):
                events.append(("error", message))

        self.assertIsNone(method(App(), "/tmp/default.txt"))
        self.assertEqual(events, [("error", "protected")])

    def test_manager_callbacks_do_not_touch_document_or_undo(self):
        combined = _method_source("rename_managed_template") + _method_source("delete_managed_template")
        for forbidden in (
            "current_file",
            "document.file_path",
            "self.modified",
            "set_text(",
            "reset_undo_history",
            "history.",
            "add_recent_file",
            "save_favourites",
            "save_settings",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
