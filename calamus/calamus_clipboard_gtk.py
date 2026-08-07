"""Tiny GTK clipboard adapter used by W107 subsystem ports."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk


def copy_text(text: str) -> bool:
    if not isinstance(text, str):
        return False
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(text, -1)
    clipboard.store()
    return True
