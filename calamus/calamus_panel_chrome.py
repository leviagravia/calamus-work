"""Shared compact side-panel chrome for Calamus GTK views."""
from __future__ import annotations


def build_compact_close_button(on_activate, *, name: str, tooltip: str):
    """Return a small accessible symbolic button using application CSS.

    Gtk themes can impose larger button chrome than ``set_size_request``.  The
    dedicated CSS therefore removes border, background, shadow and padding in
    every interactive state while preserving a real focusable Gtk.Button.
    """
    if not callable(on_activate):
        raise TypeError("on_activate must be callable")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    if not isinstance(tooltip, str) or not tooltip.strip():
        raise ValueError("tooltip must be a non-empty string")

    from gi.repository import Gtk

    widget_name = name.strip()
    button = Gtk.Button()
    button.set_name(widget_name)
    button.set_relief(Gtk.ReliefStyle.NONE)
    button.set_focus_on_click(False)
    button.set_can_focus(True)
    button.set_size_request(18, 18)
    button.set_valign(Gtk.Align.CENTER)
    button.set_halign(Gtk.Align.END)
    button.set_tooltip_text(tooltip.strip())

    image = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
    if hasattr(image, "set_pixel_size"):
        image.set_pixel_size(10)
    button.add(image)

    provider = Gtk.CssProvider()
    selector = f"button#{widget_name}"
    css = f"""
{selector},
{selector}:hover,
{selector}:active,
{selector}:checked,
{selector}:focus {{
    min-width: 16px;
    min-height: 16px;
    padding: 0;
    margin: 0;
    border: 0;
    border-radius: 2px;
    background: transparent;
    background-image: none;
    box-shadow: none;
    outline-width: 1px;
}}
""".encode("utf-8")
    provider.load_from_data(css)
    button.get_style_context().add_provider(
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 50,
    )
    # Keep provider alive for the lifetime of the widget.
    button._calamus_css_provider = provider
    button.connect("clicked", lambda *_: on_activate())
    try:
        button.get_accessible().set_name(tooltip.strip())
    except Exception:
        pass
    return button
