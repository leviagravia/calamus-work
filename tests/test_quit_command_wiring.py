import ast
import copy
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"


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


class _Gtk:
    events = None

    @classmethod
    def main_quit(cls):
        cls.events.append("gtk-main-quit")


class QuitCommandWiringTests(unittest.TestCase):
    def test_visible_quit_command_and_shortcut_keep_named_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('add_item(filem, "Quit\\tCtrl+Q", app.on_quit)', ui)
        self.assertIn('(\"<Control>Q\", app.on_quit)', ui)
        shortcuts = SHORTCUTS.read_text(encoding="utf-8")
        self.assertIn('ShortcutSpec("File", "Quit", "Ctrl+Q")', shortcuts)

    def test_window_delete_event_keeps_named_close_entrypoint(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('self.connect("delete-event", self.on_close)', launcher)

    def test_menu_quit_and_window_close_delegate_to_one_gateway(self):
        close_method = _method_source("on_close")
        quit_method = _method_source("on_quit")
        self.assertIn("self.request_application_close(quit_main_loop=False)", close_method)
        self.assertIn("self.request_application_close(quit_main_loop=True)", quit_method)
        self.assertNotIn("self.may_continue()", close_method)
        self.assertNotIn("self.may_continue()", quit_method)
        self.assertNotIn("self.save_settings()", close_method)
        self.assertNotIn("self.save_settings()", quit_method)

    def test_delete_event_inverts_gateway_result_for_gtk_contract(self):
        on_close = _compiled_method("on_close")

        class App:
            def __init__(self, accepted):
                self.accepted = accepted
                self.calls = []

            def request_application_close(self, *, quit_main_loop):
                self.calls.append(quit_main_loop)
                return self.accepted

        accepted = App(True)
        self.assertFalse(on_close(accepted))
        self.assertEqual(accepted.calls, [False])

        rejected = App(False)
        self.assertTrue(on_close(rejected))
        self.assertEqual(rejected.calls, [False])

    def test_menu_quit_returns_gateway_result(self):
        on_quit = _compiled_method("on_quit")

        class App:
            def __init__(self, accepted):
                self.accepted = accepted
                self.calls = []

            def request_application_close(self, *, quit_main_loop):
                self.calls.append(quit_main_loop)
                return self.accepted

        accepted = App(True)
        self.assertTrue(on_quit(accepted))
        self.assertEqual(accepted.calls, [True])

        rejected = App(False)
        self.assertFalse(on_quit(rejected))
        self.assertEqual(rejected.calls, [True])

    def test_gateway_orders_unsaved_decision_before_settings_and_quit(self):
        method = _method_source("request_application_close")
        prompt_at = method.index("self.may_continue()")
        settings_at = method.index("self.save_settings()")
        quit_at = method.index("Gtk.main_quit()")
        self.assertLess(prompt_at, settings_at)
        self.assertLess(settings_at, quit_at)
        self.assertIn("if not self.may_continue():", method)
        self.assertIn("return False", method)
        self.assertIn("return True", method)

    def test_gateway_does_not_absorb_other_file_commands(self):
        method = _method_source("request_application_close")
        for forbidden in (
            "prepare_save_plan",
            "prepare_save_as_plan",
            "prepare_open_plan",
            "prepare_new_plan",
            "open_recent_path",
            "open_favourite_path",
            "on_save_session",
            "on_print",
        ):
            self.assertNotIn(forbidden, method)


if __name__ == "__main__":
    unittest.main()
