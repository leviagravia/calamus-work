"""Dedicated GTK presentation boundary for the Calamus Character Map."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk


def present_character_map(parent, text_view, *, replace_selection, execute_command) -> None:
    if not callable(replace_selection) or not callable(execute_command):
        raise TypeError("character-map editor capabilities must be callable")
    d = Gtk.Dialog(title="Character Map", transient_for=parent, modal=True)
    d.set_name("calamus-character-map-dialog")
    d.add_buttons("Close", Gtk.ResponseType.CLOSE)
    d.set_default_size(720, 520)

    css = b"""
    #calamus-character-map-dialog,
    #calamus-character-map-dialog box,
    #calamus-character-map-dialog scrolledwindow,
    #calamus-character-map-dialog viewport {
        background-color: #ffffff;
        color: #000000;
        background-image: none;
    }
    #calamus-character-map-dialog label {
        color: #000000;
    }
    #calamus-character-map-dialog button,
    #calamus-character-map-dialog button label {
        background-color: #eeeeee;
        color: #000000;
        background-image: none;
        text-shadow: none;
        box-shadow: none;
    }
    #calamus-character-map-dialog button:hover {
        background-color: #dddddd;
        color: #000000;
        background-image: none;
    }
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
    )

    box = d.get_content_area()
    box.set_spacing(8)
    box.set_margin_start(10)
    box.set_margin_end(10)
    box.set_margin_top(10)
    box.set_margin_bottom(10)

    hint = Gtk.Label(label="Click a character to insert it at the cursor position. Shortcut: Ctrl+Alt+F10")
    hint.set_xalign(0)
    box.pack_start(hint, False, False, 0)

    notebook = Gtk.Notebook()
    box.pack_start(notebook, True, True, 0)

    groups = [
        ("Alphabet", "ABCDEFGHIJKLMNOPQRSTUVWXYZ\nabcdefghijklmnopqrstuvwxyz"),
        ("Accents", "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß\nàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ\nĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĞğĠġĢģĪīĮįİıŁłŃńŇňŐőŒœŔŕŘřŚśŞşŠšŤťŪūŮůŰűŲųŸŹźŻżŽž"),
        ("Greek", "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ\nαβγδεζηθικλμνξοπρστυφχψω"),
        ("Numbers", "0123456789 ⁰¹²³⁴⁵⁶⁷⁸⁹ ₀₁₂₃₄₅₆₇₈₉ ½⅓⅔¼¾⅛⅜⅝⅞"),
        ("Punctuation", ".,;:!?¡¿'\"`´‘’“”‚„…·•-–—_()[]{}<>/\\|@#&§¶"),
        ("Math", "+−×÷=≠≈≡<≤>≥±∞√∑∏∫∂∆∇πµΩ°′″‰%¬∧∨∩∪⊂⊃⊆⊇∈∉∅"),
        ("Currency", "€£$¥¢₹₽₩₪₫₴₦₱₲₵₡₭₮₨฿"),
        ("Arrows", "←↑→↓↔↕↖↗↘↙⇐⇑⇒⇓⇔⇧⇨➜➤➔➜➞"),
        ("Symbols", "©®™✓✔✕✖★☆♥♦♣♠♪♫☀☁☂☃☎☑☐☒⚠⚙⚡☕⌘⌥⇧⎋"),
    ]

    def insert_char(ch):
        buffer = text_view.get_buffer()
        if buffer.get_has_selection():
            replace_selection(lambda _old, c=ch: c)
            return
        cursor = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()

        def edit(target_buffer):
            target_buffer.insert(target_buffer.get_iter_at_offset(cursor), ch)

        execute_command(
            "Insert Character",
            edit,
            select_range=(cursor + len(ch), cursor + len(ch)),
        )

    for title, chars in groups:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid(column_spacing=4, row_spacing=4)
        grid.set_margin_start(8)
        grid.set_margin_end(8)
        grid.set_margin_top(8)
        grid.set_margin_bottom(8)
        scroll.add(grid)

        row = 0
        col = 0
        for ch in chars:
            if ch == "\n":
                row += 1
                col = 0
                continue
            if ch == " ":
                continue
            btn = Gtk.Button(label=ch)
            btn.set_size_request(34, 30)
            btn.set_tooltip_text("Insert " + ch)
            btn.connect("clicked", lambda _b, c=ch: insert_char(c))
            grid.attach(btn, col, row, 1, 1)
            col += 1
            if col >= 16:
                row += 1
                col = 0
        notebook.append_page(scroll, Gtk.Label(label=title))

    d.show_all()
    d.run()
    d.destroy()
