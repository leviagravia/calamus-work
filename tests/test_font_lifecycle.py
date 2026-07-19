import ast
import copy
from pathlib import Path
import unittest

from calamus_typography import prepare_font_preference_plan


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
    isolated = copy.deepcopy(_method_node(name))
    module = ast.Module(body=[isolated], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class _Description:
    def __init__(self, font):
        family, size = font.rsplit(" ", 1)
        self.family = family
        self.size = int(size)

    def get_family(self):
        return self.family

    def get_size(self):
        return self.size * 1024


class _Pango:
    SCALE = 1024
    FontDescription = _Description


class _ResponseType:
    OK = 1
    CANCEL = 0


class _Dialog:
    response = _ResponseType.OK
    selected_font = "Serif 18"
    instances = []

    def __init__(self, title=None, transient_for=None):
        self.title = title
        self.transient_for = transient_for
        self.initial_font = None
        self.destroyed = False
        type(self).instances.append(self)

    def set_font(self, font):
        self.initial_font = font

    def run(self):
        return type(self).response

    def get_font(self):
        return type(self).selected_font

    def destroy(self):
        self.destroyed = True


class _Gtk:
    FontChooserDialog = _Dialog
    ResponseType = _ResponseType


class _App:
    def __init__(self, *, persist=True):
        self.font_family = "Monospace"
        self.font_size = 12
        self.persist = persist
        self.events = []
        self.errors = []

    def save_settings(self, overrides=None):
        self.events.append(("save-settings", dict(overrides or {})))
        return self.persist

    def apply_font(self):
        self.events.append(("apply-font", self.font_family, self.font_size))

    def error(self, message):
        self.errors.append(message)


class FontLifecycleTests(unittest.TestCase):
    def setUp(self):
        _Dialog.instances = []
        _Dialog.response = _ResponseType.OK
        _Dialog.selected_font = "Serif 18"
        self.callback = _compiled_method(
            "on_font",
            {
                "Gtk": _Gtk,
                "Pango": _Pango,
                "prepare_font_preference_plan": prepare_font_preference_plan,
            },
        )

    def test_success_persists_before_runtime_commit_and_apply(self):
        app = _App(persist=True)
        self.assertTrue(self.callback(app))
        self.assertEqual(app.font_family, "Serif")
        self.assertEqual(app.font_size, 18)
        self.assertEqual(
            app.events,
            [
                ("save-settings", {"font_family": "Serif", "font_size": 18}),
                ("apply-font", "Serif", 18),
            ],
        )
        self.assertEqual(app.errors, [])
        self.assertEqual(_Dialog.instances[0].initial_font, "Monospace 12")
        self.assertTrue(_Dialog.instances[0].destroyed)

    def test_cancel_is_noop_and_destroys_dialog(self):
        _Dialog.response = _ResponseType.CANCEL
        app = _App()
        self.assertFalse(self.callback(app))
        self.assertEqual((app.font_family, app.font_size), ("Monospace", 12))
        self.assertEqual(app.events, [])
        self.assertTrue(_Dialog.instances[0].destroyed)

    def test_persistence_failure_preserves_runtime_font(self):
        app = _App(persist=False)
        self.assertFalse(self.callback(app))
        self.assertEqual((app.font_family, app.font_size), ("Monospace", 12))
        self.assertEqual(app.events, [("save-settings", {"font_family": "Serif", "font_size": 18})])
        self.assertEqual(app.errors, ["Could not save the Font preference."])

    def test_noop_selection_does_not_persist_or_apply(self):
        _Dialog.selected_font = "Monospace 12"
        app = _App()
        self.assertFalse(self.callback(app))
        self.assertEqual(app.events, [])
        self.assertEqual(app.errors, [])


if __name__ == "__main__":
    unittest.main()
