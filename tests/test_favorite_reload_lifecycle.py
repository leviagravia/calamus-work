import ast
import copy
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"


def _method_node(name: str):
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"method {name!r} not found")


def _compiled_method(name: str, namespace=None):
    node = copy.deepcopy(_method_node(name))
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class _FakeMenuItem:
    def __init__(self, label=""):
        self.label = label
        self.sensitive = True
        self.tooltip = None
        self.callbacks = []

    def set_sensitive(self, value):
        self.sensitive = bool(value)

    def set_tooltip_text(self, text):
        self.tooltip = text

    def connect(self, signal, callback):
        self.callbacks.append((signal, callback))

    def activate(self):
        for signal, callback in self.callbacks:
            if signal == "activate":
                callback(self)


class _FakeGtk:
    MenuItem = _FakeMenuItem


class _FakeMenu:
    def __init__(self, children=None):
        self.children = list(children or [])
        self.remove_events = []
        self.append_events = []
        self.show_count = 0

    def get_children(self):
        return list(self.children)

    def remove(self, child):
        self.remove_events.append(child)
        self.children.remove(child)

    def append(self, child):
        self.append_events.append(child)
        self.children.append(child)

    def show_all(self):
        self.show_count += 1


class _FakeApp:
    def __init__(self, snapshots, *, menu=True):
        self._snapshots = [list(items) for items in snapshots]
        self.opened = []
        if menu:
            self.favourites_menu = _FakeMenu()

    def load_favourites(self):
        if not self._snapshots:
            raise AssertionError("unexpected extra Favorites load")
        return self._snapshots.pop(0)

    def open_favourite_path(self, path):
        self.opened.append(path)
        return True

    def save_favourites(self, _items):
        raise AssertionError("Reload must not persist Favorites")

    def load_favourite_store(self):
        raise AssertionError("Reload uses the availability view, not canonical editing")


POPULATE = _compiled_method("populate_favourites_menu", {"Gtk": _FakeGtk, "os": os})
RELOAD = _compiled_method("on_reload_favourites")


class FavoriteReloadLifecycleTests(unittest.TestCase):
    def test_missing_menu_is_a_safe_empty_result(self):
        app = _FakeApp([[]], menu=False)
        self.assertEqual(POPULATE(app), ())
        self.assertEqual(len(app._snapshots), 1)

    def test_first_population_preserves_all_existing_fixed_children(self):
        fixed = [_FakeMenuItem(f"fixed-{i}") for i in range(6)]
        app = _FakeApp([["/tmp/a.txt", "/tmp/b.txt"]])
        app.favourites_menu = _FakeMenu(fixed)

        result = POPULATE(app)

        self.assertEqual(result, ("/tmp/a.txt", "/tmp/b.txt"))
        self.assertEqual(app.favourites_menu.children[:6], fixed)
        self.assertEqual([item.label for item in app._favourite_dynamic_items], ["a.txt", "b.txt"])
        self.assertEqual(app.favourites_menu.remove_events, [])
        self.assertEqual(app.favourites_menu.show_count, 1)

    def test_repopulation_removes_only_previously_owned_dynamic_items(self):
        fixed = [_FakeMenuItem(f"fixed-{i}") for i in range(4)]
        foreign = _FakeMenuItem("future-static-command")
        old_a = _FakeMenuItem("old-a")
        old_b = _FakeMenuItem("old-b")
        app = _FakeApp([["/tmp/new.txt"]])
        app.favourites_menu = _FakeMenu(fixed + [foreign, old_a, old_b])
        app._favourite_dynamic_items = [old_a, old_b]

        result = POPULATE(app)

        self.assertEqual(result, ("/tmp/new.txt",))
        self.assertEqual(app.favourites_menu.children[:5], fixed + [foreign])
        self.assertIn(foreign, app.favourites_menu.children)
        self.assertEqual(app.favourites_menu.remove_events, [old_a, old_b])
        self.assertEqual([item.label for item in app._favourite_dynamic_items], ["new.txt"])

    def test_empty_view_has_one_owned_disabled_placeholder(self):
        fixed = [_FakeMenuItem("fixed")]
        app = _FakeApp([[]])
        app.favourites_menu = _FakeMenu(fixed)

        result = POPULATE(app)

        self.assertEqual(result, ())
        self.assertEqual(len(app._favourite_dynamic_items), 1)
        placeholder = app._favourite_dynamic_items[0]
        self.assertEqual(placeholder.label, "No favourites")
        self.assertFalse(placeholder.sensitive)
        self.assertEqual(app.favourites_menu.children, fixed + [placeholder])

    def test_dynamic_item_activation_uses_favorite_gateway(self):
        app = _FakeApp([["/tmp/a.txt"]])
        POPULATE(app)
        item = app._favourite_dynamic_items[0]

        item.activate()

        self.assertEqual(app.opened, ["/tmp/a.txt"])
        self.assertEqual(item.tooltip, "/tmp/a.txt")

    def test_repeated_refresh_has_no_dynamic_duplicates(self):
        fixed = [_FakeMenuItem("add"), _FakeMenuItem("edit"), _FakeMenuItem("reload")]
        app = _FakeApp([["/tmp/a.txt"], ["/tmp/a.txt", "/tmp/b.txt"]])
        app.favourites_menu = _FakeMenu(fixed)

        POPULATE(app)
        first_dynamic = list(app._favourite_dynamic_items)
        POPULATE(app)

        self.assertTrue(all(item not in app.favourites_menu.children for item in first_dynamic))
        self.assertEqual(app.favourites_menu.children[:3], fixed)
        self.assertEqual([item.label for item in app._favourite_dynamic_items], ["a.txt", "b.txt"])
        self.assertEqual(len(app.favourites_menu.children), 5)

    def test_visible_reload_delegates_once_and_returns_true(self):
        events = []

        class App:
            def populate_favourites_menu(self):
                events.append("populate")
                return ("/tmp/a.txt",)

        app = App()
        self.assertTrue(RELOAD(app))
        self.assertEqual(events, ["populate"])

    def test_reload_does_not_touch_document_undo_or_persistence(self):
        events = []

        class App:
            current_file = "/tmp/current.txt"
            modified = True

            def populate_favourites_menu(self):
                events.append("populate")

            def save_favourites(self, _items):
                raise AssertionError("must not persist")

            def reset_undo(self):
                raise AssertionError("must not touch Undo")

        app = App()
        before = (app.current_file, app.modified)
        self.assertTrue(RELOAD(app))
        self.assertEqual((app.current_file, app.modified), before)
        self.assertEqual(events, ["populate"])


if __name__ == "__main__":
    unittest.main()
