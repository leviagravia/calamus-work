"""GTK opacity adapter separated from the pure opacity preference model."""
from __future__ import annotations

from typing import Any

from calamus_opacity import OpacityPreference


def apply_widget_opacity(widget: Any, percent: int, *, widget_api: Any = None) -> None:
    """Apply opacity through the non-deprecated Gtk.Widget API."""
    preference = OpacityPreference(percent)
    if widget_api is None:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        widget_api = Gtk.Widget
    setter = getattr(widget_api, "set_opacity", None)
    if not callable(setter):
        raise TypeError("widget opacity API does not provide set_opacity")
    setter(widget, preference.fraction)
