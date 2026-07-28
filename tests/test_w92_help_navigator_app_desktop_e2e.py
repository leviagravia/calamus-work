"""Real GTK proof for the W92 R3 hierarchical Help Navigator."""
import os
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


@unittest.skipUnless(
    os.environ.get("CALAMUS_W92_RUN_REAL_GTK") == "1",
    "set CALAMUS_W92_RUN_REAL_GTK=1 for the real W92 GTK lane",
)
class W92HelpNavigatorGtkE2E(unittest.TestCase):
    def test_real_help_opens_with_visible_hierarchical_navigator_and_menu_map(self):
        if not _display_ready():
            self.skipTest("GTK display unavailable")
        from calamus_help_dialogs import build_user_guide_dialog, select_help_topic

        widgets = build_user_guide_dialog(None, load_user_guide())
        failures = []

        def inspect_and_close():
            try:
                self.assertTrue(widgets.dialog.get_visible())
                self.assertTrue(widgets.navigator.get_visible())
                self.assertIs(widgets.topics, widgets.navigator)
                model = widgets.navigator.get_model()
                self.assertGreaterEqual(model.iter_n_children(None), 10)

                model, selected = widgets.navigator.get_selection().get_selected()
                self.assertIsNotNone(selected)
                self.assertEqual(
                    model.get_value(selected, 0),
                    "Current command menu (W92 candidate)",
                )
                current_path = model.get_path(selected)
                self.assertTrue(widgets.navigator.row_expanded(current_path))

                self.assertTrue(select_help_topic(widgets, "File"))
                _pump()
                start, end = widgets.text_view.get_buffer().get_bounds()
                body = widgets.text_view.get_buffer().get_text(start, end, True)
                self.assertIn("Writing Workspace", body)
                self.assertIn("Move Selected Item to Trash", body)

                self.assertTrue(select_help_topic(widgets, "Final Research"))
                _pump()
                start, end = widgets.text_view.get_buffer().get_bounds()
                body = widgets.text_view.get_buffer().get_text(start, end, True)
                self.assertIn("Tags", body)
                self.assertIn("Scratchpad Full", body)
                self.assertIn("after W96", body)
            except Exception as error:
                failures.append(error)
            widgets.dialog.response(Gtk.ResponseType.CLOSE)
            return False

        GLib.idle_add(inspect_and_close)
        response = widgets.dialog.run()
        widgets.dialog.destroy()
        _pump()
        if failures:
            raise failures[0]
        self.assertEqual(response, Gtk.ResponseType.CLOSE)
        print("W92_REAL_HELP_NAVIGATOR_VISIBLE=PASS")
        print("W92_REAL_HELP_HIERARCHY=PASS")
        print("W92_REAL_HELP_CURRENT_AND_FINAL_MENU=PASS")


if __name__ == "__main__":
    unittest.main()
