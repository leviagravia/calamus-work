import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
RECENT = ROOT / "calamus" / "calamus_recent_files.py"


def _method_node(name: str):
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return source, node
    raise AssertionError(f"method {name!r} not found")


def _method_source(name: str) -> str:
    source, node = _method_node(name)
    return ast.get_source_segment(source, node) or ""


def _compiled_method(name: str, namespace=None):
    _source, node = _method_node(name)
    isolated = copy.deepcopy(node)
    module = ast.Module(body=[isolated], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class _Plan:
    def __init__(self, previous_paths):
        self.previous_paths = tuple(previous_paths)
        self.remaining_paths = ()

    @property
    def should_clear(self):
        return bool(self.previous_paths)


class _FakeApp:
    def __init__(self, *, recent=None, save_result=True):
        self.events = []
        self._recent = list(recent if recent is not None else ["/tmp/a.txt"])
        self._save_result = save_result

    def load_recent_files(self):
        self.events.append(("load",))
        return list(self._recent)

    def save_recent_files(self, items):
        self.events.append(("save", tuple(items)))
        return self._save_result

    def populate_recent_menu(self):
        self.events.append(("populate",))

    def error(self, message):
        self.events.append(("error", message))


class ClearRecentFilesCommandWiringTests(unittest.TestCase):
    def test_visible_menu_item_keeps_existing_entrypoint_and_label(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn(
            'self.item(self.recent_menu, "Clear Recent Files", self.on_clear_recent)',
            source,
        )

    def test_launcher_imports_clear_recent_plan(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("prepare_clear_recent_plan", source)
        self.assertIn("prepare_open_recent_plan", source)

    def test_plan_module_has_no_gtk_io_state_or_command_layer(self):
        source = RECENT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports))
        identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertNotIn("StateManager", identifiers)
        self.assertNotIn("CommandLayer", identifiers)
        self.assertNotIn("open", identifiers)

    def test_clear_path_is_plan_then_persist_then_refresh(self):
        method = _method_source("on_clear_recent")
        self.assertIn("prepare_clear_recent_plan(self.load_recent_files())", method)
        self.assertIn("if not plan.should_clear:", method)
        self.assertIn("self.save_recent_files(list(plan.remaining_paths))", method)
        self.assertIn('self.error("Could not clear recent files.")', method)
        self.assertIn("self.populate_recent_menu()", method)
        self.assertLess(method.index("prepare_clear_recent_plan"), method.index("self.save_recent_files"))
        self.assertLess(method.index("self.save_recent_files"), method.index("self.populate_recent_menu"))

    def test_success_persists_empty_history_then_refreshes(self):
        def prepare(items):
            self.assertEqual(items, ["/tmp/a.txt", "/tmp/b.txt"])
            return _Plan(items)

        method = _compiled_method("on_clear_recent", {"prepare_clear_recent_plan": prepare})
        app = _FakeApp(recent=["/tmp/a.txt", "/tmp/b.txt"], save_result=True)
        self.assertTrue(method(app))
        self.assertEqual(
            app.events,
            [("load",), ("save", ()), ("populate",)],
        )

    def test_persistence_failure_reports_error_and_does_not_refresh(self):
        method = _compiled_method(
            "on_clear_recent",
            {"prepare_clear_recent_plan": lambda items: _Plan(items)},
        )
        app = _FakeApp(recent=["/tmp/a.txt"], save_result=False)
        self.assertFalse(method(app))
        self.assertEqual(
            app.events,
            [
                ("load",),
                ("save", ()),
                ("error", "Could not clear recent files."),
            ],
        )

    def test_empty_history_is_no_op_without_write_refresh_or_error(self):
        method = _compiled_method(
            "on_clear_recent",
            {"prepare_clear_recent_plan": lambda items: _Plan(items)},
        )
        app = _FakeApp(recent=[])
        self.assertFalse(method(app))
        self.assertEqual(app.events, [("load",)])

    def test_clear_does_not_prompt_or_touch_document_lifecycle(self):
        method = _method_source("on_clear_recent")
        forbidden = (
            "may_continue",
            "open_path",
            "current_file",
            "document",
            "set_buffer",
            "reset_undo_history",
            "save_file",
            "save_as",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, method)

    def test_clear_does_not_delete_files_or_use_command_layer(self):
        method = _method_source("on_clear_recent")
        for token in ("os.remove", "os.unlink", "shutil", "execute_command", "CommandLayer"):
            with self.subTest(token=token):
                self.assertNotIn(token, method)

    def test_open_recent_and_favorites_remain_separate(self):
        clear_method = _method_source("on_clear_recent")
        self.assertNotIn("prepare_open_recent_plan", clear_method)
        for name in ("on_add_favourite", "on_edit_favourites", "on_reload_favourites"):
            self.assertNotIn("prepare_clear_recent_plan", _method_source(name))


if __name__ == "__main__":
    unittest.main()
