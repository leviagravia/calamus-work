import ast
import copy
from pathlib import Path
import unittest

from calamus_application_lifecycle import ApplicationLifecycleCoordinator


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
    level = 0
    events = None

    @classmethod
    def main_level(cls):
        return cls.level

    @classmethod
    def main_quit(cls):
        cls.events.append("gtk-main-quit")


class _App:
    def __init__(
        self, *, continuation=True, destroy_error=None, pre_destroy_allowed=True
    ):
        self.continuation = continuation
        self.destroy_error = destroy_error
        self.pre_destroy_allowed = pre_destroy_allowed
        self.events = []
        self.errors = []
        self._application_close_in_progress = False
        self.application_lifecycle = ApplicationLifecycleCoordinator()
        self.application_lifecycle.register_pre_destroy(
            "pandoc-export", self.stop_worker
        )
        self.application_lifecycle.register_final(
            "runtime", self.stop_runtime
        )

    def stop_worker(self):
        self.events.append("pre-destroy")
        return self.pre_destroy_allowed

    def stop_runtime(self):
        self.events.append("final-shutdown")
        return True

    def may_continue(self):
        self.events.append("may-continue")
        return self.continuation

    def record_window_geometry(self):
        self.events.append("record-geometry")
        return True

    def record_last_file(self):
        self.events.append("record-last-file")
        return True

    def error(self, message):
        self.errors.append(message)

    def destroy(self):
        self.events.append("destroy")
        if self.destroy_error is not None:
            raise self.destroy_error


class QuitLifecycleTests(unittest.TestCase):
    def setUp(self):
        _Gtk.level = 0
        _Gtk.events = []
        self.request_close = _compiled_method("request_application_close")
        self.on_destroy = _compiled_method(
            "on_destroy", {"Gtk": _Gtk, "log_nonfatal": lambda *_: None}
        )

    def test_cancelled_close_preserves_runtime_and_does_not_save_or_destroy(self):
        app = _App(continuation=False)
        self.assertFalse(self.request_close(app))
        self.assertEqual(app.events, ["may-continue"])
        self.assertFalse(app._application_close_in_progress)

    def test_accepted_close_saves_then_destroys_window(self):
        app = _App(continuation=True)
        self.assertTrue(self.request_close(app))
        self.assertEqual(
            app.events, ["may-continue", "pre-destroy", "record-geometry", "record-last-file", "destroy"]
        )
        self.assertTrue(app._application_close_in_progress)

    def test_reentrant_close_is_idempotent(self):
        app = _App()
        app._application_close_in_progress = True
        self.assertTrue(self.request_close(app))
        self.assertEqual(app.events, [])

    def test_destroy_failure_reopens_gateway_and_propagates(self):
        app = _App(destroy_error=RuntimeError("destroy failed"))
        with self.assertRaisesRegex(RuntimeError, "destroy failed"):
            self.request_close(app)
        self.assertEqual(
            app.events, ["may-continue", "pre-destroy", "record-geometry", "record-last-file", "destroy"]
        )
        self.assertFalse(app._application_close_in_progress)

    def test_destroy_without_active_main_loop_does_not_call_main_quit(self):
        app = _App()
        self.assertFalse(self.on_destroy(app))
        self.assertEqual(_Gtk.events, [])
        self.assertEqual(app.events, ["pre-destroy", "final-shutdown"])

    def test_destroy_of_final_window_terminates_active_main_loop(self):
        app = _App()
        _Gtk.level = 1
        _Gtk.events = app.events
        self.assertFalse(self.on_destroy(app))
        self.assertEqual(
            app.events, ["pre-destroy", "final-shutdown", "gtk-main-quit"]
        )

    def test_failed_pre_destroy_keeps_application_open_and_reports_owner(self):
        app = _App(pre_destroy_allowed=False)
        self.assertFalse(self.request_close(app))
        self.assertEqual(app.events, ["may-continue", "pre-destroy"])
        self.assertFalse(app._application_close_in_progress)
        self.assertIn("pandoc-export", app.errors[-1])

    def test_failed_save_decision_is_treated_as_rejected_close(self):
        class SaveFailureApp(_App):
            def may_continue(self):
                self.events.append("save-failed")
                return False

        app = SaveFailureApp()
        self.assertFalse(self.request_close(app))
        self.assertEqual(app.events, ["save-failed"])

    def test_gateway_queries_continuation_once(self):
        class CountApp(_App):
            def __init__(self):
                super().__init__(continuation=True)
                self.count = 0

            def may_continue(self):
                self.count += 1
                return super().may_continue()

        app = CountApp()
        self.assertTrue(self.request_close(app))
        self.assertEqual(app.count, 1)


if __name__ == "__main__":
    unittest.main()
