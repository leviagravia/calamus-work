import ast
import copy
from pathlib import Path
import unittest

from calamus_view_preferences import prepare_text_wrap_plan

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"


def _methods(*names):
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    nodes = []
    for name in names:
        node = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name), None)
        if node is None:
            raise AssertionError(f"method {name!r} not found")
        nodes.append(copy.deepcopy(node))
    module = ast.Module(body=nodes, type_ignores=[])
    ast.fix_missing_locations(module)
    scope = {"prepare_text_wrap_plan": prepare_text_wrap_plan}
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return tuple(scope[name] for name in names)


class _Item:
    def __init__(self, active): self.active = active
    def get_active(self): return self.active


class _App:
    def __init__(self, *, enabled=False, persist=True):
        self.word_wrap = enabled
        self.persist = persist
        self.events = []
        self.errors = []
    def update_preferences(self, **changes):
        self.events.append(("update-preferences", dict(changes)))
        if not self.persist:
            self.events.append(("refresh-ui-state", self.word_wrap))
            self.errors.append("could not persist preferences")
            return False
        self.word_wrap = changes.get("word_wrap", self.word_wrap)
        return True
    def refresh_ui_state(self): self.events.append(("refresh-ui-state", self.word_wrap))
    def error(self, message): self.errors.append(message)


class TextWrapLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        set_wrap, on_wrap = _methods("set_word_wrap", "on_word_wrap")
        cls.set_wrap = staticmethod(set_wrap)
        cls.on_wrap = staticmethod(on_wrap)

    def test_success_persists_then_commits_reflows_and_projects(self):
        app = _App(enabled=False, persist=True)
        self.assertTrue(self.set_wrap(app, True))
        self.assertTrue(app.word_wrap)
        self.assertEqual(app.events, [("update-preferences", {"word_wrap": True})])
        self.assertEqual(app.errors, [])

    def test_persistence_failure_keeps_logical_state_and_reprojects(self):
        app = _App(enabled=False, persist=False)
        self.assertFalse(self.set_wrap(app, True))
        self.assertFalse(app.word_wrap)
        self.assertEqual(app.events, [
            ("update-preferences", {"word_wrap": True}),
            ("refresh-ui-state", False),
        ])
        self.assertEqual(app.errors, ["could not persist preferences"])

    def test_noop_only_reprojects(self):
        app = _App(enabled=True, persist=True)
        self.assertFalse(self.set_wrap(app, True))
        self.assertEqual(app.events, [("refresh-ui-state", True)])

    def test_menu_input_is_only_requested_boolean(self):
        app = _App(enabled=False, persist=True)
        app.set_word_wrap = lambda requested: self.set_wrap(app, requested)
        self.assertTrue(self.on_wrap(app, _Item(True)))
        self.assertTrue(app.word_wrap)

    def test_no_menu_sync_guard_or_widget_rollback_remains(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotIn("_syncing_word_wrap_item", source)
        self.assertNotIn("word_wrap_item.set_active", source)


if __name__ == "__main__": unittest.main()
