import ast
import copy
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
FAVORITES = ROOT / "calamus" / "calamus_favorites.py"
STATE = ROOT / "calamus" / "calamus_state.py"
CONFIG = ROOT / "calamus" / "calamus_config.py"


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
    def __init__(self, updated, rejected=()):
        self.updated_paths = tuple(updated)
        self.rejected_paths = tuple(rejected)


class _FakeApp:
    def __init__(self, *, store=None, save_result=True):
        self._store = list(store if store is not None else ["/old/missing.txt"])
        self._save_result = save_result
        self.events = []

    def load_favourite_store(self):
        self.events.append(("load_store",))
        return list(self._store)

    def save_favourites(self, items):
        self.events.append(("save", tuple(items)))
        return self._save_result

    def populate_favourites_menu(self):
        self.events.append(("populate",))

    def error(self, message):
        self.events.append(("error", message))


class FavoriteEditCommandWiringTests(unittest.TestCase):
    def test_visible_edit_command_and_shortcut_are_unchanged(self):
        source = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(favm, "Edit Favourites…\\tCtrl+Shift+D", app.on_edit_favourites)',
            source,
        )
        self.assertIn('("<Control><Shift>D", app.on_edit_favourites)', source)

    def test_launcher_imports_edit_parser_and_plan_from_favorites_domain(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("parse_favorite_edit_text", source)
        self.assertIn("prepare_edit_favorite_plan", source)

    def test_favorites_domain_remains_pure(self):
        source = FAVORITES.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports))
        self.assertNotIn("os", imports)
        identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertNotIn("StateManager", identifiers)
        self.assertNotIn("CommandLayer", identifiers)
        self.assertNotIn("open", identifiers)

    def test_state_exposes_canonical_store_separate_from_available_view(self):
        state_source = STATE.read_text(encoding="utf-8")
        config_source = CONFIG.read_text(encoding="utf-8")
        self.assertIn("def load_favourite_store", state_source)
        self.assertIn("def load_favourite_store", config_source)
        self.assertIn("return _clean_existing_paths(self.load_favourite_store(limit), limit)", state_source)
        self.assertIn("return _clean_existing_paths(load_favourite_store(limit), limit)", config_source)

    def test_dialog_shape_is_preserved_but_uses_canonical_store(self):
        method = _method_source("on_edit_favourites")
        self.assertIn('Gtk.Dialog(title="Edit Favourites"', method)
        self.assertIn('d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)', method)
        self.assertIn('Gtk.Label(label="One file path per line:")', method)
        self.assertIn("scroll.set_size_request(520, 260)", method)
        self.assertIn('view.get_buffer().set_text("\\n".join(self.load_favourite_store()))', method)
        self.assertIn("result = self.apply_favourite_edits", method)
        self.assertIn("d.destroy()", method)
        self.assertNotIn("os.path.exists", method)
        self.assertNotIn("self.save_favourites", method)

    def test_apply_adapter_is_parse_resolve_plan_persist_refresh(self):
        method = _method_source("apply_favourite_edits")
        required = (
            "parse_favorite_edit_text",
            "os.path.expanduser",
            "os.path.abspath",
            "os.path.isfile",
            "prepare_edit_favorite_plan",
            "self.load_favourite_store()",
            "self.save_favourites(list(plan.updated_paths))",
            'self.error("Could not save Favourites.")',
            "self.populate_favourites_menu()",
            "plan.rejected_paths",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, method)
        self.assertLess(method.index("prepare_edit_favorite_plan"), method.index("self.save_favourites"))
        self.assertLess(method.index("self.save_favourites"), method.index("self.populate_favourites_menu"))

    def test_success_normalizes_classifies_persists_then_refreshes(self):
        parse_calls = []
        prepare_calls = []

        def parse(text):
            parse_calls.append(text)
            return ("~/a.txt", "relative.txt", "/tmp/dir")

        def prepare(existing, resolved):
            prepare_calls.append((tuple(existing), tuple(resolved)))
            return _Plan([resolved[0][0], resolved[1][0]], [resolved[2][0]])

        real_isfile = os.path.isfile
        os.path.isfile = lambda path: path != os.path.abspath("/tmp/dir")
        try:
            method = _compiled_method(
                "apply_favourite_edits",
                {
                    "parse_favorite_edit_text": parse,
                    "prepare_edit_favorite_plan": prepare,
                    "os": os,
                },
            )
            app = _FakeApp(save_result=True)
            self.assertTrue(method(app, "submitted"))
        finally:
            os.path.isfile = real_isfile

        self.assertEqual(parse_calls, ["submitted"])
        self.assertEqual(prepare_calls[0][0], ("/old/missing.txt",))
        resolved = prepare_calls[0][1]
        self.assertEqual(resolved[0][0], os.path.abspath(os.path.expanduser("~/a.txt")))
        self.assertEqual(resolved[1][0], os.path.abspath("relative.txt"))
        self.assertEqual(
            app.events,
            [
                ("load_store",),
                ("save", (resolved[0][0], resolved[1][0])),
                ("populate",),
                (
                    "error",
                    "These favourite entries are not regular files and were skipped:\n"
                    + resolved[2][0],
                ),
            ],
        )

    def test_persistence_failure_suppresses_refresh_and_rejection_notice(self):
        method = _compiled_method(
            "apply_favourite_edits",
            {
                "parse_favorite_edit_text": lambda text: ("/tmp/a.txt",),
                "prepare_edit_favorite_plan": lambda existing, resolved: _Plan(
                    ["/tmp/a.txt"], ["/tmp/rejected"]
                ),
                "os": os,
            },
        )
        app = _FakeApp(save_result=False)
        self.assertFalse(method(app, "/tmp/a.txt"))
        self.assertEqual(
            app.events,
            [
                ("load_store",),
                ("save", ("/tmp/a.txt",)),
                ("error", "Could not save Favourites."),
            ],
        )

    def test_edit_does_not_touch_document_recent_bookmarks_or_undo(self):
        combined = _method_source("apply_favourite_edits") + _method_source("on_edit_favourites")
        forbidden = (
            "self.document",
            "current_file",
            "buffer_text",
            "reset_undo_history",
            "execute_command",
            "open_path",
            "open_recent_path",
            "save_recent_files",
            "recent_menu",
            "bookmark",
            "command_layer",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, combined)

    def test_other_favorite_commands_and_menu_structure_are_not_rewritten(self):
        for name in ("open_favourite_path", "on_add_favourite", "on_reload_favourites"):
            source = _method_source(name)
            self.assertNotIn("prepare_edit_favorite_plan", source)
            self.assertNotIn("parse_favorite_edit_text", source)
        method = _method_source("apply_favourite_edits")
        self.assertNotIn("favourites_menu.append", method)
        self.assertNotIn("favourites_menu.remove", method)
        self.assertNotIn("Gtk.", method)


if __name__ == "__main__":
    unittest.main()
