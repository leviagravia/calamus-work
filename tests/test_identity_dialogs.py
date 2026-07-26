"""Owned component proofs for About and System Info dialogs."""
from __future__ import annotations

import unittest

from calamus_gtk_test_driver import HAVE_GTK, Gtk, display_ready

if HAVE_GTK:
    from calamus_identity_dialogs import (
        AboutDialogWidgets,
        SystemInfoDialogWidgets,
        build_about_dialog,
        build_system_info_dialog,
    )
    from calamus_modal_dialog import destroy_modal
    from calamus_runtime_identity import build_runtime_identity


@unittest.skipUnless(HAVE_GTK and display_ready(), "real GTK display required")
class IdentityDialogComponentTests(unittest.TestCase):
    def setUp(self):
        self.parent = Gtk.Window()

    def tearDown(self):
        self.parent.destroy()

    @staticmethod
    def _text(view):
        buffer = view.get_buffer()
        start, end = buffer.get_bounds()
        return buffer.get_text(start, end, True)

    def test_about_builder_returns_exact_owned_widgets(self):
        identity = build_runtime_identity(
            "Development build",
            "W89",
            "569dd742abd607bb55a1e6bf9efbad1fdba1684c",
        )
        widgets = build_about_dialog(self.parent, identity)
        try:
            self.assertIsInstance(widgets, AboutDialogWidgets)
            self.assertEqual(widgets.dialog.get_title(), "About Calamus")
            self.assertEqual(widgets.dialog.get_name(), "calamus-about-dialog")
            self.assertIs(widgets.dialog.get_transient_for(), self.parent)
            self.assertEqual(widgets.text_view.get_name(), "calamus-about-text")
            body = self._text(widgets.text_view)
            self.assertEqual(body.splitlines()[0], "Calamus")
            self.assertNotIn("Calamus-Working-Copy", body)
            print("W89_IDENTITY_COMPONENT_ABOUT=PASS")
        finally:
            destroy_modal(widgets.dialog)

    def test_system_info_builder_returns_exact_owned_widgets(self):
        body = (
            "Calamus: Development build\n"
            "Work item: W89\n"
            "Published baseline: 569dd742abd607bb55a1e6bf9efbad1fdba1684c"
        )
        widgets = build_system_info_dialog(self.parent, body)
        try:
            self.assertIsInstance(widgets, SystemInfoDialogWidgets)
            self.assertEqual(widgets.dialog.get_title(), "System Info")
            self.assertEqual(
                widgets.dialog.get_name(),
                "calamus-system-info-dialog",
            )
            self.assertIs(widgets.dialog.get_transient_for(), self.parent)
            self.assertEqual(
                widgets.text_view.get_name(),
                "calamus-system-info-text",
            )
            self.assertEqual(self._text(widgets.text_view), body)
            print("W89_IDENTITY_COMPONENT_SYSTEM_INFO=PASS")
        finally:
            destroy_modal(widgets.dialog)


if __name__ == "__main__":
    unittest.main()
