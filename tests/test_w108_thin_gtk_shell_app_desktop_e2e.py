from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest.mock import patch

from tests.calamus_gtk_test_driver import (
    HAVE_GTK, Gtk, ModalDriver, close_visible_dialogs, dialog_text, display_ready, pump, visible_dialog, visible_dialogs,
)
from tests.w101_isolation_helpers import runtime_environment, runtime_paths, snapshot_tree, write_settings

ROOT = Path(__file__).resolve().parents[1]
RUN = os.environ.get("CALAMUS_W108_RUN_REAL_GTK") == "1"


def load_app():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = "w108_thin_shell_" + uuid.uuid4().hex
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin" / "calamus"))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def buffer_text(window):
    buf = window.text.get_buffer(); start, end = buf.get_bounds()
    return buf.get_text(start, end, True)


def button_with_label(widget, label):
    if isinstance(widget, Gtk.Button) and (widget.get_label() or "") == label:
        return widget
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            found = button_with_label(child, label)
            if found is not None:
                return found
    return None


@unittest.skipUnless(RUN and HAVE_GTK and display_ready(), "real W108 thin GTK shell lane")
class W108ThinGtkShellRealAppE2E(unittest.TestCase):
    def test_true_app_thin_shell_nine_command_families_and_normal_close(self):
        real_home = Path(os.environ.get("CALAMUS_REAL_HOME", os.environ.get("HOME", str(Path.home())))).resolve()
        real_config_dir = real_home / ".config" / "calamus"
        real_before = snapshot_tree(real_config_dir)

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "home"
            workspace = Path(temp) / "workspace"; workspace.mkdir()
            document = workspace / "ThinShell.md"
            document.write_text("# One\n\nalpha beta\n\n## Two\n", encoding="utf-8")
            paths = runtime_paths(home)
            write_settings(paths.calamus_config_dir, workspace, document)
            window = None
            with patch.dict(os.environ, runtime_environment(paths), clear=False):
                window = load_app().App(); window.show_all(); pump()
                try:
                    # W108 current GTK authority is behavioral only. Structural facts
                    # (39 seams, 24 aliases, 117 bindings, composition topology) are
                    # certified exclusively by source/headless lanes before packaging.
                    self.assertEqual(Path(window.document_session.file_path).resolve(), document.resolve())
                    print("W108_BEHAVIORAL_GTK_LANE_READY=PASS")

                    # EDIT family: stable command reaches the concrete shell callback.
                    self.assertTrue(window.invoke_command("edit.select-all", source="w108-true-app").success); pump()
                    self.assertTrue(window.text.get_buffer().get_has_selection())

                    # FILE family: existing-document save is bounded and does not change identity.
                    self.assertTrue(window.invoke_command("file.save", source="w108-true-app").success); pump()
                    self.assertEqual(Path(window.document_session.file_path).resolve(), document.resolve())

                    # HELP family through the real modal boundary.
                    def close_about():
                        dialog = visible_dialog("About Calamus")
                        if dialog is None: return False
                        dialog.response(Gtk.ResponseType.CLOSE); return True
                    driver = ModalDriver([close_about]); driver.start()
                    self.assertTrue(window.invoke_command("help.about", source="w108-true-app").success); pump(); driver.assert_complete()

                    # VIEW/adapter contract: Character Map is outside App, inserts through W103, and Undo restores exactly.
                    before_character = buffer_text(window)
                    buf = window.text.get_buffer(); buf.place_cursor(buf.get_end_iter())
                    def click_character():
                        dialog = visible_dialog("Character Map")
                        if dialog is None: return False
                        button = button_with_label(dialog, "Ω")
                        if button is None: return False
                        button.clicked(); return True
                    def close_character_map():
                        dialog = visible_dialog("Character Map")
                        if dialog is None: return False
                        dialog.response(Gtk.ResponseType.CLOSE); return True
                    driver = ModalDriver([click_character, close_character_map]); driver.start()
                    self.assertTrue(window.invoke_command("view.character-map", source="w108-true-app").success); pump(); driver.assert_complete()
                    self.assertEqual(buffer_text(window), before_character + "Ω")
                    self.assertTrue(window.invoke_command("edit.undo", source="w108-true-app").success); pump()
                    self.assertEqual(buffer_text(window), before_character)
                    print("W108_CHARACTER_MAP_TRUE_GTK=PASS")

                    # NAVIGATE changed-binding receipt: exercise the exact W108-rewired
                    # Navigator path, not a sibling command in the same family.
                    navigator_before = bool(window.navigator_panel_runtime.is_visible)
                    self.assertTrue(window.invoke_command("navigate.navigator-panel", source="w108-true-app").success); pump()
                    self.assertEqual(bool(window.navigator_panel_runtime.is_visible), not navigator_before)
                    self.assertTrue(window.invoke_command("navigate.navigator-panel", source="w108-true-app").success); pump()
                    self.assertEqual(bool(window.navigator_panel_runtime.is_visible), navigator_before)
                    print("W108_NAVIGATOR_PANEL_TRUE_GTK=PASS")

                    # OPTIONS family: state transition still projects through W105/W106 authorities.
                    wrap_before = bool(window.word_wrap)
                    self.assertTrue(window.invoke_command("options.word-wrap", source="w108-true-app").success); pump()
                    self.assertEqual(bool(window.word_wrap), not wrap_before)

                    # RESEARCH family: direct ResearchApplicationRuntime binding.
                    research_before = bool(window.research_panel_runtime.is_visible)
                    self.assertTrue(window.invoke_command("research.panel", source="w108-true-app").success); pump()
                    self.assertEqual(bool(window.research_panel_runtime.is_visible), not research_before)

                    # TOOLS family through real System Info modal.
                    def close_system_info():
                        dialog = visible_dialog("System Info")
                        if dialog is None: return False
                        dialog.response(Gtk.ResponseType.CLOSE); return True
                    driver = ModalDriver([close_system_info]); driver.start()
                    self.assertTrue(window.invoke_command("tools.system-info", source="w108-true-app").success); pump(); driver.assert_complete()

                    # VIEW family: concrete GTK shell keeps visual state while command authority is W104.
                    focus_before = bool(window.focus_mode)
                    self.assertTrue(window.invoke_command("view.focus-mode", source="w108-true-app").success); pump()
                    self.assertEqual(bool(window.focus_mode), not focus_before)

                    # WRITING family: typewriter runtime is a direct command port, no App forwarding method.
                    typewriter_before = bool(window.typewriter_mode)
                    self.assertTrue(window.invoke_command("writing.typewriter-mode", source="w108-true-app").success); pump()
                    self.assertEqual(bool(window.typewriter_mode), not typewriter_before)

                    # Character Map Undo restores the bytes, but W102/W103 do not yet have
                    # savepoint-aware dirty restoration. Re-establish clean state only through
                    # the public W104 file.save path before testing a clean document replacement.
                    self.assertTrue(window.invoke_command("file.save", source="w108-true-app").success); pump()

                    # CLEAN DnD receipt: real App GTK endpoint -> stable file.open-drop ->
                    # may_continue -> open_path. No modal is expected after the explicit save.
                    dropped = workspace / "Dropped.md"
                    dropped.write_text("# Dropped\n", encoding="utf-8")
                    class DropData:
                        def __init__(self, path):
                            self.path = Path(path)
                        def get_uris(self):
                            return [self.path.resolve().as_uri()]
                    with patch.object(Gtk, "drag_finish") as finish:
                        self.assertTrue(window.on_drag_data_received(window.text, object(), 0, 0, DropData(dropped), 0, 77))
                        pump()
                        self.assertEqual(finish.call_count, 1)
                        self.assertEqual(finish.call_args.args[1:], (True, False, 77))
                    self.assertEqual(Path(window.document_session.file_path).resolve(), dropped.resolve())
                    self.assertEqual(buffer_text(window), "# Dropped\n")
                    print("W108_CLEAN_DROP_TRUE_GTK=PASS")

                    # DIRTY DnD receipt: a modified current document must not be replaced
                    # silently. Drive the real Save changes? dialog to Cancel and require a
                    # fail-closed drag receipt plus exact identity/content preservation.
                    buf = window.text.get_buffer(); buf.place_cursor(buf.get_end_iter())
                    clean_dropped_text = buffer_text(window)
                    self.assertTrue(window.invoke_command("writing.insert-date", source="w108-true-app").success); pump()
                    dirty_text = buffer_text(window)
                    self.assertNotEqual(dirty_text, clean_dropped_text)
                    self.assertTrue(window.document_session.requires_save_confirmation())
                    second = workspace / "Second.md"
                    second.write_text("# Second\n", encoding="utf-8")
                    def cancel_dirty_drop():
                        for dialog in visible_dialogs():
                            if "Save changes?" not in dialog_text(dialog):
                                continue
                            button = button_with_label(dialog, "Cancel")
                            if button is None:
                                return False
                            button.clicked(); return True
                        return False
                    driver = ModalDriver([cancel_dirty_drop]); driver.start()
                    with patch.object(Gtk, "drag_finish") as finish:
                        self.assertTrue(window.on_drag_data_received(window.text, object(), 0, 0, DropData(second), 0, 78))
                        pump(); driver.assert_complete()
                        self.assertEqual(finish.call_count, 1)
                        self.assertEqual(finish.call_args.args[1:], (False, False, 78))
                    self.assertEqual(Path(window.document_session.file_path).resolve(), dropped.resolve())
                    self.assertEqual(buffer_text(window), dirty_text)
                    self.assertTrue(window.document_session.requires_save_confirmation())
                    print("W108_DIRTY_DROP_CANCEL_TRUE_GTK=PASS")

                    # Return to clean state through the public command and close through the
                    # public Quit command. No direct dirty override or may_continue bypass.
                    self.assertTrue(window.invoke_command("file.save", source="w108-true-app").success); pump()
                    self.assertEqual(dropped.read_text(encoding="utf-8"), dirty_text)
                    self.assertFalse(window.document_session.requires_save_confirmation())
                    self.assertTrue(window.invoke_command("file.quit", source="w108-true-app").success); pump()
                    self.assertTrue(window.application_lifecycle.is_shutdown)
                    print("W108_THIN_GTK_SHELL_TRUE_APP=PASS")
                finally:
                    close_visible_dialogs()
                    if window is not None and not window.application_lifecycle.is_shutdown:
                        window.destroy()
                    pump()

        self.assertEqual(real_before, snapshot_tree(real_config_dir))
        print("W108_REAL_CONFIG_UNCHANGED=PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
