"""Owned GTK presentation for Calamus About and System Info dialogs."""
from __future__ import annotations

from dataclasses import dataclass

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk

from calamus_modal_dialog import destroy_modal, run_modal
from calamus_runtime_identity import RuntimeIdentity, build_about_body


@dataclass(frozen=True)
class AboutDialogWidgets:
    dialog: Gtk.Dialog
    text_view: Gtk.TextView


@dataclass(frozen=True)
class SystemInfoDialogWidgets:
    dialog: Gtk.Dialog
    text_view: Gtk.TextView


def _readonly_text_view(name: str, text: str) -> Gtk.TextView:
    view = Gtk.TextView()
    view.set_name(name)
    view.set_editable(False)
    view.set_cursor_visible(False)
    view.set_wrap_mode(Gtk.WrapMode.WORD)
    view.set_left_margin(12)
    view.set_right_margin(12)
    view.set_top_margin(12)
    view.set_bottom_margin(12)
    view.get_buffer().set_text(text)
    return view


def _scrolled(view: Gtk.TextView) -> Gtk.ScrolledWindow:
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(view)
    return scroll


def _install_about_css() -> None:
    css = b"""
    #calamus-about-dialog, #calamus-about-dialog box,
    #calamus-about-dialog notebook, #calamus-about-dialog notebook > stack,
    #calamus-about-dialog notebook stack, #calamus-about-dialog notebook header,
    #calamus-about-dialog notebook tab, #calamus-about-dialog notebook tab label,
    #calamus-about-dialog scrolledwindow, #calamus-about-dialog viewport,
    #calamus-about-dialog textview, #calamus-about-dialog textview text {
        background-color: #ffffff;
        color: #000000;
        background-image: none;
    }
    #calamus-about-dialog notebook tab {
        background-color: #e6e6e6;
        color: #000000;
        padding: 6px 10px;
        background-image: none;
    }
    #calamus-about-dialog notebook tab:checked,
    #calamus-about-dialog notebook tab:hover {
        background-color: #ffffff;
        color: #000000;
        background-image: none;
    }
    #calamus-about-dialog label,
    #calamus-about-dialog textview text {
        color: #000000;
    }
    #calamus-about-dialog button,
    #calamus-about-dialog button label {
        background-color: #eeeeee;
        color: #000000;
        background-image: none;
        text-shadow: none;
        box-shadow: none;
    }
    #calamus-about-dialog button:hover {
        background-color: #dddddd;
        color: #000000;
        background-image: none;
    }
    """
    screen = Gdk.Screen.get_default()
    if screen is None:
        return
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        screen,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_USER,
    )


def build_about_dialog(parent, identity: RuntimeIdentity) -> AboutDialogWidgets:
    dialog = Gtk.Dialog(
        title="About Calamus",
        transient_for=parent,
        modal=True,
        destroy_with_parent=True,
    )
    dialog.set_name("calamus-about-dialog")
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(560, 420)
    _install_about_css()

    box = dialog.get_content_area()
    box.set_border_width(8)
    notebook = Gtk.Notebook()
    box.pack_start(notebook, True, True, 0)

    about_view = _readonly_text_view(
        "calamus-about-text",
        build_about_body(identity),
    )
    notebook.append_page(_scrolled(about_view), Gtk.Label(label="About"))

    license_text = (
        "Calamus is free software: you can redistribute it and/or modify it "
        "under the terms of the GNU General Public License as published by the "
        "Free Software Foundation, either version 3 of the License, or (at your "
        "option) any later version.\n\n"
        "Calamus is distributed in the hope that it will be useful, but WITHOUT "
        "ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or "
        "FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License "
        "for more details."
    )
    license_view = _readonly_text_view("calamus-license-text", license_text)
    notebook.append_page(_scrolled(license_view), Gtk.Label(label="License"))

    dialog.show_all()
    return AboutDialogWidgets(dialog=dialog, text_view=about_view)


def present_about_dialog(parent, identity: RuntimeIdentity) -> None:
    widgets = build_about_dialog(parent, identity)
    try:
        run_modal(widgets.dialog)
    finally:
        destroy_modal(widgets.dialog)


def build_system_info_dialog(parent, body: str) -> SystemInfoDialogWidgets:
    dialog = Gtk.Dialog(
        title="System Info",
        transient_for=parent,
        modal=True,
        destroy_with_parent=True,
    )
    dialog.set_name("calamus-system-info-dialog")
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(660, 480)

    box = dialog.get_content_area()
    box.set_border_width(10)
    info_view = _readonly_text_view("calamus-system-info-text", body)
    box.pack_start(_scrolled(info_view), True, True, 0)
    dialog.show_all()
    return SystemInfoDialogWidgets(dialog=dialog, text_view=info_view)


def present_system_info_dialog(parent, body: str) -> None:
    widgets = build_system_info_dialog(parent, body)
    try:
        run_modal(widgets.dialog)
    finally:
        destroy_modal(widgets.dialog)
