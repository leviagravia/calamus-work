import ast
from pathlib import Path
import unittest
from tests.w104_command_test_support import guide_has


from tests.w105_menu_test_support import legacy_menu_projection
ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"


def _method_source(name: str) -> str:
    source = LAUNCHER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"method {name!r} not found")


class TextWrapCommandWiringTests(unittest.TestCase):
    def test_visible_command_and_shortcut_remain_single_named_entrypoint(self):
        ui = legacy_menu_projection()
        self.assertIn('connect_check_command(app.word_wrap_item, app, "options.word-wrap")', ui)
        self.assertIn("command_shortcut_bindings()", ui)
        self.assertTrue(guide_has("Options", "Word Wrap", "Alt+Z"))

    def test_startup_uses_typed_loader_not_python_truthiness(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("self.persistence = build_preferences_application_state_components(CONFIG_DIR)", launcher)
        self.assertIn("return self.preference_snapshot.word_wrap", launcher)
        self.assertNotIn("self.settings", launcher)

    def test_callback_is_a_persist_then_apply_gateway(self):
        callback = _method_source("on_word_wrap")
        self.assertIn("self.set_word_wrap(bool(item.get_active()))", callback)
        self.assertLessEqual(len(callback.splitlines()), 2)
        self.assertNotIn("item.set_active", callback)

        method = _method_source("set_word_wrap")
        self.assertIn("prepare_text_wrap_plan", method)
        self.assertIn("return self.update_preferences(word_wrap=plan.enabled)", method)
        self.assertNotIn("item.set_active", method)
        self.assertNotIn("self.save_settings", method)
        self.assertNotIn("self.word_wrap =", method)

    def test_callback_has_no_document_or_undo_mutation(self):
        method = _method_source("on_word_wrap")
        for forbidden in (
            "current_file",
            "document",
            "buffer",
            "history",
            "undo",
            "modified",
            "Recent",
            "Favorite",
            "CommandContext",
            "command_layer",
        ):
            self.assertNotIn(forbidden, method)

    def test_save_settings_now_reports_persistence_and_updates_snapshot_on_success(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        repository = (ROOT / "calamus" / "calamus_settings_repository.py").read_text(encoding="utf-8")
        self.assertNotIn("def save_settings", launcher)
        self.assertNotIn("self.settings", launcher)
        self.assertIn("class SettingsRepository", repository)
        self.assertIn("def update_preferences", repository)
        self.assertIn("def update_application_state", repository)

    def test_runtime_adapter_uses_viewport_allocation_not_never_policy(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        editor = (ROOT / "calamus" / "calamus_editor.py").read_text(encoding="utf-8")
        apply_method = _method_source("apply_wrap_policy")
        self.assertIn("apply_text_wrap_policy", apply_method)
        self.assertNotIn("Gtk.PolicyType.NEVER", apply_method)
        self.assertIn("Gtk.PolicyType.AUTOMATIC", editor)
        self.assertIn("scroller.get_hadjustment()", editor)
        self.assertIn("self.queue_wrap_reflow()", _method_source("_project_preferences_snapshot"))
        self.assertIn("self._wrap_reflow_source = GLib.idle_add(apply_deferred)", _method_source("queue_wrap_reflow"))
        self.assertIn("GLib.source_remove(source)", _method_source("queue_wrap_reflow"))

    def test_options_menu_is_not_recomposed_incidentally(self):
        ui = legacy_menu_projection()
        self.assertIn('optm = top_menu(app, "Options")', ui)
        self.assertIn('app.word_wrap_item = Gtk.CheckMenuItem(label="Word Wrap\\tAlt+Z")', ui)
        self.assertNotIn('Gtk.CheckMenuItem(label="Text Wrap', ui)


if __name__ == "__main__":
    unittest.main()
