"""Clip Collection panel construction and sizing helpers."""
from __future__ import annotations

from calamus_layout import CLIP_PANEL_DEFAULT_WIDTH, CLIP_PANEL_MIN_WIDTH, CLIP_PANEL_MAX_FRACTION


def calculate_clip_panel_width(total_width: int) -> int:
    width = int(total_width or 900)
    max_width = int(width * CLIP_PANEL_MAX_FRACTION)
    return max(CLIP_PANEL_MIN_WIDTH, min(CLIP_PANEL_DEFAULT_WIDTH, max_width))


def build_clip_panel(on_clip_list_button_press, on_add, on_insert, on_delete):
    from gi.repository import Gtk, Gdk, Pango
    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    panel.set_size_request(CLIP_PANEL_DEFAULT_WIDTH, -1)
    panel.set_hexpand(False)
    panel.set_margin_start(3)
    panel.set_margin_end(3)
    panel.set_margin_top(3)
    panel.set_margin_bottom(3)

    title = Gtk.Label(label="Clip Collection")
    title.set_name("calamus-clip-title")
    title.set_xalign(0)
    title.set_ellipsize(Pango.EllipsizeMode.END)
    panel.pack_start(title, False, False, 0)

    clip_list = Gtk.ListBox()
    clip_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    clip_list.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
    clip_list.connect("button-press-event", on_clip_list_button_press)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    if hasattr(scroll, "set_propagate_natural_width"):
        scroll.set_propagate_natural_width(False)
    if hasattr(scroll, "set_propagate_natural_height"):
        scroll.set_propagate_natural_height(False)
    scroll.set_hexpand(False)
    scroll.set_vexpand(True)
    scroll.add(clip_list)
    panel.pack_start(scroll, True, True, 0)

    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    row.set_hexpand(False)
    row.set_halign(Gtk.Align.START)
    for label, cb in (("Add", on_add), ("Insert", on_insert), ("Delete", on_delete)):
        btn = Gtk.Button(label=label)
        btn.set_size_request(56, 26)
        btn.set_relief(Gtk.ReliefStyle.NORMAL)
        btn.set_hexpand(False)
        btn.get_style_context().add_class("calamus-clip-button")
        btn.connect("clicked", cb)
        row.pack_start(btn, False, False, 0)
    panel.pack_start(row, False, False, 0)
    return panel, clip_list
