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


class QuitCommandWiringTests(unittest.TestCase):
    def test_visible_quit_command_and_shortcut_keep_named_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(r'add_item(filem, "Quit\tCtrl+Q", app.on_quit)', ui)
        self.assertIn('("<Control>Q", app.on_quit)', ui)
        shortcuts = SHORTCUTS.read_text(encoding="utf-8")
        self.assertIn('ShortcutSpec("File", "Quit", "Ctrl+Q")', shortcuts)

    def test_window_signals_use_named_close_and_destroy_gateways(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('self.connect("delete-event", self.on_close)', launcher)
        self.assertIn('self.connect("destroy", self.on_destroy)', launcher)

    def test_menu_quit_and_window_close_delegate_to_one_gateway(self):
        close_method = _method_source("on_close")
        quit_method = _method_source("on_quit")
        self.assertIn("self.request_application_close()", close_method)
        self.assertIn("self.request_application_close()", quit_method)
        self.assertNotIn("self.may_continue()", close_method)
        self.assertNotIn("self.may_continue()", quit_method)
        self.assertNotIn("self.save_settings()", close_method)
        self.assertNotIn("self.save_settings()", quit_method)

    def test_delete_event_is_always_owned_by_canonical_gateway(self):
        on_close = _compiled_method("on_close")

        class App:
            def __init__(self, accepted):
                self.accepted = accepted
                self.calls = 0

            def request_application_close(self):
                self.calls += 1
                return self.accepted

        for accepted in (True, False):
            app = App(accepted)
            self.assertTrue(on_close(app))
            self.assertEqual(app.calls, 1)

    def test_menu_quit_returns_gateway_result(self):
        on_quit = _compiled_method("on_quit")

        class App:
            def __init__(self, accepted):
                self.accepted = accepted
                self.calls = 0

            def request_application_close(self):
                self.calls += 1
                return self.accepted

        accepted = App(True)
        self.assertTrue(on_quit(accepted))
        self.assertEqual(accepted.calls, 1)

        rejected = App(False)
        self.assertFalse(on_quit(rejected))
        self.assertEqual(rejected.calls, 1)

    def test_gateway_orders_decision_settings_and_destroy(self):
        method = _method_source("request_application_close")
        prompt_at = method.index("self.may_continue()")
        settings_at = method.index("self.save_settings()")
        flag_at = method.index('self._application_close_in_progress = True')
        destroy_at = method.index("self.destroy()")
        self.assertLess(prompt_at, settings_at)
        self.assertLess(settings_at, flag_at)
        self.assertLess(flag_at, destroy_at)
        self.assertIn("return False", method)
        self.assertIn("return True", method)

    def test_destroy_gateway_terminates_only_an_active_main_loop(self):
        method = _method_source("on_destroy")
        self.assertIn("Gtk.main_level() > 0", method)
        self.assertIn("Gtk.main_quit()", method)
        self.assertIn("return False", method)

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
