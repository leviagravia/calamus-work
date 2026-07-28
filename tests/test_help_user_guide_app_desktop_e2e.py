"""Real GTK proof for the Calamus User Guide."""
import unittest

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
    HAVE_GTK = True
except Exception:
    HAVE_GTK = False

from calamus_help import load_user_guide


def _display_ready():
    if not HAVE_GTK:
        return False
    try:
        result = Gtk.init_check()
    except TypeError:
        result = Gtk.init_check(None)
    ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
    return bool(ok and Gdk.Display.get_default() is not None)


def _pump():
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


class UserGuideAppDesktopE2E(unittest.TestCase):
    def test_real_dialog_navigates_to_tag_integrity_example(self):
        if not _display_ready():
            self.skipTest("GTK display unavailable")
        from calamus_help_dialogs import build_user_guide_dialog, select_help_topic

        widgets = build_user_guide_dialog(None, load_user_guide())
        dialog = widgets.dialog
        failures = []

        def inspect_and_close():
            try:
                self.assertTrue(dialog.get_visible())
                self.assertTrue(widgets.navigator.get_visible())
                self.assertGreaterEqual(len(widgets.help_topics), 20)
                self.assertTrue(select_help_topic(widgets, "Tag Integrity"))
                _pump()
                start, end = widgets.text_view.get_buffer().get_bounds()
                body = widgets.text_view.get_buffer().get_text(start, end, True)
                self.assertIn("Only the logical variants of `Faith` become `doctrine`", body)
                self.assertIn("unrelated tags", body)
            except Exception as error:
                failures.append(error)
            dialog.response(Gtk.ResponseType.CLOSE)
            return False

        GLib.idle_add(inspect_and_close)
        response = dialog.run()
        dialog.destroy()
        _pump()
        if failures:
            raise failures[0]
        self.assertEqual(response, Gtk.ResponseType.CLOSE)
        print("W86_REAL_USER_GUIDE_DIALOG=PASS")
        print("W86_REAL_RESEARCH_EXAMPLE=PASS")


if __name__ == "__main__":
    unittest.main()
