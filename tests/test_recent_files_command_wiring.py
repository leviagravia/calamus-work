import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
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
    def __init__(self, target_path, remaining):
        self.target_path = target_path
        self.remaining_paths_after_failure = tuple(remaining)

    @property
    def should_open(self):
        return self.target_path is not None


class _FakeApp:
    def __init__(self, *, may_continue=True, open_result=True):
        self.events = []
        self._may_continue = may_continue
        self._open_result = open_result

    def may_continue(self):
        self.events.append(("prompt",))
        return self._may_continue

    def load_recent_files(self):
        self.events.append(("load",))
        return ["/tmp/current.txt", "/tmp/other.txt"]

    def open_path(self, path):
        self.events.append(("open", path))
        return self._open_result

    def error(self, message):
        self.events.append(("error", message))

    def save_recent_files(self, items):
        self.events.append(("save", tuple(items)))
        return True

    def populate_recent_menu(self):
        self.events.append(("populate",))


class RecentFilesCommandWiringTests(unittest.TestCase):
    def test_existing_recent_submenu_entries_keep_open_recent_entrypoint(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('app.recent_item = Gtk.MenuItem(label="Recent Files")', ui)
        self.assertIn('item.connect("activate", lambda _w, p=path: self.open_recent_path(p))', launcher)

    def test_launcher_imports_pure_recent_plan(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("from calamus_recent_files import prepare_open_recent_plan", source)

    def test_recent_plan_module_has_no_gtk_io_state_or_command_layer(self):
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

    def test_open_path_reports_boolean_success_to_recent_gateway(self):
        method = _method_source("open_path")
        self.assertIn("return self.execute_open_plan(plan, silent=silent)", method)
        self.assertIn("return False", method)

    def test_open_path_returns_executor_success(self):
        def prepare(path, text, *, large_file):
            self.assertEqual((path, text, large_file), ("/tmp/a.txt", "body", False))
            return object()

        method = _compiled_method(
            "open_path",
            {
                "prepare_open_plan": prepare,
                "read_text_file": lambda _path: "body",
                "is_large_text_file": lambda _path: False,
                "OSError": OSError,
                "UnicodeError": UnicodeError,
            },
        )

        class App:
            def execute_open_plan(self, _plan, silent=False):
                return not silent

            def error(self, _message):
                raise AssertionError("success path must not report an error")

        self.assertTrue(method(App(), "/tmp/a.txt"))
        self.assertFalse(method(App(), "/tmp/a.txt", silent=True))

    def test_open_path_returns_false_after_expected_read_failure(self):
        def fail_read(_path):
            raise OSError("read failed")

        method = _compiled_method(
            "open_path",
            {
                "prepare_open_plan": lambda *_args, **_kwargs: object(),
                "read_text_file": fail_read,
                "is_large_text_file": lambda _path: False,
                "OSError": OSError,
                "UnicodeError": UnicodeError,
            },
        )

        class App:
            def __init__(self):
                self.errors = []

            def execute_open_plan(self, _plan, silent=False):
                raise AssertionError("executor must not run after read failure")

            def error(self, message):
                self.errors.append(message)

        app = App()
        self.assertFalse(method(app, "/tmp/a.txt"))
        self.assertEqual(app.errors, ["read failed"])
        silent = App()
        self.assertFalse(method(silent, "/tmp/a.txt", silent=True))
        self.assertEqual(silent.errors, [])

    def test_recent_activation_preserves_save_prompt_before_plan(self):
        method = _method_source("open_recent_path")
        self.assertIn("if not self.may_continue():", method)
        self.assertIn("prepare_open_recent_plan", method)
        self.assertLess(method.index("self.may_continue()"), method.index("prepare_open_recent_plan"))
        self.assertIn("path_exists=os.path.exists(path)", method)

    def test_cancelled_recent_activation_has_no_other_effect(self):
        prepare_calls = []

        def prepare(*args, **kwargs):
            prepare_calls.append((args, kwargs))
            return _Plan("/tmp/current.txt", [])

        method = _compiled_method(
            "open_recent_path",
            {"prepare_open_recent_plan": prepare, "os": type("OS", (), {"path": None})},
        )
        app = _FakeApp(may_continue=False)
        self.assertFalse(method(app, "/tmp/current.txt"))
        self.assertEqual(app.events, [("prompt",)])
        self.assertEqual(prepare_calls, [])

    def test_existing_recent_success_opens_without_rewriting_history(self):
        def prepare(path, items, *, path_exists):
            self.assertEqual(path, "/tmp/current.txt")
            self.assertEqual(items, ["/tmp/current.txt", "/tmp/other.txt"])
            self.assertTrue(path_exists)
            return _Plan(path, ["/tmp/other.txt"])

        fake_os = type("OS", (), {"path": type("Path", (), {"exists": staticmethod(lambda _p: True)})})
        method = _compiled_method(
            "open_recent_path",
            {"prepare_open_recent_plan": prepare, "os": fake_os},
        )
        app = _FakeApp(open_result=True)
        self.assertTrue(method(app, "/tmp/current.txt"))
        self.assertEqual(
            app.events,
            [("prompt",), ("load",), ("open", "/tmp/current.txt")],
        )

    def test_missing_recent_is_reported_pruned_and_menu_refreshed(self):
        def prepare(_path, _items, *, path_exists):
            self.assertFalse(path_exists)
            return _Plan(None, ["/tmp/other.txt"])

        fake_os = type("OS", (), {"path": type("Path", (), {"exists": staticmethod(lambda _p: False)})})
        method = _compiled_method(
            "open_recent_path",
            {"prepare_open_recent_plan": prepare, "os": fake_os},
        )
        app = _FakeApp()
        self.assertFalse(method(app, "/tmp/missing.txt"))
        self.assertEqual(
            app.events,
            [
                ("prompt",),
                ("load",),
                ("error", "Recent file not found:\n/tmp/missing.txt"),
                ("save", ("/tmp/other.txt",)),
                ("populate",),
            ],
        )

    def test_existing_recent_load_failure_is_pruned_without_second_error(self):
        def prepare(path, _items, *, path_exists):
            self.assertTrue(path_exists)
            return _Plan(path, ["/tmp/other.txt"])

        fake_os = type("OS", (), {"path": type("Path", (), {"exists": staticmethod(lambda _p: True)})})
        method = _compiled_method(
            "open_recent_path",
            {"prepare_open_recent_plan": prepare, "os": fake_os},
        )
        app = _FakeApp(open_result=False)
        self.assertFalse(method(app, "/tmp/current.txt"))
        self.assertEqual(
            app.events,
            [
                ("prompt",),
                ("load",),
                ("open", "/tmp/current.txt"),
                ("save", ("/tmp/other.txt",)),
                ("populate",),
            ],
        )

    def test_clear_recent_and_favorites_are_not_batched_into_w50(self):
        self.assertNotIn("prepare_open_recent_plan", _method_source("on_clear_recent"))
        for name in ("on_add_favourite", "on_edit_favourites", "on_reload_favourites"):
            self.assertNotIn("prepare_open_recent_plan", _method_source(name))


if __name__ == "__main__":
    unittest.main()
