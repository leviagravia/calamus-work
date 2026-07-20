"""Editor widget construction helpers.

Invariant: the Gtk.TextView must be the direct child of Gtk.ScrolledWindow.
This preserves native GTK caret and selection scrolling.
"""
from __future__ import annotations

from gi.repository import Gtk, Gdk

from calamus_line_numbers import LineGutterAdapter
from calamus_layout import (
    LINE_GUTTER_MIN_WIDTH,
    EDITOR_MIN_CONTENT_WIDTH,
    EDITOR_MIN_CONTENT_HEIGHT,
)


def _contain_scrolled_window(scroller, *, min_width=None, min_height=None):
    """Make a Gtk.ScrolledWindow absorb child growth instead of exporting it."""
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

    # The gutter is a viewport-sized drawing surface, not a second scrolling
    # text widget.  Its draw adapter asks GtkTextView for the exact visible
    # logical lines and their y coordinates, so font metrics, paragraph spacing
    # and soft-wrapped rows cannot accumulate scroll drift.
    line_gutter_widget = Gtk.DrawingArea()
    line_gutter_widget.set_name("line-gutter")
    line_gutter_widget.set_size_request(LINE_GUTTER_MIN_WIDTH, 1)
    line_gutter_widget.set_hexpand(False)
    line_gutter_widget.set_vexpand(True)
    editor_box.pack_start(line_gutter_widget, False, False, 0)

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

    line_gutter = LineGutterAdapter(
        line_gutter_widget,
        text,
        minimum_width=LINE_GUTTER_MIN_WIDTH,
        render_layout=Gtk.render_layout,
    )

    def draw_line_gutter(widget, cairo_context):
        style_context = widget.get_style_context()
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        Gtk.render_background(style_context, cairo_context, 0, 0, width, height)
        Gtk.render_frame(style_context, cairo_context, 0, 0, width, height)
        return line_gutter.draw(widget, cairo_context)

    line_gutter_widget.connect("draw", draw_line_gutter)

    # Scroll and reflow only invalidate the viewport drawing.  Line-number
    # coordinates are always recalculated from GtkTextView on the next draw.
    scroller.get_vadjustment().connect(
        "value-changed",
        lambda _adjustment: line_gutter_widget.queue_draw(),
    )
    text.connect(
        "size-allocate",
        lambda _widget, _allocation: line_gutter_widget.queue_draw(),
    )

    return editor_box, line_gutter, scroller, text


def apply_text_wrap_policy(text, scroller, enabled: bool) -> bool:
    """Apply soft wrap without giving the TextView a virtual line width."""
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
