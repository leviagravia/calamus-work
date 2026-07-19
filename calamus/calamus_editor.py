"""Editor widget construction helpers.

Invariant: the Gtk.TextView must be the direct child of Gtk.ScrolledWindow.
This preserves native GTK caret and selection scrolling.
"""
from __future__ import annotations

from gi.repository import Gtk, Gdk

from calamus_layout import (
    LINE_GUTTER_MIN_WIDTH,
    EDITOR_MIN_CONTENT_WIDTH,
    EDITOR_MIN_CONTENT_HEIGHT,
    LINE_GUTTER_MIN_CONTENT_HEIGHT,
)


def _contain_scrolled_window(scroller, *, min_width=None, min_height=None):
    """Make a Gtk.ScrolledWindow absorb child growth instead of exporting it.

    This is the core geometry guard for Calamus Standard Edition: document
    length and wrapped-line height must change the scroll adjustments, not the
    GtkWindow requisition.
    """
    if hasattr(scroller, "set_propagate_natural_height"):
        scroller.set_propagate_natural_height(False)
    if hasattr(scroller, "set_propagate_natural_width"):
        scroller.set_propagate_natural_width(False)
    if min_width is not None and hasattr(scroller, "set_min_content_width"):
        scroller.set_min_content_width(min_width)
    if min_height is not None and hasattr(scroller, "set_min_content_height"):
        scroller.set_min_content_height(min_height)
    scroller.set_hexpand(min_width is not None)
    scroller.set_vexpand(True)


def build_editor_widgets(word_wrap: bool):
    editor_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    editor_box.set_hexpand(True)
    editor_box.set_vexpand(True)

    # Keep the line-number widget inside its own vertical scroller. A bare Gtk.Label
    # containing thousands of newline-separated numbers reports a huge natural
    # height and can force the top-level window to grow with document length.
    # IMPORTANT: the vertical policy must be scrollable (AUTOMATIC), not NEVER.
    # With NEVER, GTK may treat the full label height as the gutter's minimum
    # height, so pressing Enter repeatedly can stretch the program window.
    line_scroller = Gtk.ScrolledWindow()
    line_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    line_scroller.set_size_request(LINE_GUTTER_MIN_WIDTH, 1)
    _contain_scrolled_window(line_scroller, min_height=LINE_GUTTER_MIN_CONTENT_HEIGHT)
    line_scroller.set_hexpand(False)
    editor_box.pack_start(line_scroller, False, False, 0)

    line_numbers = Gtk.Label()
    line_numbers.set_xalign(1)
    line_numbers.set_yalign(0)
    line_numbers.set_margin_start(2)
    line_numbers.set_margin_end(3)
    line_numbers.set_margin_top(10)
    line_numbers.set_selectable(False)
    line_numbers.set_size_request(LINE_GUTTER_MIN_WIDTH - 5, 1)
    line_scroller.add(line_numbers)

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    _contain_scrolled_window(
        scroller,
        min_width=EDITOR_MIN_CONTENT_WIDTH,
        min_height=EDITOR_MIN_CONTENT_HEIGHT,
    )
    editor_box.pack_start(scroller, True, True, 0)

    text = Gtk.TextView()
    text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR if word_wrap else Gtk.WrapMode.NONE)
    text.set_left_margin(10)
    text.set_right_margin(10)
    text.set_top_margin(10)
    text.set_bottom_margin(10)
    # The TextView remains the direct child of scroller.  It may expand inside
    # the viewport, but its natural size is contained by the ScrolledWindow.
    text.set_hexpand(True)
    text.set_vexpand(True)
    text.add_events(
        Gdk.EventMask.BUTTON_PRESS_MASK
        | Gdk.EventMask.BUTTON_RELEASE_MASK
        | Gdk.EventMask.POINTER_MOTION_MASK
        | Gdk.EventMask.KEY_PRESS_MASK
        | Gdk.EventMask.KEY_RELEASE_MASK
    )
    scroller.add(text)

    def sync_gutter_scroll(adj):
        try:
            line_scroller.get_vadjustment().set_value(adj.get_value())
        except Exception:
            pass

    scroller.get_vadjustment().connect("value-changed", sync_gutter_scroll)
    return editor_box, line_numbers, scroller, text


def apply_text_wrap_policy(text, scroller, enabled: bool) -> bool:
    """Apply soft wrap without giving the TextView a virtual line width.

    Gtk.TextView performs soft wrapping from its allocated viewport width.  The
    surrounding scroller therefore keeps its normal AUTOMATIC policies; forcing
    the horizontal policy to NEVER can leave the child allocated to the natural
    width of a long line, so changing wrap-mode produces no visible reflow.
    """
    if not isinstance(enabled, bool):
        raise TypeError("enabled must be boolean")
    text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR if enabled else Gtk.WrapMode.NONE)
    scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    if enabled:
        adjustment = scroller.get_hadjustment()
        if adjustment is not None:
            adjustment.set_value(adjustment.get_lower())
    scroller.queue_resize()
    text.queue_resize()
    return enabled


def assert_textview_direct_child(scroller, text) -> bool:
    return scroller.get_child() is text
