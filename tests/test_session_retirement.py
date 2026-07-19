import ast
from pathlib import Path
import tempfile
import unittest

from calamus_state import StateManager


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
SHORTCUTS = ROOT / "calamus" / "calamus_shortcuts.py"
STATE = ROOT / "calamus" / "calamus_state.py"
CONFIG = ROOT / "calamus" / "calamus_config.py"
DIALOGS = ROOT / "calamus" / "calamus_dialogs.py"


class SessionRetirementTests(unittest.TestCase):
    def test_file_menu_no_longer_exposes_manual_session_commands(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertNotIn("Save Session", ui)
        self.assertNotIn("Reopen Last Session", ui)
        self.assertNotIn("app.on_save_session", ui)
        self.assertNotIn("app.on_restore_session", ui)

    def test_manual_session_shortcuts_are_unbound(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertNotIn('(\"<Control><Alt>S\", app.on_save_session)', ui)
        self.assertNotIn('(\"<Control><Alt>O\", app.on_restore_session)', ui)

    def test_shortcut_guide_no_longer_advertises_sessions(self):
        shortcuts = SHORTCUTS.read_text(encoding="utf-8")
        self.assertNotIn("Save Session", shortcuts)
        self.assertNotIn("Reopen Last Session", shortcuts)
        self.assertNotIn('ShortcutSpec("File", "Save Session"', shortcuts)
        self.assertNotIn('ShortcutSpec("File", "Reopen Last Session"', shortcuts)

    def test_launcher_no_longer_contains_manual_session_callbacks(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        tree = ast.parse(launcher)
        names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertNotIn("on_save_session", names)
        self.assertNotIn("on_restore_session", names)

    def test_state_manager_no_longer_owns_session_persistence(self):
        state_source = STATE.read_text(encoding="utf-8")
        self.assertNotIn("session_file", state_source)
        self.assertNotIn("def load_session", state_source)
        self.assertNotIn("def save_session", state_source)
        with tempfile.TemporaryDirectory() as td:
            state = StateManager(td)
            self.assertFalse(hasattr(state, "session_file"))
            self.assertFalse(hasattr(state, "load_session"))
            self.assertFalse(hasattr(state, "save_session"))

    def test_config_no_longer_declares_session_store(self):
        config = CONFIG.read_text(encoding="utf-8")
        self.assertNotIn("SESSION_FILE", config)
        self.assertNotIn('"session.json"', config)

    def test_about_dialog_no_longer_claims_session_restore(self):
        dialogs = DIALOGS.read_text(encoding="utf-8")
        self.assertNotIn("- Session restore", dialogs)

    def test_file_menu_flows_from_print_block_to_quit_without_session_block(self):
        ui = UI.read_text(encoding="utf-8")
        print_pos = ui.index('add_item(filem, "Print…\\tCtrl+P", app.on_print)')
        quit_pos = ui.index('add_item(filem, "Quit\\tCtrl+Q", app.on_quit)')
        between = ui[print_pos:quit_pos]
        self.assertEqual(between.count("add_separator(filem)"), 1)
        self.assertNotIn("Session", between)

    def test_runtime_sources_have_no_manual_session_identity(self):
        runtime_files = (
            LAUNCHER,
            UI,
            SHORTCUTS,
            STATE,
            CONFIG,
            DIALOGS,
        )
        combined = "\n".join(path.read_text(encoding="utf-8") for path in runtime_files)
        for forbidden in (
            "on_save_session",
            "on_restore_session",
            "Save Session",
            "Reopen Last Session",
            "SESSION_FILE",
            "session_file",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
