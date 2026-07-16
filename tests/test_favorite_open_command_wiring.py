import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
FAVORITES = ROOT / "calamus" / "calamus_favorites.py"


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
    def __init__(self, selected_path, target_path):
        self.selected_path = selected_path
        self.target_path = target_path

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

    def open_path(self, path):
        self.events.append(("open", path))
        return self._open_result

    def error(self, message):
        self.events.append(("error", message))

    def load_recent_files(self):
        self.events.append(("load_recent",))
        raise AssertionError("Favorite activation must not read Recent Files")

    def save_recent_files(self, items):
        self.events.append(("save_recent", tuple(items)))
        raise AssertionError("Favorite activation must not persist Recent Files")

    def load_favourites(self):
        self.events.append(("load_favourites",))
        raise AssertionError("Favorite activation must not rewrite its store")

    def save_favourites(self, items):
        self.events.append(("save_favourites", tuple(items)))
        raise AssertionError("Favorite activation must not prune Favorites")


class FavoriteOpenCommandWiringTests(unittest.TestCase):
    def test_dynamic_favorite_entries_use_dedicated_entrypoint(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn(
            'item.connect("activate", lambda _w, p=path: self.open_favourite_path(p))',
            launcher,
        )
        favorites_method = _method_source("populate_favourites_menu")
        self.assertNotIn("open_recent_path", favorites_method)

    def test_launcher_imports_pure_favorite_plan(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("from calamus_favorites import prepare_open_favorite_plan", source)

    def test_favorite_plan_module_has_no_gtk_io_state_or_command_layer(self):
        source = FAVORITES.read_text(encoding="utf-8")
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

    def test_favorite_activation_prompts_before_filesystem_plan(self):
        method = _method_source("open_favourite_path")
        self.assertIn("if not self.may_continue():", method)
        self.assertIn("prepare_open_favorite_plan", method)
        self.assertLess(method.index("self.may_continue()"), method.index("prepare_open_favorite_plan"))
        self.assertIn("path_is_file=os.path.isfile(path)", method)
        self.assertNotIn("open_recent_path", method)
        self.assertNotIn("save_recent_files", method)
        self.assertNotIn("save_favourites", method)

    def test_cancelled_favorite_activation_has_no_other_effect(self):
        prepare_calls = []

        def prepare(*args, **kwargs):
            prepare_calls.append((args, kwargs))
            return _Plan("/tmp/a.txt", "/tmp/a.txt")

        method = _compiled_method(
            "open_favourite_path",
            {"prepare_open_favorite_plan": prepare, "os": type("OS", (), {"path": None})},
        )
        app = _FakeApp(may_continue=False)
        self.assertFalse(method(app, "/tmp/a.txt"))
        self.assertEqual(app.events, [("prompt",)])
        self.assertEqual(prepare_calls, [])

    def test_regular_file_uses_w48_open_gateway_and_returns_its_result(self):
        def prepare(path, *, path_is_file):
            self.assertEqual(path, "/tmp/a.txt")
            self.assertTrue(path_is_file)
            return _Plan(path, path)

        fake_os = type("OS", (), {"path": type("Path", (), {"isfile": staticmethod(lambda _p: True)})})
        method = _compiled_method(
            "open_favourite_path",
            {"prepare_open_favorite_plan": prepare, "os": fake_os},
        )
        success = _FakeApp(open_result=True)
        self.assertTrue(method(success, "/tmp/a.txt"))
        self.assertEqual(success.events, [("prompt",), ("open", "/tmp/a.txt")])

        failure = _FakeApp(open_result=False)
        self.assertFalse(method(failure, "/tmp/a.txt"))
        self.assertEqual(failure.events, [("prompt",), ("open", "/tmp/a.txt")])

    def test_missing_favorite_reports_domain_specific_error_without_store_mutation(self):
        def prepare(path, *, path_is_file):
            self.assertEqual(path, "/tmp/missing.txt")
            self.assertFalse(path_is_file)
            return _Plan(path, None)

        fake_os = type("OS", (), {"path": type("Path", (), {"isfile": staticmethod(lambda _p: False)})})
        method = _compiled_method(
            "open_favourite_path",
            {"prepare_open_favorite_plan": prepare, "os": fake_os},
        )
        app = _FakeApp()
        self.assertFalse(method(app, "/tmp/missing.txt"))
        self.assertEqual(
            app.events,
            [
                ("prompt",),
                ("error", "Favourite file not found or is not a regular file:\n/tmp/missing.txt"),
            ],
        )

    def test_directory_favorite_is_rejected_as_not_a_document_file(self):
        calls = []

        def prepare(path, *, path_is_file):
            calls.append((path, path_is_file))
            return _Plan(path, None)

        fake_os = type("OS", (), {"path": type("Path", (), {"isfile": staticmethod(lambda _p: False)})})
        method = _compiled_method(
            "open_favourite_path",
            {"prepare_open_favorite_plan": prepare, "os": fake_os},
        )
        app = _FakeApp()
        self.assertFalse(method(app, "/tmp/folder"))
        self.assertEqual(calls, [("/tmp/folder", False)])
        self.assertFalse(any(event[0] == "open" for event in app.events))

    def test_recent_gateway_and_favorite_management_commands_are_not_rewritten(self):
        self.assertNotIn("prepare_open_favorite_plan", _method_source("open_recent_path"))
        for name in ("on_add_favourite", "on_edit_favourites", "on_reload_favourites"):
            self.assertNotIn("prepare_open_favorite_plan", _method_source(name))


if __name__ == "__main__":
    unittest.main()
