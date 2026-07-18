import ast
import copy
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
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
    def __init__(self, path, previous, updated):
        self.favorite_path = path
        self.previous_paths = tuple(previous)
        self.updated_paths = tuple(updated)


class _FakeApp:
    def __init__(self, *, current_file="/tmp/current.txt", favorites=None, save_result=True):
        self.current_file = current_file
        self.events = []
        self._favorites = list(favorites if favorites is not None else ["/tmp/a.txt"])
        self._save_result = save_result

    def error(self, message):
        self.events.append(("error", message))

    def info(self, message):
        self.events.append(("info", message))

    def load_favourite_store(self):
        self.events.append(("load-store",))
        return list(self._favorites)

    def load_favourites(self):
        raise AssertionError("Add must not read the availability-filtered menu view")

    def save_favourites(self, items):
        self.events.append(("save", tuple(items)))
        return self._save_result

    def populate_favourites_menu(self):
        self.events.append(("populate",))


class FavoriteAddCommandWiringTests(unittest.TestCase):
    def test_visible_command_label_and_shortcut_are_unchanged(self):
        source = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(favm, "Add to Favourites\\tCtrl+Alt+B", app.on_add_favourite)',
            source,
        )
        self.assertIn('("<Control><Alt>B", app.on_add_favourite)', source)

    def test_launcher_imports_add_and_open_plans_from_same_domain_module(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("prepare_add_favorite_plan", source)
        self.assertIn("prepare_open_favorite_plan", source)

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

    def test_add_path_is_guard_plan_persist_refresh_notify(self):
        method = _method_source("on_add_favourite")
        self.assertIn("if not self.current_file:", method)
        self.assertIn("prepare_add_favorite_plan", method)
        self.assertIn("os.path.abspath(self.current_file)", method)
        self.assertIn("self.load_favourite_store()", method)
        self.assertNotIn("self.load_favourites()", method)
        self.assertIn("self.save_favourites(list(plan.updated_paths))", method)
        self.assertIn('self.error("Could not add file to Favourites.")', method)
        self.assertIn("self.populate_favourites_menu()", method)
        self.assertIn('self.info("Added to Favourites:\\n" + plan.favorite_path)', method)
        self.assertLess(method.index("prepare_add_favorite_plan"), method.index("self.save_favourites"))
        self.assertLess(method.index("self.save_favourites"), method.index("self.populate_favourites_menu"))
        self.assertLess(method.index("self.populate_favourites_menu"), method.index("self.info"))

    def test_unnamed_document_is_rejected_without_store_or_ui_effects(self):
        prepare_calls = []

        def prepare(*args, **kwargs):
            prepare_calls.append((args, kwargs))
            raise AssertionError("plan must not run for an unnamed document")

        method = _compiled_method("on_add_favourite", {"prepare_add_favorite_plan": prepare, "os": os})
        app = _FakeApp(current_file=None)
        self.assertFalse(method(app))
        self.assertEqual(
            app.events,
            [("error", "Save the current document before adding it to Favourites.")],
        )
        self.assertEqual(prepare_calls, [])

    def test_success_persists_plan_then_refreshes_and_notifies(self):
        prepare_calls = []

        def prepare(path, existing):
            prepare_calls.append((path, tuple(existing)))
            return _Plan(path, existing, [path, "/tmp/a.txt"])

        method = _compiled_method("on_add_favourite", {"prepare_add_favorite_plan": prepare, "os": os})
        app = _FakeApp(
            current_file="/tmp/current.txt",
            favorites=["/tmp/a.txt"],
            save_result=True,
        )
        self.assertTrue(method(app))
        self.assertEqual(prepare_calls, [("/tmp/current.txt", ("/tmp/a.txt",))])
        self.assertEqual(
            app.events,
            [
                ("load-store",),
                ("save", ("/tmp/current.txt", "/tmp/a.txt")),
                ("populate",),
                ("info", "Added to Favourites:\n/tmp/current.txt"),
            ],
        )

    def test_add_preserves_temporarily_unavailable_canonical_favorites(self):
        from calamus_favorites import prepare_add_favorite_plan

        method = _compiled_method(
            "on_add_favourite",
            {"prepare_add_favorite_plan": prepare_add_favorite_plan, "os": os},
        )
        app = _FakeApp(
            current_file="/tmp/current.txt",
            favorites=["/tmp/missing.txt", "/tmp/available.txt"],
        )
        self.assertTrue(method(app))
        self.assertEqual(
            app.events,
            [
                ("load-store",),
                ("save", ("/tmp/current.txt", "/tmp/missing.txt", "/tmp/available.txt")),
                ("populate",),
                ("info", "Added to Favourites:\n/tmp/current.txt"),
            ],
        )

    def test_relative_current_file_is_normalized_at_app_boundary(self):
        captured = []

        def prepare(path, existing):
            captured.append((path, tuple(existing)))
            return _Plan(path, existing, [path])

        method = _compiled_method("on_add_favourite", {"prepare_add_favorite_plan": prepare, "os": os})
        app = _FakeApp(current_file="relative.txt", favorites=[])
        self.assertTrue(method(app))
        self.assertEqual(captured[0][0], os.path.abspath("relative.txt"))

    def test_persistence_failure_reports_error_and_suppresses_ui_commit(self):
        method = _compiled_method(
            "on_add_favourite",
            {
                "prepare_add_favorite_plan": lambda path, existing: _Plan(
                    path, existing, [path, *existing]
                ),
                "os": os,
            },
        )
        app = _FakeApp(save_result=False)
        self.assertFalse(method(app))
        self.assertEqual(
            app.events,
            [
                ("load-store",),
                ("save", ("/tmp/current.txt", "/tmp/a.txt")),
                ("error", "Could not add file to Favourites."),
            ],
        )

    def test_existing_favorite_is_persisted_in_move_to_front_order(self):
        from calamus_favorites import prepare_add_favorite_plan

        method = _compiled_method(
            "on_add_favourite",
            {"prepare_add_favorite_plan": prepare_add_favorite_plan, "os": os},
        )
        app = _FakeApp(
            current_file="/tmp/b.txt",
            favorites=["/tmp/a.txt", "/tmp/b.txt", "/tmp/c.txt", "/tmp/b.txt"],
        )
        self.assertTrue(method(app))
        self.assertIn(("save", ("/tmp/b.txt", "/tmp/a.txt", "/tmp/c.txt")), app.events)

    def test_add_does_not_prompt_open_or_touch_document_and_undo(self):
        method = _method_source("on_add_favourite")
        forbidden = (
            "may_continue",
            "open_path",
            "open_recent_path",
            "open_favourite_path",
            "self.document",
            "buffer",
            "set_text",
            "reset_undo_history",
            "execute_command",
            "save_file",
            "save_as",
            "bookmark",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, method)

    def test_add_does_not_change_menu_structure_or_other_favorite_commands(self):
        method = _method_source("on_add_favourite")
        self.assertNotIn("favourites_menu.append", method)
        self.assertNotIn("favourites_menu.remove", method)
        self.assertNotIn("Gtk.", method)
        for name in ("open_favourite_path", "on_edit_favourites", "on_reload_favourites"):
            self.assertNotIn("prepare_add_favorite_plan", _method_source(name))


if __name__ == "__main__":
    unittest.main()
