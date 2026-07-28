"""Real GTK proof that W87 Help exposes complete BibTeX/BibLaTeX examples."""
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


class BibtexHelpAppDesktopE2E(unittest.TestCase):
    def test_real_user_guide_navigates_to_import_and_export_examples(self):
        if not _display_ready():
            self.skipTest("GTK display unavailable")
        from calamus_help_dialogs import build_user_guide_dialog, select_help_topic

        widgets = build_user_guide_dialog(None, load_user_guide())
        failures = []

        def inspect_and_close():
            try:
                for title, required in (
                    ("Import BibTeX/BibLaTeX", "theology-library.bib"),
                    ("Export References as BibTeX/BibLaTeX", "calamus-references.bib"),
                ):
                    self.assertTrue(select_help_topic(widgets, title))
                    _pump()
                    start, end = widgets.text_view.get_buffer().get_bounds()
                    body = widgets.text_view.get_buffer().get_text(start, end, True)
                    self.assertIn(required, body)
                    self.assertIn("references.md", body)
            except Exception as error:
                failures.append(error)
            widgets.dialog.response(Gtk.ResponseType.CLOSE)
            return False

        GLib.idle_add(inspect_and_close)
        widgets.dialog.run()
        widgets.dialog.destroy()
        _pump()
        if failures:
            raise failures[0]
        print("W87_REAL_USER_GUIDE_IMPORT_EXAMPLE=PASS")
        print("W87_REAL_USER_GUIDE_EXPORT_EXAMPLE=PASS")


if __name__ == "__main__":
    unittest.main()
