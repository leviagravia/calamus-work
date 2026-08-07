"""GTK menu and shortcut wiring for Calamus.

This module intentionally contains GTK construction/binding only.  The window
object passed in supplies command callbacks and application state.
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from calamus_application_commands import command_target_for_callback, invoke_check_command
from calamus_command_catalog import shortcut_bindings as command_shortcut_bindings

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
    """Compatibility menu constructor routed through stable W104 command IDs."""
    item = Gtk.MenuItem(label=label)
    owner = getattr(callback, "__self__", None)
    if owner is not None and hasattr(owner, "invoke_command"):
        target = command_target_for_callback(callback)
        if target is None:
            raise RuntimeError(f"Uncatalogued Calamus menu callback: {getattr(callback, '__name__', callback)!r}")
        item.connect(
            "activate",
            lambda *_args, app=owner, command_id=target.command_id, data=target.data():
                app.invoke_command(command_id, source="menu", data=data),
        )
    else:
        item.connect("activate", callback)
    menu.append(item)
    return item


def add_command_item(menu: Gtk.Menu, label: str, app, command_id: str, data=None):
    item = Gtk.MenuItem(label=label)
    payload = dict(data or {})
    item.connect(
        "activate",
        lambda *_args, cid=command_id, values=payload: app.invoke_command(
            cid, source="menu", data=values
        ),
    )
    menu.append(item)
    return item


def connect_check_command(item, app, command_id: str) -> None:
    item.connect(
        "toggled",
        lambda widget, cid=command_id: invoke_check_command(
            app, cid, bool(widget.get_active()), source="menu"
        ),
    )


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
    add_separator(filem)
    app.workspace_file_item = Gtk.MenuItem(label="Writing Workspace")
    app.workspace_file_menu = Gtk.Menu()
    app.workspace_file_item.set_submenu(app.workspace_file_menu)
    filem.append(app.workspace_file_item)
    app.workspace_show_item = add_item(
        app.workspace_file_menu,
        "Show Workspace Panel",
        app.show_workspace_panel,
    )
    app.workspace_new_text_file_item = add_item(
        app.workspace_file_menu,
        "New Text File…",
        app.on_new_workspace_text_file,
    )
    app.workspace_new_text_file_item.set_sensitive(bool(getattr(app, "workspace_root", None)))
    app.workspace_new_folder_item = add_item(
        app.workspace_file_menu,
        "New Folder…",
        app.on_new_workspace_folder,
    )
    app.workspace_new_folder_item.set_sensitive(bool(getattr(app, "workspace_root", None)))
    app.workspace_rename_item = add_item(
        app.workspace_file_menu,
        "Rename Selected Item…",
        app.on_rename_workspace_item,
    )
    app.workspace_rename_item.set_sensitive(bool(getattr(app, "workspace_root", None)))
    app.workspace_duplicate_item = add_item(
        app.workspace_file_menu,
        "Duplicate Selected Text File",
        app.on_duplicate_workspace_file,
    )
    app.workspace_duplicate_item.set_sensitive(bool(getattr(app, "workspace_root", None)))
    app.workspace_trash_item = add_item(
        app.workspace_file_menu,
        "Move Selected Item to Trash",
        app.on_move_workspace_item_to_trash,
    )
    app.workspace_trash_item.set_sensitive(bool(getattr(app, "workspace_root", None)))
    add_separator(app.workspace_file_menu)
    add_item(
        app.workspace_file_menu,
        "Change Workspace Folder…",
        app.on_select_workspace_folder,
    )
    app.recent_workspaces_item = Gtk.MenuItem(label="Recent Workspaces")
    app.recent_workspaces_menu = Gtk.Menu()
    app.recent_workspaces_item.set_submenu(app.recent_workspaces_menu)
    app.workspace_file_menu.append(app.recent_workspaces_item)
    app.populate_recent_workspaces_menu()
    add_separator(app.workspace_file_menu)
    add_item(app.workspace_file_menu, "Rescan Folder Contents", app.on_refresh_workspace)
    add_item(app.workspace_file_menu, "Reveal Workspace Folder in File Manager", app.on_reveal_workspace)
    add_item(app.workspace_file_menu, "Close Workspace", app.on_close_workspace)
    add_separator(filem)
    add_item(filem, "Save\tCtrl+S", app.on_save)
    add_item(filem, "Save As…\tCtrl+Shift+S", app.on_save_as)
    add_item(filem, "Save as Template…", app.on_save_as_template)
    add_item(filem, "Manage Templates…", app.on_manage_templates)

    app.favourites_item = Gtk.MenuItem(label="Favorites")
    favm = Gtk.Menu()
    app.favourites_item.set_submenu(favm)
    filem.append(app.favourites_item)
    add_item(favm, "Add to Favourites\tCtrl+Alt+B", app.on_add_favourite)
    add_item(favm, "Edit Favourites…\tCtrl+Shift+D", app.on_edit_favourites)
    add_item(favm, "Reload Favourites\tCtrl+Alt+R", app.on_reload_favourites)
    add_separator(favm)
    app.favourites_menu = favm
    app.populate_favourites_menu()

    add_separator(filem)
    add_item(filem, "Print Preview…\tCtrl+Shift+P", app.on_print_preview)
    add_item(filem, "Print…\tCtrl+P", app.on_print)
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
    add_item(editm, "Find All…", app.on_find_all)
    add_item(editm, "Find Next Word\tCtrl+G", app.on_find_next)
    add_item(editm, "Find Previous\tCtrl+Shift+G", app.on_find_previous)
    add_item(editm, "Replace\tCtrl+H", app.on_find_replace)
    add_item(editm, "Replace All\tCtrl+Shift+H", app.on_replace_all_dialog)

    researchm = top_menu(app, "Research")
    app.research_item = Gtk.CheckMenuItem(label="Research Panel\tCtrl+Alt+C")
    app.research_item.set_active(False)
    connect_check_command(app.research_item, app, "research.panel")
    researchm.append(app.research_item)
    add_separator(researchm)
    add_item(researchm, "Clip Collection", app.show_clip_collection)
    add_item(researchm, "Insert Clip…\tCtrl+Alt+K", app.on_insert_clip)
    add_item(researchm, "Scratchpad\tCtrl+Alt+S", app.show_scratchpad)
    add_item(researchm, "Bibliography", app.show_references)
    add_item(researchm, "Open Bibliography File", app.on_open_bibliography_file)
    add_item(researchm, "Export Bibliography as Markdown…", app.on_export_bibliography_markdown)
    add_item(researchm, "Export Bibliography as Text…", app.on_export_bibliography_text)
    add_item(researchm, "Tags", app.show_tags)
    add_item(researchm, "Reference Sets", app.show_reference_sets)
    add_item(researchm, "Source Notes", app.show_source_notes)
    add_item(researchm, "Authoring Bridge", app.show_authoring_bridge)
    add_separator(researchm)
    add_item(researchm, "Capture Selection in Scratchpad…\tCtrl+Alt+Shift+S", app.on_capture_selection_in_scratchpad)
    add_item(researchm, "New Scratchpad Entry for Current Section…", app.on_new_scratchpad_for_current_section)
    add_item(researchm, "Show Scratchpad for Current Section", app.on_show_scratchpad_for_current_section)
    add_separator(researchm)
    add_item(
        researchm,
        "Create Source Note from Selection…",
        app.on_create_source_note_from_selection,
    )
    add_item(researchm, "Insert Link to Heading…", app.on_insert_link_to_heading)
    add_separator(researchm)
    add_item(researchm, "Quick Cite…	Ctrl+Alt+Q", app.on_quick_cite)
    add_item(
        researchm,
        "Open Citation in Bibliography	Ctrl+Alt+Shift+Q",
        app.on_open_citation_in_references,
    )
    add_separator(researchm)
    add_item(researchm, "Rename Reference Key…", app.on_rename_reference_key)
    add_item(researchm, "Research Check…", app.on_research_check)
    add_item(researchm, "Tag Integrity…", app.on_tag_integrity)
    add_separator(researchm)
    add_item(researchm, "Import BibTeX/BibLaTeX…", app.on_import_bibtex_biblatex)
    add_item(
        researchm,
        "Export References as BibTeX/BibLaTeX…",
        app.on_export_references_bibtex_biblatex,
    )
    add_item(researchm, "Export Research Apparatus…", app.on_export_research_apparatus)
    add_item(researchm, "Export with Pandoc/citeproc…", app.on_export_with_pandoc)

    navigatem = top_menu(app, "Navigate")
    app.navigator_item = Gtk.CheckMenuItem(label="Navigator Panel\tCtrl+Alt+N")
    app.navigator_item.set_active(False)
    connect_check_command(app.navigator_item, app, "navigate.navigator-panel")
    navigatem.append(app.navigator_item)
    app.workspace_item = Gtk.CheckMenuItem(label="Writing Workspace")
    app.workspace_item.set_active(False)
    connect_check_command(app.workspace_item, app, "navigate.workspace-panel")
    navigatem.append(app.workspace_item)
    add_item(navigatem, "Document Overview", app.on_document_overview)
    add_separator(navigatem)
    add_item(navigatem, "Go to Line…\tCtrl+L", app.on_go_to_line)
    add_item(navigatem, "Go to Section…\tCtrl+Shift+L", app.on_go_to_section)
    add_separator(navigatem)
    add_item(navigatem, "Insert Bookmark Here\tCtrl+F2", app.toggle_bookmark)
    add_item(navigatem, "Next Bookmark\tF2", app.next_bookmark)
    add_item(navigatem, "Previous Bookmark\tShift+F2", app.previous_bookmark)
    add_item(navigatem, "Manage Bookmarks…", app.on_manage_bookmarks)
    add_separator(navigatem)
    add_item(navigatem, "Next Heading\tCtrl+PageDown", app.on_next_heading)
    add_item(navigatem, "Previous Heading\tCtrl+PageUp", app.on_previous_heading)

    writingm = top_menu(app, "Writing")
    app.typewriter_item = Gtk.CheckMenuItem(label="Typewriter Mode\tShift+F9")
    app.typewriter_item.set_active(False)
    connect_check_command(app.typewriter_item, app, "writing.typewriter-mode")
    writingm.append(app.typewriter_item)
    add_separator(writingm)
    add_item(writingm, "Insert Date", app.on_insert_date)
    add_item(writingm, "Insert Time", app.on_insert_time)
    add_item(writingm, "Insert Date and Time\tCtrl+Alt+D", app.on_insert_datetime)

    revisem = top_menu(app, "Revise")
    add_item(revisem, "UPPERCASE (convert selected)\tCtrl+Alt+U", app.on_uppercase)
    add_item(revisem, "Lowercase (convert selected)\tCtrl+Alt+Shift+U", app.on_lowercase)
    add_item(revisem, "Title Case\tCtrl+Alt+Y", app.on_title_case)
    add_item(revisem, "Sentence case\tCtrl+Alt+Shift+Y", app.on_sentence_case)
    add_separator(revisem)
    add_item(revisem, "Paste Clean from PDF\tCtrl+Alt+V", app.on_paste_clean_pdf)
    add_item(revisem, "Clean Selected Text from PDF\tCtrl+Alt+Shift+V", app.on_clean_selected_pdf)
    add_item(revisem, "Smart Typography\tCtrl+Alt+M", app.on_smart_typography)
    add_item(revisem, "Reflow Paragraph\tCtrl+Alt+J", app.on_reflow_paragraph)
    add_item(revisem, "Join Lines\tCtrl+J", app.on_join_lines)
    add_item(revisem, "Remove Extra Spaces", app.on_remove_extra_spaces)
    add_item(revisem, "Remove Trailing Spaces", app.on_remove_trailing_spaces)
    add_item(revisem, "Sort Alphabetically A-Z\tCtrl+Alt+Up", app.on_sort_lines_ascending)
    add_item(revisem, "Sort Alphabetically Z-A\tCtrl+Alt+Down", app.on_sort_lines_descending)

    viewm = top_menu(app, "View")
    add_item(viewm, "Focus Mode\tF9", app.toggle_focus_mode)
    add_item(viewm, "Distraction-Free Mode\tF11", app.toggle_distraction_free)
    add_item(viewm, "Highlight Current Line\tCtrl+Alt+I", app.toggle_current_line_highlight)
    add_item(viewm, "Character Map\tCtrl+Alt+F10", app.on_character_map)

    optm = top_menu(app, "Options")
    app.word_wrap_item = Gtk.CheckMenuItem(label="Word Wrap\tAlt+Z")
    app.word_wrap_item.set_active(app.word_wrap)
    connect_check_command(app.word_wrap_item, app, "options.word-wrap")
    optm.append(app.word_wrap_item)
    add_item(optm, "Font…\tCtrl+Shift+F", app.on_font)
    app.transparent_item = Gtk.CheckMenuItem(label="Transparent Mode\tCtrl+Shift+T")
    app.transparent_item.set_active(app.opacity_percent < 100)
    connect_check_command(app.transparent_item, app, "options.transparent-mode")
    optm.append(app.transparent_item)
    app.always_item = Gtk.CheckMenuItem(label="Always on Top\tCtrl+Shift+A")
    app.always_item.set_active(app.always_on_top)
    connect_check_command(app.always_item, app, "options.always-on-top")
    optm.append(app.always_item)
    add_separator(optm)
    app.white_item = Gtk.CheckMenuItem(label="White Background")
    app.white_item.set_active(app.appearance_mode == "light")
    connect_check_command(app.white_item, app, "options.appearance.light")
    optm.append(app.white_item)
    app.dark_item = Gtk.CheckMenuItem(label="Dark Mode")
    app.dark_item.set_active(app.appearance_mode == "dark")
    connect_check_command(app.dark_item, app, "options.appearance.dark")
    optm.append(app.dark_item)
    app.line_item = Gtk.CheckMenuItem(label="Line Numbers\tCtrl+Alt+L")
    app.line_item.set_active(app.line_numbers_enabled)
    connect_check_command(app.line_item, app, "options.line-numbers")
    optm.append(app.line_item)
    add_separator(optm)
    add_command_item(optm, "Font Bigger\tCtrl++", app, "options.font-size.adjust", {"delta": 1})
    add_command_item(optm, "Font Smaller\tCtrl+-", app, "options.font-size.adjust", {"delta": -1})
    add_separator(optm)
    opacity_item = Gtk.MenuItem(label="Opacity")
    opacity_menu = Gtk.Menu()
    opacity_item.set_submenu(opacity_menu)
    optm.append(opacity_item)
    add_item(opacity_menu, "Opacity Selection…", app.on_opacity_selection)
    add_separator(opacity_menu)
    for opacity in (100, 90, 88, 80, 70, 60, 50, 40, 30):
        add_command_item(opacity_menu, f"{opacity}%", app, "options.opacity.set", {"percent": opacity})

    toolsm = top_menu(app, "Tools")
    add_item(toolsm, "External Spellcheck\tF7", app.on_check)
    add_item(toolsm, "Document Statistics\tCtrl+Alt+W", app.on_document_statistics)
    add_separator(toolsm)
    add_item(toolsm, "Language…", app.on_language_selection)
    add_item(toolsm, "System Info…", app.on_system_info)

    helpm = top_menu(app, "Help")
    add_item(helpm, "User Guide…", app.on_user_guide)
    add_item(helpm, "Keyboard Shortcuts\tCtrl+/", app.on_keyboard_shortcuts)
    add_separator(helpm)
    add_item(helpm, "About\tF1", app.on_about)


def shortcut_bindings(app):
    rows = []
    for accelerator, command_id, data in command_shortcut_bindings():
        payload = dict(data)
        rows.append((
            accelerator,
            lambda *_args, cid=command_id, values=payload: app.invoke_command(
                cid, source="shortcut", data=values
            ),
        ))
    return tuple(rows)


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
