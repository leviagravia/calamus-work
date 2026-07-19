import ast
import copy
from pathlib import Path
import unittest

from calamus_view_preferences import prepare_text_wrap_plan


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


class _Item:
    def __init__(self, active):
        self.active = active
        self.events = []

    def get_active(self):
        self.events.append(("get-active", self.active))
        return self.active

    def set_active(self, value):
        self.active = value
        self.events.append(("set-active", value))


class _App:
    def __init__(self, *, enabled=False, persist=True):
        self.word_wrap = enabled
        self.persist = persist
        self.events = []
        self.errors = []

    def save_settings(self, overrides=None):
        self.events.append(("save-settings", dict(overrides or {})))
        return self.persist

    def queue_wrap_reflow(self):
        self.events.append(("queue-wrap-reflow", self.word_wrap))

    def update_title(self):
        self.events.append(("update-title", self.word_wrap))

    def error(self, message):
        self.errors.append(message)


class TextWrapLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.callback = _compiled_method(
            "on_word_wrap",
            {"prepare_text_wrap_plan": prepare_text_wrap_plan},
        )

    def test_success_persists_before_runtime_commit_and_apply(self):
        app = _App(enabled=False, persist=True)
        item = _Item(True)
        self.assertTrue(self.callback(app, item))
        self.assertTrue(app.word_wrap)
        self.assertEqual(
            app.events,
            [
                ("save-settings", {"word_wrap": True}),
                ("queue-wrap-reflow", True),
                ("update-title", True),
            ],
        )
        self.assertEqual(app.errors, [])

    def test_persistence_failure_rolls_back_menu_and_runtime(self):
        app = _App(enabled=False, persist=False)
        item = _Item(True)
        self.assertFalse(self.callback(app, item))
        self.assertFalse(app.word_wrap)
        self.assertEqual(app.events, [("save-settings", {"word_wrap": True})])
        self.assertEqual(item.events[-1], ("set-active", False))
        self.assertEqual(app.errors, ["Could not save the Word Wrap preference."])
        self.assertFalse(getattr(app, "_syncing_word_wrap_item", False))

    def test_noop_does_not_persist_or_reapply(self):
        app = _App(enabled=True, persist=True)
        item = _Item(True)
        self.assertFalse(self.callback(app, item))
        self.assertEqual(app.events, [])
        self.assertEqual(app.errors, [])

    def test_sync_guard_ignores_programmatic_rollback_signal(self):
        app = _App(enabled=False, persist=True)
        app._syncing_word_wrap_item = True
        item = _Item(True)
        self.assertFalse(self.callback(app, item))
        self.assertEqual(app.events, [])
        self.assertFalse(app.word_wrap)


if __name__ == "__main__":
    unittest.main()
