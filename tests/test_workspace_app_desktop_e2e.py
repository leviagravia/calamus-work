"""Desktop-only proofs for the real Workspace command and open lifecycle."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
import uuid

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
    HAVE_GTK = True
except Exception:
    HAVE_GTK = False

ROOT = Path(__file__).resolve().parents[1]


def _gtk_display_ready():
    if not HAVE_GTK:
        return False, "PyGObject/GTK unavailable"
    try:
        result = Gtk.init_check()
    except TypeError:
        result = Gtk.init_check(None)
    ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
    if not ok:
        return False, "Gtk.init_check() failed"
    display = Gdk.Display.get_default()
    if display is None:
        return False, "Gdk.Display.get_default() returned None"
    backend = getattr(getattr(display, "__gtype__", None), "name", type(display).__name__)
    name = display.get_name() if hasattr(display, "get_name") else "unknown"
    return True, f"backend={backend} name={name}"


def _pump():
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def _write_settings(workspace):
    config = Path.home() / ".config" / "calamus"
    config.mkdir(parents=True, exist_ok=True)
    (config / "settings.json").write_text(
        json.dumps(
            {
                "width": 900,
                "height": 650,
                "appearance_mode": "dark",
                "dark_mode": True,
                "workspace_root": str(Path(workspace).resolve()),
                "workspace_visible": True,
                "last_file": None,
                "word_wrap": True,
                "line_numbers": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _load_app_module():
    os.environ["CALAMUS_LIB_DIR"] = str(ROOT / "calamus")
    os.environ["CALAMUS_SOURCE_ROOT"] = str(ROOT)
    if str(ROOT / "calamus") not in sys.path:
        sys.path.insert(0, str(ROOT / "calamus"))
    name = f"calamus_w79_app_{uuid.uuid4().hex}"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _activate_relative(win, relative):
    tree = win.workspace_panel_view.tree
    tree_path = tree.path_for_relative(relative)
    if tree_path is None:
        raise AssertionError(f"Workspace tree path unavailable: {relative}")
    tree.expand_to_path(tree_path)
    tree.emit("row-activated", tree_path, tree.get_column(0))
    _pump()


class WorkspaceAppDesktopE2E(unittest.TestCase):
    def _require_environment(self):
        workspace = os.environ.get("CALAMUS_W79_E2E_WORKSPACE")
        alt_workspace = os.environ.get("CALAMUS_W79_E2E_ALT_WORKSPACE")
        if not workspace or not os.path.isdir(workspace):
            self.skipTest("CALAMUS_W79_E2E_WORKSPACE unavailable")
        if not alt_workspace or not os.path.isdir(alt_workspace):
            self.skipTest("CALAMUS_W79_E2E_ALT_WORKSPACE unavailable")
        ready, detail = _gtk_display_ready()
        if not ready:
            self.skipTest(
                f"GTK display unavailable: {detail}; "
                f"DISPLAY={os.environ.get('DISPLAY')!r}; "
                f"WAYLAND_DISPLAY={os.environ.get('WAYLAND_DISPLAY')!r}"
            )
        print(f"W79_E2E_GTK_DISPLAY=PASS {detail}")
        return os.path.abspath(workspace), os.path.abspath(alt_workspace)

    def test_menu_root_change_recent_and_navigate_use_operational_panel(self):
        workspace, alt_workspace = self._require_environment()
        _write_settings(workspace)
        module = _load_app_module()
        win = module.App()
        try:
            win.show_all()
            _pump()

            original_chooser = module.choose_workspace_folder
            module.choose_workspace_folder = lambda _parent, _initial=None: alt_workspace
            try:
                self.assertTrue(win.on_select_workspace_folder())
            finally:
                module.choose_workspace_folder = original_chooser
            _pump()

            self.assertEqual(win.workspace_application_runtime.root, alt_workspace)
            self.assertTrue(win.workspace_panel_runtime.is_visible)
            alt_target = os.path.join(alt_workspace, "Alternative_Document.md")
            expected = Path(alt_target).read_text(encoding="utf-8")
            _activate_relative(win, "Alternative_Document.md")
            self.assertEqual(win.current_file, os.path.abspath(alt_target))
            self.assertEqual(win.buffer_text(), expected)
            print("W79_REAL_APP_SELECT_COMMAND=PASS")

            win.workspace_panel_runtime.hide()
            self.assertFalse(win.workspace_panel_runtime.is_visible)
            win.workspace_show_item.activate()
            _pump()
            self.assertTrue(win.workspace_panel_runtime.is_visible)
            self.assertEqual(win.workspace_application_runtime.root, alt_workspace)
            print("W79_REAL_APP_FILE_SHOW_COMMAND=PASS")

            win.on_close_workspace()
            self.assertIsNone(win.workspace_application_runtime.root)
            self.assertFalse(win.workspace_panel_runtime.is_visible)
            win.populate_recent_workspaces_menu()
            recent_item = next(
                (
                    child
                    for child in win.recent_workspaces_menu.get_children()
                    if child.get_label() == alt_workspace
                ),
                None,
            )
            self.assertIsNotNone(recent_item)
            recent_item.activate()
            _pump()
            self.assertEqual(win.workspace_application_runtime.root, alt_workspace)
            self.assertTrue(win.workspace_panel_runtime.is_visible)
            _activate_relative(win, "Alternative_Document.md")
            self.assertEqual(win.current_file, os.path.abspath(alt_target))
            print("W79_REAL_APP_RECENT_COMMAND=PASS")

            win.workspace_panel_runtime.hide()
            self.assertFalse(win.workspace_panel_runtime.is_visible)
            win.workspace_item.set_active(True)
            _pump()
            self.assertTrue(win.workspace_panel_runtime.is_visible)
            self.assertEqual(win.workspace_application_runtime.root, alt_workspace)
            _activate_relative(win, "Alternative_Document.md")
            self.assertEqual(win.current_file, os.path.abspath(alt_target))
            print("W79_REAL_APP_NAVIGATE_COMMAND=PASS")
            print("W79_REAL_APP_COMMAND_LIFECYCLE=PASS")
        finally:
            win.destroy()
            _pump()


    def test_real_app_new_text_file_command_creates_rescans_selects_and_opens(self):
        workspace, _alt_workspace = self._require_environment()
        _write_settings(workspace)
        drafts = os.path.join(workspace, "01_Drafts")
        target = os.path.join(drafts, "W80_Created.md")
        try:
            os.unlink(target)
        except FileNotFoundError:
            pass
        module = _load_app_module()
        win = module.App()
        try:
            win.show_all()
            _pump()
            self.assertTrue(win.workspace_panel_view.tree.select_absolute_path(drafts))
            self.assertTrue(win.create_workspace_text_file("W80_Created", ".md"))
            _pump()
            self.assertTrue(os.path.isfile(target))
            self.assertEqual(Path(target).read_bytes(), b"")
            self.assertEqual(win.current_file, os.path.abspath(target))
            self.assertEqual(win.buffer_text(), "")
            self.assertIn(os.path.abspath(target), win.state.load_recent_files())
            selected = win.workspace_panel_view.selected_item()
            self.assertIsNotNone(selected)
            self.assertEqual(selected.path, os.path.abspath(target))
            self.assertTrue(win.workspace_new_text_file_item.get_sensitive())
            print("W80_REAL_APP_NEW_TEXT_FILE=PASS")
            print("W80_REAL_APP_RESCAN_SELECT_OPEN=PASS")
        finally:
            win.destroy()
            _pump()
            try:
                os.unlink(target)
            except FileNotFoundError:
                pass


    def test_real_app_new_folder_command_creates_rescans_and_selects_without_opening(self):
        workspace, _alt_workspace = self._require_environment()
        _write_settings(workspace)
        drafts = os.path.join(workspace, "01_Drafts")
        target = os.path.join(drafts, "W81_Created_Folder")
        if os.path.isdir(target):
            os.rmdir(target)
        module = _load_app_module()
        win = module.App()
        try:
            win.show_all()
            _pump()
            _activate_relative(win, "01_Drafts/Capitolo_1.md")
            current_before = win.current_file
            buffer = win.text.get_buffer()
            buffer.set_text(win.buffer_text() + "\nUnsaved W81 marker")
            _pump()
            text_before = win.buffer_text()
            self.assertTrue(win.workspace_panel_view.tree.select_absolute_path(drafts))
            self.assertTrue(win.create_workspace_folder("W81_Created_Folder"))
            _pump()
            self.assertTrue(os.path.isdir(target))
            self.assertFalse(os.path.islink(target))
            self.assertEqual(win.current_file, current_before)
            self.assertEqual(win.buffer_text(), text_before)
            selected = win.workspace_panel_view.selected_item()
            self.assertIsNotNone(selected)
            self.assertEqual(selected.path, os.path.abspath(target))
            self.assertTrue(selected.is_directory)
            self.assertTrue(win.workspace_new_folder_item.get_sensitive())
            print("W81_REAL_APP_NEW_FOLDER=PASS")
            print("W81_REAL_APP_RESCAN_SELECT=PASS")
            print("W81_ACTIVE_DOCUMENT_UNCHANGED=PASS")
        finally:
            win.destroy()
            _pump()
            if os.path.isdir(target):
                os.rmdir(target)

    def test_real_app_opens_real_workspace_file_from_real_tree_signal(self):
        workspace, _alt_workspace = self._require_environment()
        _write_settings(workspace)
        target = os.path.join(workspace, "01_Drafts", "Capitolo_1.md")
        expected = Path(target).read_text(encoding="utf-8")
        module = _load_app_module()
        win = module.App()
        try:
            win.show_all()
            _pump()
            self.assertEqual(win.workspace_application_runtime.root, workspace)
            self.assertTrue(win.workspace_panel_runtime.is_visible)
            _activate_relative(win, "01_Drafts/Capitolo_1.md")
            self.assertEqual(win.current_file, os.path.abspath(target))
            self.assertEqual(win.buffer_text(), expected)
            self.assertIn(os.path.abspath(target), win.state.load_recent_files())

            self.assertEqual(win.workspace_panel_view.widget.get_size_request()[0], -1)
            self.assertTrue(
                win.workspace_paned.child_get_property(
                    win.workspace_panel_view.widget, "shrink"
                )
            )
            self.assertIsNotNone(win.workspace_file_item.get_submenu())

            requisitions = (
                ("window", win),
                ("root-box", win.get_child()),
                ("menubar", win.menubar),
                ("status-line", win.status),
                ("workspace-paned", win.workspace_paned),
                ("workspace-panel", win.workspace_panel_view.widget),
                ("workspace-header", win.workspace_panel_view.header),
                ("workspace-actions", win.workspace_panel_view.action_row),
                ("workspace-root-label", win.workspace_panel_view.root_label),
                ("workspace-scroll", win.workspace_panel_view.scroll),
                ("workspace-tree", win.workspace_panel_view.tree),
                ("editor-box", win.editor_box),
            )
            preferred = {}
            for name, widget in requisitions:
                minimum, natural = widget.get_preferred_width()
                preferred[name] = (minimum, natural)
                print(
                    f"W79_WIDTH_REQUISITION name={name} "
                    f"min={minimum} natural={natural}"
                )
            self.assertEqual(
                win.workspace_panel_view.root_label.get_text(),
                os.path.basename(workspace),
            )
            self.assertEqual(
                win.workspace_panel_view.root_label.get_tooltip_text(),
                workspace,
            )
            self.assertLessEqual(preferred["workspace-panel"][0], 300)
            self.assertLessEqual(preferred["workspace-root-label"][0], 220)
            self.assertLessEqual(preferred["workspace-paned"][0], 700)
            self.assertLessEqual(preferred["status-line"][0], 240)
            self.assertLessEqual(preferred["root-box"][0], 700)
            self.assertNotIn(os.path.abspath(target), win.status.get_text())
            self.assertIn(os.path.basename(target), win.status.get_text())
            self.assertIn(os.path.abspath(target), win.status.get_tooltip_text())
            print("W79_STATUS_REQUISITION=PASS")
            print("W79_WORKSPACE_REQUISITION=PASS")

            win.present()
            _pump()
            observed = []
            loop = GLib.MainLoop()

            def on_configure(_window, event):
                observed.append((event.width, event.height))
                if (
                    event.width <= 700
                    and event.height <= 520
                    and loop.is_running()
                ):
                    loop.quit()
                return False

            handler = win.connect("configure-event", on_configure)
            try:
                win.resize(620, 440)

                def stop_waiting():
                    if loop.is_running():
                        loop.quit()
                    return False

                GLib.timeout_add(1800, stop_waiting)
                loop.run()
            finally:
                win.disconnect(handler)
            _pump()
            width, height = win.get_size()
            self.assertLessEqual(
                width,
                700,
                f"window refused shrink; final={width}x{height}; "
                f"configure-events={observed!r}",
            )
            self.assertLessEqual(height, 520)
            print(
                f"W79_REAL_APP_RESIZE=PASS size={width}x{height} "
                f"events={observed!r}"
            )
            print("W79_REAL_APP_GEOMETRY=PASS")
            print("W79_REAL_APP_E2E=PASS")
        finally:
            win.destroy()
            _pump()


if __name__ == "__main__":
    unittest.main(verbosity=2)
