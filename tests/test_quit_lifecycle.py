import ast
import copy
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
    isolated = copy.deepcopy(_method_node(name))
    module = ast.Module(body=[isolated], type_ignores=[])
    ast.fix_missing_locations(module)
    scope = dict(namespace or {})
    exec(compile(module, str(LAUNCHER), "exec"), scope)
    return scope[name]


class _Gtk:
    events = None

    @classmethod
    def main_quit(cls):
        cls.events.append("gtk-main-quit")


class _App:
    def __init__(self, *, continuation=True):
        self.continuation = continuation
        self.events = []

    def may_continue(self):
        self.events.append("may-continue")
        return self.continuation

    def save_settings(self):
        self.events.append("save-settings")


class QuitLifecycleTests(unittest.TestCase):
    def setUp(self):
        _Gtk.events = []
        self.request_close = _compiled_method(
            "request_application_close",
            {"Gtk": _Gtk},
        )

    def test_cancelled_close_preserves_runtime_and_does_not_save_settings(self):
        app = _App(continuation=False)
        self.assertFalse(self.request_close(app, quit_main_loop=False))
        self.assertEqual(app.events, ["may-continue"])
        self.assertEqual(_Gtk.events, [])

    def test_cancelled_menu_quit_does_not_exit_main_loop(self):
        app = _App(continuation=False)
        self.assertFalse(self.request_close(app, quit_main_loop=True))
        self.assertEqual(app.events, ["may-continue"])
        self.assertEqual(_Gtk.events, [])

    def test_accepted_window_close_saves_settings_without_quitting_main_loop_directly(self):
        app = _App(continuation=True)
        self.assertTrue(self.request_close(app, quit_main_loop=False))
        self.assertEqual(app.events, ["may-continue", "save-settings"])
        self.assertEqual(_Gtk.events, [])

    def test_accepted_menu_quit_saves_settings_before_main_loop_exit(self):
        app = _App(continuation=True)
        _Gtk.events = app.events
        self.assertTrue(self.request_close(app, quit_main_loop=True))
        self.assertEqual(
            app.events,
            ["may-continue", "save-settings", "gtk-main-quit"],
        )

    def test_failed_save_decision_is_treated_as_rejected_close(self):
        class SaveFailureApp(_App):
            def may_continue(self):
                self.events.append("save-failed")
                return False

        app = SaveFailureApp()
        self.assertFalse(self.request_close(app, quit_main_loop=True))
        self.assertEqual(app.events, ["save-failed"])
        self.assertEqual(_Gtk.events, [])

    def test_gateway_queries_continuation_once(self):
        class CountApp(_App):
            def __init__(self):
                super().__init__(continuation=True)
                self.count = 0

            def may_continue(self):
                self.count += 1
                return super().may_continue()

        app = CountApp()
        self.assertTrue(self.request_close(app, quit_main_loop=False))
        self.assertEqual(app.count, 1)


if __name__ == "__main__":
    unittest.main()
