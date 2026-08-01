"""Fresh-process real-GTK proof for ModalSession ownership."""
from __future__ import annotations

import unittest

from tests.calamus_gtk_test_driver import HAVE_GTK, GLib, Gtk, display_ready, visible_dialogs

if HAVE_GTK:
    from calamus_modal_dialog import ModalSession


@unittest.skipUnless(HAVE_GTK and display_ready(), "real GTK display required")
class ModalDialogGtkSessionTests(unittest.TestCase):
    def test_response_hide_source_cleanup_and_destroy_are_owned(self):
        dialog = Gtk.Dialog(title="W90 Modal Session Proof", modal=True)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.show_all()
        state = {"active": False, "removed": False}
        session = ModalSession(dialog)

        def respond_once():
            state["active"] = False
            dialog.response(Gtk.ResponseType.CANCEL)
            return False

        def remove_source(source_id):
            if state["active"]:
                GLib.source_remove(source_id)
                state["active"] = False
                state["removed"] = True

        source_id = GLib.idle_add(respond_once)
        state["active"] = True
        session.register_source(source_id, remove_source)
        with session:
            response = session.run()
            self.assertEqual(response, Gtk.ResponseType.CANCEL)
            self.assertFalse(dialog.get_visible())
            self.assertFalse(session.closed)
        self.assertTrue(session.closed)
        self.assertEqual(session.source_count, 0)
        self.assertFalse(any(window.get_title() == "W90 Modal Session Proof" for window in visible_dialogs()))
        print("W90_MODAL_SESSION_RESPONSE=PASS")
        print("W90_MODAL_SESSION_HIDE_BEFORE_DESTROY=PASS")
        print("W90_MODAL_SESSION_SOURCE_OWNERSHIP=PASS")


if __name__ == "__main__":
    unittest.main()
