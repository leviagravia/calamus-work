"""GTK menu and shortcut wiring for Calamus.

This module intentionally contains GTK construction/binding only.  The window
object passed in supplies command callbacks and application state.
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from calamus_writing import (
    clean_pdf_text,
    join_lines,
    remove_extra_spaces,
    remove_trailing_spaces,
    sentence_case,
    smart_typography,
    sort_lines,
    title_case,
)


def top_menu(app, label: str) -> Gtk.Menu:
    item = Gtk.MenuItem(label=label)
    menu = Gtk.Menu()
    item.set_submenu(menu)
    app.menubar.append(item)
    return menu


def add_item(menu: Gtk.Menu, label: str, callback):
    item = Gtk.MenuItem(label=label)
    item.connect("activate", callback)
    menu.append(item)
    return item


def add_separator(menu: Gtk.Menu) -> None:
    menu.append(Gtk.SeparatorMenuItem())


def build_menu(app) -> None:
    filem = top_menu(app, "File")
    add_item(filem, "New\tCtrl+N", app.on_new)
    app.template_item = Gtk.MenuItem(label="New from Template")
    app.template_menu = Gtk.Menu()
    app.template_item.set_submenu(app.template_menu)
    filem.append(app.template_item)
    app.populate_template_menu()
    add_item(filem, "Open…\tCtrl+O", app.on_open)
    app.recent_item = Gtk.MenuItem(label="Recent Files")
    app.recent_menu = Gtk.Menu()
    app.recent_item.set_submenu(app.recent_menu)
    filem.append(app.recent_item)
    app.populate_recent_menu()
    add_item(filem, "Save\tCtrl+S", app.on_save)
    add_item(filem, "Save As…\tCtrl+Shift+S", app.on_save_as)
    add_separator(filem)
    add_item(filem, "Print Preview…\tCtrl+Shift+P", app.on_print_preview)
    add_item(filem, "Print…\tCtrl+P", app.on_print)
    add_separator(filem)
    add_item(filem, "Save Session\tCtrl+Alt+S", app.on_save_session)
    add_item(filem, "Reopen Last Session\tCtrl+Alt+O", app.on_restore_session)
    add_separator(filem)
    add_item(filem, "Quit\tCtrl+Q", app.on_quit)

    editm = top_menu(app, "Edit")
    add_item(editm, "Undo\tCtrl+Z", app.on_undo)
    add_item(editm, "Redo\tCtrl+Y", app.on_redo)
    add_separator(editm)
    add_item(editm, "Cut\tCtrl+X", app.on_cut)
    add_item(editm, "Copy\tCtrl+C", app.on_copy)
    add_item(editm, "Paste\tCtrl+V", app.on_paste)
    add_item(editm, "Paste as Plain Text\tCtrl+Shift+V", app.on_paste_plain_text)
    add_item(editm, "Select All\tCtrl+A", app.on_select_all)
    add_item(editm, "Duplicate Line / Selection\tCtrl+D", app.on_duplicate_line_or_selection)
    add_separator(editm)
    add_item(editm, "Find / Replace…\tCtrl+F", app.on_find_replace)
    add_item(editm, "Find Next Word\tCtrl+G", app.on_find_next)
    add_item(editm, "Find Previous\tCtrl+Shift+G", app.on_find_previous)
    add_item(editm, "Replace\tCtrl+H", app.on_find_replace)
    add_item(editm, "Replace All\tCtrl+Shift+H", app.on_replace_all_dialog)
    add_separator(editm)
    add_item(editm, "Go to Line…\tCtrl+L", app.on_go_to_line)

    revisem = top_menu(app, "Revise")
    add_item(revisem, "UPPERCASE (convert selected)\tCtrl+Alt+U", lambda *_: app.replace_selection(str.upper))
    add_item(revisem, "Lowercase (convert selected)\tCtrl+Alt+Shift+U", lambda *_: app.replace_selection(str.lower))
    add_item(revisem, "Title Case\tCtrl+Alt+Y", lambda *_: app.apply_text_transform(title_case, "Title Case"))
    add_item(revisem, "Sentence case\tCtrl+Alt+Shift+Y", lambda *_: app.apply_text_transform(sentence_case, "Sentence Case"))
    add_separator(revisem)
    add_item(revisem, "Insert Date/Time\tCtrl+Alt+D", app.on_insert_datetime)
    add_separator(revisem)
    add_item(revisem, "Insert Bookmark Here\tCtrl+F2", app.toggle_bookmark)
    add_item(revisem, "Next Bookmark\tF2", app.next_bookmark)
    add_item(revisem, "Previous Bookmark\tShift+F2", app.previous_bookmark)
    add_item(revisem, "Manage Bookmarks…", app.on_manage_bookmarks)
    add_separator(revisem)
    add_item(revisem, "Paste Clean from PDF\tCtrl+Alt+V", app.on_paste_clean_pdf)
    add_item(revisem, "Clean Selected Text from PDF\tCtrl+Alt+Shift+V", app.on_clean_selected_pdf)
    add_item(revisem, "Smart Typography\tCtrl+Alt+M", app.on_smart_typography)
    add_item(revisem, "Reflow Paragraph\tCtrl+Alt+J", app.on_reflow_paragraph)
    add_item(revisem, "Join Lines\tCtrl+J", app.on_join_lines)
    add_item(revisem, "Remove Extra Spaces", app.on_remove_extra_spaces)
    add_item(revisem, "Remove Trailing Spaces", lambda *_: app.apply_text_transform(remove_trailing_spaces, "Remove Trailing Spaces"))
    add_item(revisem, "Sort Alphabetically A-Z\tCtrl+Alt+Up", lambda *_: app.apply_text_transform(lambda t: sort_lines(t, reverse=False), "Sort A-Z"))
    add_item(revisem, "Sort Alphabetically Z-A\tCtrl+Alt+Down", lambda *_: app.apply_text_transform(lambda t: sort_lines(t, reverse=True), "Sort Z-A"))

    favm = top_menu(app, "Favourites")
    add_item(favm, "Add to Favourites\tCtrl+Alt+B", app.on_add_favourite)
    add_item(favm, "Edit Favourites…\tCtrl+Shift+D", app.on_edit_favourites)
    add_item(favm, "Reload Favourites\tCtrl+Alt+R", app.on_reload_favourites)
    add_separator(favm)
    app.favourites_menu = favm
    app.populate_favourites_menu()

    viewm = top_menu(app, "View")
    add_item(viewm, "Focus Mode\tF9", app.toggle_focus_mode)
    add_item(viewm, "Distraction-Free Mode\tF11", app.toggle_distraction_free)
    add_item(viewm, "Highlight Current Line\tCtrl+Alt+I", app.toggle_current_line_highlight)
    add_item(viewm, "Clip Collection\tCtrl+Alt+C", app.toggle_clip_collection)
    add_item(viewm, "Character Map\tCtrl+Alt+F10", app.on_character_map)

    optm = top_menu(app, "Options")
    app.word_wrap_item = Gtk.CheckMenuItem(label="Word Wrap\tAlt+Z")
    app.word_wrap_item.set_active(app.word_wrap)
    app.word_wrap_item.connect("toggled", app.on_word_wrap)
    optm.append(app.word_wrap_item)
    add_item(optm, "Font…\tCtrl+Shift+F", app.on_font)
    app.transparent_item = Gtk.CheckMenuItem(label="Transparent Mode\tCtrl+Shift+T")
    app.transparent_item.set_active(int(app.settings.get("opacity", app.DEFAULT_OPACITY if hasattr(app, "DEFAULT_OPACITY") else 88)) < 100)
    app.transparent_item.connect("toggled", app.on_transparent_mode)
    optm.append(app.transparent_item)
    app.always_item = Gtk.CheckMenuItem(label="Always on Top\tCtrl+Shift+A")
    app.always_item.set_active(app.always_on_top)
    app.always_item.connect("toggled", app.on_top)
    optm.append(app.always_item)
    add_separator(optm)
    app.white_item = Gtk.CheckMenuItem(label="White Background")
    app.white_item.set_active(app.white_background)
    app.white_item.connect("toggled", app.on_white_background)
    optm.append(app.white_item)
    app.dark_item = Gtk.CheckMenuItem(label="Dark Mode")
    app.dark_item.set_active(app.dark_mode)
    app.dark_item.connect("toggled", app.on_dark_mode)
    optm.append(app.dark_item)
    app.line_item = Gtk.CheckMenuItem(label="Line Numbers\tCtrl+Alt+L")
    app.line_item.set_active(app.show_line_numbers)
    app.line_item.connect("toggled", app.on_line_numbers)
    optm.append(app.line_item)
    add_separator(optm)
    add_item(optm, "Font Bigger\tCtrl++", lambda *_: app.change_font(1))
    add_item(optm, "Font Smaller\tCtrl+-", lambda *_: app.change_font(-1))
    add_separator(optm)
    opacity_item = Gtk.MenuItem(label="Opacity")
    opacity_menu = Gtk.Menu()
    opacity_item.set_submenu(opacity_menu)
    optm.append(opacity_item)
    add_item(opacity_menu, "Opacity Selection…", app.on_opacity_selection)
    add_separator(opacity_menu)
    for opacity in (100, 90, 88, 80, 70, 60, 50, 40, 30):
        add_item(opacity_menu, f"{opacity}%", lambda _w, val=opacity: app.set_opacity_value(val))

    toolsm = top_menu(app, "Tools")
    add_item(toolsm, "External Spellcheck\tF7", app.on_check)
    add_item(toolsm, "Document Statistics\tCtrl+Alt+W", app.on_document_statistics)
    add_separator(toolsm)
    add_item(toolsm, "Language…", app.on_language_selection)
    add_item(toolsm, "System Info…", app.on_system_info)

    helpm = top_menu(app, "Help")
    add_item(helpm, "Keyboard Shortcuts\tCtrl+/", app.on_keyboard_shortcuts)
    add_item(helpm, "About\tF1", app.on_about)


def shortcut_bindings(app):
    return (
        ("<Control>Z", app.on_undo),
        ("<Control>Y", app.on_redo),
        ("<Control><Shift>Z", app.on_redo),
        ("<Control>N", app.on_new),
        ("<Control>O", app.on_open),
        ("<Control>S", app.on_save),
        ("<Control><Shift>S", app.on_save_as),
        ("<Control><Alt>S", app.on_save_session),
        ("<Control><Alt>O", app.on_restore_session),
        ("<Control>F", app.on_find_replace),
        ("<Control>H", app.on_find_replace),
        ("<Control><Shift>H", app.on_replace_all_dialog),
        ("<Control>G", app.on_find_next),
        ("<Control><Shift>G", app.on_find_previous),
        ("<Control>L", app.on_go_to_line),
        ("<Control><Alt>D", app.on_insert_datetime),
        ("<Control>X", app.on_cut),
        ("<Control>C", app.on_copy),
        ("<Control>V", app.on_paste),
        ("<Control>A", app.on_select_all),
        ("<Control><Shift>V", app.on_paste_plain_text),
        ("<Control>D", app.on_duplicate_line_or_selection),
        ("<Alt>Up", lambda *_: app.on_move_line(-1)),
        ("<Alt>Down", lambda *_: app.on_move_line(1)),
        ("<Control>F2", app.toggle_bookmark),
        ("F2", app.next_bookmark),
        ("<Shift>F2", app.previous_bookmark),
        ("<Control><Shift>P", app.on_print_preview),
        ("<Control>P", app.on_print),
        ("<Control>Q", app.on_quit),
        ("<Control><Alt>U", lambda *_: app.replace_selection(str.upper)),
        ("<Control><Alt><Shift>U", lambda *_: app.replace_selection(str.lower)),
        ("<Control>plus", lambda *_: app.change_font(1)),
        ("<Control>minus", lambda *_: app.change_font(-1)),
        ("<Alt>Z", app.toggle_word_wrap),
        ("<Control><Shift>F", app.on_font),
        ("<Control><Shift>T", app.toggle_transparent_mode),
        ("<Control><Shift>A", app.toggle_always_on_top),
        ("<Control><Alt>L", app.toggle_line_numbers),
        ("<Control><Alt>B", app.on_add_favourite),
        ("<Control><Shift>D", app.on_edit_favourites),
        ("<Control><Alt>R", app.on_reload_favourites),
        ("<Control><Alt>F10", app.on_character_map),
        ("<Control><Alt>C", app.toggle_clip_collection),
        ("F9", app.toggle_focus_mode),
        ("F11", app.toggle_distraction_free),
        ("<Control><Alt>I", app.toggle_current_line_highlight),
        *( (f"<Control><Alt>{i}", (lambda *_args, n=i: app.insert_clip_number(n))) for i in range(1, 10) ),
        ("<Control><Alt>W", app.on_document_statistics),
        ("<Control><Alt>V", app.on_paste_clean_pdf),
        ("<Control><Alt><Shift>V", app.on_clean_selected_pdf),
        ("<Control><Alt>J", app.on_reflow_paragraph),
        ("<Control>J", app.on_join_lines),
        ("<Control><Alt>Y", lambda *_: app.apply_text_transform(title_case, "Title Case")),
        ("<Control><Alt><Shift>Y", lambda *_: app.apply_text_transform(sentence_case, "Sentence Case")),
        ("<Control><Alt>Up", lambda *_: app.apply_text_transform(lambda t: sort_lines(t, reverse=False), "Sort A-Z")),
        ("<Control><Alt>Down", lambda *_: app.apply_text_transform(lambda t: sort_lines(t, reverse=True), "Sort Z-A")),
        ("<Control><Alt>M", app.on_smart_typography),
        ("F7", app.on_check),
        ("<Control>slash", app.on_keyboard_shortcuts),
        ("F1", app.on_about),
    )


def shortcut_conflicts(bindings: tuple[tuple[str, object], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for shortcut, _callback in bindings:
        counts[shortcut] = counts.get(shortcut, 0) + 1
    return {shortcut: count for shortcut, count in counts.items() if count > 1}


def add_shortcuts(app) -> None:
    acc = Gtk.AccelGroup()
    app.add_accel_group(acc)
    bindings = shortcut_bindings(app)
    conflicts = shortcut_conflicts(bindings)
    if conflicts:
        raise RuntimeError(f"Duplicate Calamus shortcuts: {conflicts}")
    for shortcut, callback in bindings:
        key, mod = Gtk.accelerator_parse(shortcut)
        acc.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *args, cb=callback: (cb(), True)[1])
