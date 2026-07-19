import ast
from pathlib import Path
import unittest


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
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('app.word_wrap_item.connect("toggled", app.on_word_wrap)', ui)
        self.assertIn('("<Alt>Z", app.toggle_word_wrap)', ui)
        shortcuts = SHORTCUTS.read_text(encoding="utf-8")
        self.assertIn('ShortcutSpec("Options", "Word Wrap", "Alt+Z")', shortcuts)

    def test_startup_uses_typed_loader_not_python_truthiness(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("from calamus_view_preferences import", launcher)
        self.assertIn("self.word_wrap = load_text_wrap_preference(self.settings)", launcher)
        self.assertNotIn('self.word_wrap = bool(self.settings.get("word_wrap", True))', launcher)

    def test_callback_is_a_persist_then_apply_gateway(self):
        method = _method_source("on_word_wrap")
        self.assertIn("prepare_text_wrap_plan", method)
        self.assertIn('self.save_settings({"word_wrap": plan.enabled})', method)
        self.assertIn("item.set_active(plan.previous_enabled)", method)
        self.assertIn("self.word_wrap = plan.enabled", method)
        self.assertIn("self.queue_wrap_reflow()", method)
        self.assertIn("self.update_title()", method)
        self.assertIn("return True", method)
        self.assertLess(method.index("self.save_settings"), method.index("self.word_wrap = plan.enabled"))
        self.assertLess(method.index("self.word_wrap = plan.enabled"), method.index("self.queue_wrap_reflow"))

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
        method = _method_source("save_settings")
        self.assertIn("saved = self.state.save_settings(data)", method)
        self.assertIn("if saved:", method)
        self.assertIn("self.settings = data", method)
        self.assertIn("return saved", method)
        self.assertIn("data.update(overrides)", method)

    def test_runtime_adapter_uses_viewport_allocation_not_never_policy(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        editor = (ROOT / "calamus" / "calamus_editor.py").read_text(encoding="utf-8")
        apply_method = _method_source("apply_wrap_policy")
        self.assertIn("apply_text_wrap_policy", apply_method)
        self.assertNotIn("Gtk.PolicyType.NEVER", apply_method)
        self.assertIn("Gtk.PolicyType.AUTOMATIC", editor)
        self.assertIn("scroller.get_hadjustment()", editor)
        self.assertIn("self.queue_wrap_reflow()", _method_source("on_word_wrap"))
        self.assertIn("GLib.idle_add(self.apply_wrap_policy)", _method_source("queue_wrap_reflow"))

    def test_options_menu_is_not_recomposed_incidentally(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn('optm = top_menu(app, "Options")', ui)
        self.assertIn('app.word_wrap_item = Gtk.CheckMenuItem(label="Word Wrap\\tAlt+Z")', ui)
        self.assertNotIn('Gtk.CheckMenuItem(label="Text Wrap', ui)


if __name__ == "__main__":
    unittest.main()
