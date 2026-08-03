"""Real GTK/App proof for W95extra Typewriter Mode and the Writing menu."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("CALAMUS_SOURCE_ROOT", str(ROOT))
os.environ.setdefault("CALAMUS_LIB_DIR", str(ROOT / "calamus"))

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
    HAVE_GTK = True
except Exception:
    HAVE_GTK = False


def display_ready() -> bool:
    if not HAVE_GTK:
        return False
    try:
        result = Gtk.init_check()
    except TypeError:
        result = Gtk.init_check(None)
    ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
    return bool(ok and Gdk.Display.get_default() is not None)


def pump() -> None:
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def until(predicate, message: str, iterations: int = 800) -> None:
    for _ in range(iterations):
        pump()
        if predicate():
            return
        GLib.usleep(1_000)
    raise AssertionError(message)


def load_launcher():
    name = "calamus_w95extra_real_app"
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / "bin/calamus"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("could not create launcher spec")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def menu_labels(menu):
    return [child.get_label() for child in menu.get_children() if hasattr(child, "get_label")]


@unittest.skipUnless(
    os.environ.get("CALAMUS_W95EXTRA_RUN_REAL_GTK") == "1",
    "set CALAMUS_W95EXTRA_RUN_REAL_GTK=1 for the real W95extra GTK lane",
)
class W95ExtraTypewriterAppDesktopE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not display_ready():
            raise unittest.SkipTest("GTK display unavailable")
        cls.temp_home = tempfile.TemporaryDirectory(prefix="calamus-w95extra-gtk-")
        os.environ["HOME"] = cls.temp_home.name
        os.environ["XDG_CONFIG_HOME"] = str(Path(cls.temp_home.name) / ".config")
        cls.launcher = load_launcher()

    @classmethod
    def tearDownClass(cls):
        cls.temp_home.cleanup()

    def setUp(self):
        self.app = self.launcher.App()
        self.app.show_all()
        self.app.resize(1100, 760)
        pump()

    def tearDown(self):
        if self.app is not None:
            self.app.destroy()
            pump()
            self.app = None

    def find_top_menu(self, label):
        for item in self.app.menubar.get_children():
            if item.get_label() == label:
                return item.get_submenu()
        self.fail(f"missing top-level menu: {label}")

    def test_real_writing_menu_typewriter_projection_and_help(self):
        roots = [item.get_label() for item in self.app.menubar.get_children()]
        self.assertIn("Writing", roots)
        self.assertLess(roots.index("Navigate"), roots.index("Writing"))
        self.assertLess(roots.index("Writing"), roots.index("Revise"))
        writing = self.find_top_menu("Writing")
        navigate = self.find_top_menu("Navigate")
        revise = self.find_top_menu("Revise")
        labels = [label for label in menu_labels(writing) if label]
        self.assertEqual(
            labels,
            [
                "Typewriter Mode\tShift+F9",
                "Insert Date",
                "Insert Time",
                "Insert Date and Time\tCtrl+Alt+D",
            ],
        )
        navigate_labels = [label for label in menu_labels(navigate) if label]
        revise_labels = [label for label in menu_labels(revise) if label]
        for label in (
            "Insert Bookmark Here\tCtrl+F2",
            "Next Bookmark\tF2",
            "Previous Bookmark\tShift+F2",
            "Manage Bookmarks…",
        ):
            self.assertIn(label, navigate_labels)
            self.assertNotIn(label, revise_labels)
        for label in (
            "Paste Clean from PDF\tCtrl+Alt+V",
            "Clean Selected Text from PDF\tCtrl+Alt+Shift+V",
        ):
            self.assertIn(label, revise_labels)
            self.assertNotIn(label, labels)
        for label in ("Insert Date", "Insert Time", "Insert Date and Time\tCtrl+Alt+D"):
            self.assertNotIn(label, revise_labels)
        self.assertFalse(self.app.typewriter_item.get_active())

        lines = [f"Visual line {index:03d}: alpha beta gamma delta epsilon zeta." for index in range(1, 181)]
        self.app.set_buffer("\n".join(lines), modified=False)
        offset = self.app.buffer_text().index("Visual line 110")
        self.app.set_cursor_offset(offset)
        pump()
        self.app.typewriter_item.set_active(True)
        until(
            lambda: (
                self.app.typewriter_runtime.reached
                and not self.app.viewport_runtime.reveal_pending
                and self.app.viewport_runtime.scroll_source is None
            ),
            "Typewriter Mode did not reach a stable measured projection",
        )
        self.assertTrue(self.app.typewriter_runtime.enabled)
        self.assertTrue(self.app.typewriter_item.get_active())
        self.assertGreater(
            self.app.text.get_bottom_margin(),
            self.app.viewport_runtime.base_bottom_margin,
        )
        buffer = self.app.text.get_buffer()
        iterator = buffer.get_iter_at_mark(buffer.get_insert())
        caret = self.app.text.get_iter_location(iterator)
        visible = self.app.text.get_visible_rect()
        caret_center = caret.y + max(1, caret.height) / 2
        target = visible.y + visible.height * 0.5
        self.assertLessEqual(abs(caret_center - target), max(8, caret.height))

        # The runtime contract deliberately suppresses semantic projection while
        # the editor lacks focus.  Establish the real GTK focus authority instead
        # of relying on window-manager default focus, which is nondeterministic.
        self.app.present()
        self.app.set_focus(self.app.text)
        self.app.text.grab_focus()
        until(
            lambda: self.app.text.has_focus(),
            "Editor did not acquire focus for the keyboard-resume proof",
        )

        before_manual = self.app.scroller.get_vadjustment().get_value()
        self.app.typewriter_runtime.on_scroll()
        self.app.scroller.get_vadjustment().set_value(max(0, before_manual - 120))
        pump()
        self.assertTrue(self.app.typewriter_runtime.manual_scroll_suspended)
        manual_value = self.app.scroller.get_vadjustment().get_value()

        # Exercise the same App signal bridge used by a real keyboard movement:
        # key press owns the semantic adjustment, move-cursor requests projection,
        # and key release ends that ownership.
        self.app.on_text_key_press(self.app.text, None)
        try:
            self.app.on_text_move_cursor(self.app.text, None, 0, False)
            until(
                lambda: (
                    not self.app.viewport_runtime.reveal_pending
                    and self.app.viewport_runtime.scroll_source is None
                ),
                "Typewriter Mode did not resume after semantic keyboard movement",
            )
        finally:
            self.app.on_text_key_release(self.app.text, None)
        self.assertFalse(self.app.typewriter_runtime.manual_scroll_suspended)
        self.assertNotEqual(self.app.scroller.get_vadjustment().get_value(), manual_value)

        base = self.app.viewport_runtime.base_bottom_margin
        self.app.typewriter_item.set_active(False)
        until(
            lambda: self.app.text.get_bottom_margin() == base,
            "Typewriter Mode did not restore the exact bottom margin",
        )
        self.assertFalse(self.app.typewriter_runtime.enabled)

        self.app.set_buffer("", modified=False)
        items = {item.get_label(): item for item in self.find_top_menu("Writing").get_children() if hasattr(item, "get_label") and item.get_label()}
        items["Insert Date"].activate()
        self.assertRegex(self.app.buffer_text(), r"^\d{4}-\d{2}-\d{2}$")
        self.app.set_buffer("", modified=False)
        items["Insert Time"].activate()
        self.assertRegex(self.app.buffer_text(), r"^\d{2}:\d{2}$")
        self.app.set_buffer("", modified=False)
        items["Insert Date and Time\tCtrl+Alt+D"].activate()
        self.assertRegex(self.app.buffer_text(), r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

        from calamus_help import load_user_guide
        from calamus_help_dialogs import build_user_guide_dialog, select_help_topic
        widgets = build_user_guide_dialog(self.app, load_user_guide(ROOT))
        try:
            self.assertTrue(select_help_topic(widgets, "Writing"))
            pump()
            start, end = widgets.text_view.get_buffer().get_bounds()
            body = widgets.text_view.get_buffer().get_text(start, end, True)
            for expected in ("Typewriter Mode", "Insert Date", "Insert Time", "Insert Date and Time"):
                self.assertIn(expected, body)
            self.assertTrue(select_help_topic(widgets, "Typewriter Mode"))
            pump()
            start, end = widgets.text_view.get_buffer().get_bounds()
            body = widgets.text_view.get_buffer().get_text(start, end, True)
            self.assertIn("view policy", body)
            self.assertIn("wheel, touchpad or scrollbar", body)
            self.assertIn("used manually", body)
            self.assertIn("resumes the mode", body)
            self.assertIn("never", body)
        finally:
            widgets.dialog.destroy()
            pump()

        print("W95EXTRA_REAL_WRITING_MENU=PASS")
        print("W95EXTRA_REAL_MENU_TAXONOMY=PASS")
        print("W95EXTRA_REAL_TYPEWRITER_MIDPOINT=PASS")
        print("W95EXTRA_REAL_MANUAL_SCROLL_RESUME=PASS")
        print("W95EXTRA_REAL_DISABLE_RESTORE=PASS")
        print("W95EXTRA_REAL_DATE_TIME_COMMANDS=PASS")
        print("W95EXTRA_REAL_HELP=PASS")


if __name__ == "__main__":
    unittest.main()
