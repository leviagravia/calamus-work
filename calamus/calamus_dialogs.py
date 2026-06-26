"""GTK dialog helpers for Calamus.

This module keeps transient UI dialogs out of the main application class while
preserving GTK3 widgets and the existing lightweight behaviour.
"""

from gi.repository import Gtk, Gdk

from calamus_shortcuts import shortcut_rows


def _margins(widget, value=10):
    widget.set_margin_start(value)
    widget.set_margin_end(value)
    widget.set_margin_top(value)
    widget.set_margin_bottom(value)


def show_info(parent, message):
    dialog = Gtk.MessageDialog(parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, message)
    dialog.run()
    dialog.destroy()


def show_large_info(parent, title, body):
    dialog = Gtk.MessageDialog(parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, title)
    dialog.format_secondary_text(body)
    dialog.run()
    dialog.destroy()


def show_error(parent, message):
    dialog = Gtk.MessageDialog(parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()


def ask_save(parent, modified):
    if not modified:
        return "discard"
    dialog = Gtk.MessageDialog(parent, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE, "Save changes?")
    dialog.add_buttons("Discard changes", 1, "Cancel", 2, "Save", 3)
    response = dialog.run()
    dialog.destroy()
    return {1: "discard", 2: "cancel", 3: "save"}.get(response, "cancel")


def choose_open_file(parent):
    dialog = Gtk.FileChooserDialog(
        "Open text file", parent, Gtk.FileChooserAction.OPEN,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
    )
    filename = dialog.get_filename() if dialog.run() == Gtk.ResponseType.OK else None
    dialog.destroy()
    return filename


def choose_save_file(parent):
    dialog = Gtk.FileChooserDialog(
        "Save text file", parent, Gtk.FileChooserAction.SAVE,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK),
    )
    dialog.set_do_overwrite_confirmation(True)
    filename = dialog.get_filename() if dialog.run() == Gtk.ResponseType.OK else None
    dialog.destroy()
    return filename


SHORTCUT_ROWS = shortcut_rows()


def show_keyboard_shortcuts(parent, rows=SHORTCUT_ROWS):
    dialog = Gtk.Dialog(title="Keyboard Shortcuts", transient_for=parent, modal=True)
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(620, 520)
    box = dialog.get_content_area()
    box.set_spacing(8)
    _margins(box)
    grid = Gtk.Grid(column_spacing=18, row_spacing=6)
    _margins(grid, 6)
    for col, header in enumerate(["Menu", "Command", "Shortcut"]):
        label = Gtk.Label(label=f"<b>{header}</b>")
        label.set_use_markup(True)
        label.set_xalign(0)
        grid.attach(label, col, 0, 1, 1)
    for row, values in enumerate(rows, start=1):
        for col, value in enumerate(values):
            label = Gtk.Label(label=value)
            label.set_xalign(0)
            label.set_selectable(True)
            grid.attach(label, col, row, 1, 1)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(grid)
    box.pack_start(scroll, True, True, 0)
    dialog.show_all()
    dialog.run()
    dialog.destroy()


def show_about(parent, version, display_name=None):
    dialog = Gtk.Dialog(title="About Calamus", transient_for=parent, modal=True)
    about_header = display_name or f"Calamus {version}"
    dialog.set_name("calamus-about-dialog")
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE)
    dialog.set_default_size(560, 420)

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
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    box = dialog.get_content_area()
    box.set_border_width(8)
    notebook = Gtk.Notebook()
    box.pack_start(notebook, True, True, 0)

    about_body = f"""{about_header}

Calamus is a lightweight text editor focused on plain-text writing.

It is designed for users who want more writing-oriented tools than a minimal editor, without the weight or complexity of a full IDE.

Main focus:
- fast plain-text editing
- clean writing workflow
- low-distraction interface
- useful tools for writers, students and note-takers
- offline-first usage

Key features:
- Find and replace
- Spell checking
- Session restore
- Recent files and favourites
- Clip Collection for reusable text blocks
- Clean Paste from PDF
- Paragraph reflow and line joining
- Smart typography tools
- Document statistics
- Focus and distraction-free modes
- Lightweight themes

What Calamus is not:
Calamus is not an IDE. It does not include code intelligence, LSP integration, heavy plugin systems, background indexing or cloud services.

This is intentional. Calamus is meant to remain simple, fast and focused on writing.

Recommended users:
- writers
- students
- Linux users who want a lightweight editor
- users who often copy text from PDFs
- users who prefer local, offline tools

Author: leviagravia@zohomail.eu"""
    about_view = Gtk.TextView()
    about_view.set_editable(False)
    about_view.set_cursor_visible(False)
    about_view.set_wrap_mode(Gtk.WrapMode.WORD)
    about_view.set_left_margin(12)
    about_view.set_right_margin(12)
    about_view.set_top_margin(12)
    about_view.set_bottom_margin(12)
    about_view.get_buffer().set_text(about_body)
    about_scroll = Gtk.ScrolledWindow()
    about_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    about_scroll.add(about_view)
    notebook.append_page(about_scroll, Gtk.Label(label="About"))

    license_view = Gtk.TextView()
    license_view.set_editable(False)
    license_view.set_cursor_visible(False)
    license_view.set_wrap_mode(Gtk.WrapMode.WORD)
    license_view.set_left_margin(12)
    license_view.set_right_margin(12)
    license_view.set_top_margin(12)
    license_view.set_bottom_margin(12)
    license_view.get_buffer().set_text(
        "Calamus is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.\n\n"
        "Calamus is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details."
    )
    license_scroll = Gtk.ScrolledWindow()
    license_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    license_scroll.add(license_view)
    notebook.append_page(license_scroll, Gtk.Label(label="License"))

    dialog.show_all()
    dialog.run()
    dialog.destroy()


def prompt_go_to_line(parent, total_lines):
    dialog = Gtk.Dialog(title="Go to Line", transient_for=parent, modal=True)
    dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Go", Gtk.ResponseType.OK)
    box = dialog.get_content_area()
    box.set_spacing(8)
    _margins(box)
    label = Gtk.Label(label=f"Line number (1-{total_lines}):")
    label.set_xalign(0)
    entry = Gtk.Entry()
    entry.set_text("1")
    box.pack_start(label, False, False, 0)
    box.pack_start(entry, False, False, 0)
    dialog.show_all()
    response = dialog.run()
    line_no = None
    invalid = False
    if response == Gtk.ResponseType.OK:
        try:
            line_no = max(1, min(total_lines, int(entry.get_text().strip())))
        except ValueError:
            invalid = True
    dialog.destroy()
    return line_no, invalid


def run_find_replace_dialog(parent, initial_search, callbacks):
    dialog = Gtk.Dialog(title="Find / Replace", transient_for=parent, modal=False)
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE, "Find Next", 10, "Find Previous", 15, "Replace", 20, "Replace All", 30)
    dialog.set_default_size(560, 260)
    box = dialog.get_content_area()
    box.set_spacing(8)
    _margins(box)

    grid = Gtk.Grid(column_spacing=8, row_spacing=8)
    box.pack_start(grid, True, True, 0)

    find_label = Gtk.Label(label="Find:")
    find_label.set_xalign(0)
    repl_label = Gtk.Label(label="Replace with:")
    repl_label.set_xalign(0)
    find_entry = Gtk.Entry()
    repl_entry = Gtk.Entry()
    find_entry.set_text(initial_search or "")
    find_entry.set_activates_default(True)
    repl_entry.set_activates_default(True)
    grid.attach(find_label, 0, 0, 1, 1)
    grid.attach(find_entry, 1, 0, 1, 1)
    grid.attach(repl_label, 0, 1, 1, 1)
    grid.attach(repl_entry, 1, 1, 1, 1)

    case_item = Gtk.CheckButton(label="Match case")
    word_item = Gtk.CheckButton(label="Whole word")
    wrap_item = Gtk.CheckButton(label="Wrap around")
    wrap_item.set_active(True)
    grid.attach(case_item, 0, 2, 1, 1)
    grid.attach(word_item, 1, 2, 1, 1)
    grid.attach(wrap_item, 1, 3, 1, 1)

    status = Gtk.Label()
    status.set_xalign(0)
    grid.attach(status, 0, 4, 2, 1)

    def options():
        return case_item.get_active(), word_item.get_active(), wrap_item.get_active()

    def do_find(backwards=False):
        needle = find_entry.get_text()
        if not needle:
            status.set_text("Enter text to find.")
            return False
        match_case, whole_word, wrap = options()
        matches = callbacks["highlight"](needle, match_case, whole_word)
        ok = callbacks["find"](needle, backwards, match_case, whole_word, wrap)
        direction = "previous" if backwards else "next"
        status.set_text((f"Found {direction}. {matches} match(es) highlighted.") if ok else "No match found.")
        return ok

    def do_replace():
        needle = find_entry.get_text()
        replacement = repl_entry.get_text()
        if not needle:
            status.set_text("Enter text to find.")
            return
        match_case, whole_word, wrap = options()
        if callbacks["need_current_match"](needle):
            if not do_find(False):
                return
        if callbacks["replace_current"](needle, replacement, match_case, whole_word):
            callbacks["highlight"](needle, match_case, whole_word)
            status.set_text("Replaced current match.")
            callbacks["find"](needle, False, match_case, whole_word, wrap)
        else:
            status.set_text("No current match to replace.")

    def do_replace_all():
        needle = find_entry.get_text()
        replacement = repl_entry.get_text()
        if not needle:
            status.set_text("Enter text to find.")
            return
        match_case, whole_word, _wrap = options()
        count = callbacks["replace_all"](needle, replacement, match_case, whole_word)
        callbacks["highlight"](needle, match_case, whole_word)
        status.set_text(f"Replaced {count} occurrence(s).")

    dialog.set_default_response(10)
    find_entry.connect("activate", lambda *_: do_find(False))
    repl_entry.connect("activate", lambda *_: do_replace())
    dialog.show_all()
    find_entry.grab_focus()
    while True:
        response = dialog.run()
        if response in (Gtk.ResponseType.CLOSE, Gtk.ResponseType.DELETE_EVENT):
            break
        if response == 10:
            do_find(False)
        elif response == 15:
            do_find(True)
        elif response == 20:
            do_replace()
        elif response == 30:
            do_replace_all()
    dialog.destroy()


def run_spelling_dialog(parent, word, suggestions):
    dialog = Gtk.Dialog(title="External Spellcheck", transient_for=parent, modal=True)
    dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Ignore", 10, "Ignore All", 11, "Replace", 20, "Replace All", 21)
    dialog.set_default_response(20)
    box = dialog.get_content_area()
    box.set_spacing(8)
    _margins(box)

    title = Gtk.Label(label=f"Misspelled word: {word}")
    title.set_xalign(0)
    box.pack_start(title, False, False, 0)

    entry = Gtk.Entry()
    entry.set_text(suggestions[0] if suggestions else word)
    box.pack_start(entry, False, False, 0)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    for suggestion in suggestions:
        row = Gtk.ListBoxRow()
        label = Gtk.Label(label=suggestion)
        label.set_xalign(0)
        _margins(label, 4)
        label.set_margin_start(6)
        label.set_margin_end(6)
        row.add(label)
        listbox.add(row)
    if suggestions:
        listbox.select_row(listbox.get_row_at_index(0))

    def on_row_selected(_box, row):
        if row:
            entry.set_text(row.get_child().get_text())
    listbox.connect("row-selected", on_row_selected)

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.set_size_request(360, 140)
    scroll.add(listbox)
    box.pack_start(scroll, True, True, 0)

    dialog.show_all()
    response = dialog.run()
    replacement = entry.get_text()
    dialog.destroy()
    return response, replacement
