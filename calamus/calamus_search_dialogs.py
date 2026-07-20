"""Dedicated GTK dialogs for Find/Replace and compact Find All results."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from calamus_search import SearchResult


def _margins(widget, value=10):
    widget.set_margin_start(value)
    widget.set_margin_end(value)
    widget.set_margin_top(value)
    widget.set_margin_bottom(value)


def run_find_all_dialog(parent, controller) -> None:
    dialog = Gtk.Dialog(title="Find All", transient_for=parent, modal=True)
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE, "Go to", 20, "Search", 10)
    dialog.set_default_size(720, 440)
    box = dialog.get_content_area()
    box.set_spacing(8)
    _margins(box)

    controls = Gtk.Grid(column_spacing=8, row_spacing=8)
    box.pack_start(controls, False, False, 0)

    label = Gtk.Label(label="Find:")
    label.set_xalign(0)
    entry = Gtk.Entry()
    entry.set_text(controller.query.text)
    entry.set_activates_default(True)
    case_item = Gtk.CheckButton(label="Match case")
    case_item.set_active(controller.query.options.match_case)
    word_item = Gtk.CheckButton(label="Whole word")
    word_item.set_active(controller.query.options.whole_word)
    controls.attach(label, 0, 0, 1, 1)
    controls.attach(entry, 1, 0, 2, 1)
    controls.attach(case_item, 1, 1, 1, 1)
    controls.attach(word_item, 2, 1, 1, 1)

    status = Gtk.Label()
    status.set_xalign(0)
    box.pack_start(status, False, False, 0)

    store = Gtk.ListStore(int, int, str, int, int)
    tree = Gtk.TreeView(model=store)
    tree.set_headers_visible(True)
    tree.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
    tree.append_column(Gtk.TreeViewColumn("Line", Gtk.CellRendererText(), text=0))
    tree.append_column(Gtk.TreeViewColumn("Column", Gtk.CellRendererText(), text=1))
    context_renderer = Gtk.CellRendererText()
    context_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
    tree.append_column(Gtk.TreeViewColumn("Context", context_renderer, text=2))

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(tree)
    box.pack_start(scroll, True, True, 0)

    go_button = dialog.get_widget_for_response(20)
    search_button = dialog.get_widget_for_response(10)
    go_button.set_sensitive(False)

    def selected_result():
        model, tree_iter = tree.get_selection().get_selected()
        if tree_iter is None:
            return None
        return SearchResult(
            line=model[tree_iter][0],
            column=model[tree_iter][1],
            context=model[tree_iter][2],
            start=model[tree_iter][3],
            end=model[tree_iter][4],
        )

    def update_go_button(_selection=None):
        go_button.set_sensitive(selected_result() is not None)

    def search_now():
        needle = entry.get_text()
        store.clear()
        go_button.set_sensitive(False)
        if not needle:
            status.set_text("Enter text to find.")
            return False
        results = controller.find_all(
            needle,
            match_case=case_item.get_active(),
            whole_word=word_item.get_active(),
            wrap=True,
        )
        for result in results:
            store.append(
                [result.line, result.column, result.context, result.start, result.end]
            )
        status.set_text(f"{len(results)} occurrence(s).")
        if results:
            tree.get_selection().select_path(0)
        return bool(results)

    def go_to_selected():
        result = selected_result()
        if result is None:
            return False
        controller.navigate_result(result)
        return True

    tree.get_selection().connect("changed", update_go_button)
    tree.connect("row-activated", lambda *_: go_to_selected())
    entry.connect("activate", lambda *_: search_now())
    dialog.set_default_response(10)
    dialog.show_all()
    entry.grab_focus()

    if controller.query.text:
        search_now()

    while True:
        response = dialog.run()
        if response in (Gtk.ResponseType.CLOSE, Gtk.ResponseType.DELETE_EVENT):
            break
        if response == 10:
            search_now()
        elif response == 20:
            go_to_selected()
    dialog.destroy()


def run_find_replace_dialog(parent, controller, replace_current, replace_all) -> None:
    dialog = Gtk.Dialog(title="Find / Replace", transient_for=parent, modal=False)
    dialog.add_buttons(
        "Close", Gtk.ResponseType.CLOSE,
        "Find Next", 10,
        "Find Previous", 15,
        "Find All", 18,
        "Replace", 20,
        "Replace All", 30,
    )
    dialog.set_default_size(580, 280)
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
    find_entry.set_text(controller.query.text)
    find_entry.set_activates_default(True)
    repl_entry.set_activates_default(True)
    grid.attach(find_label, 0, 0, 1, 1)
    grid.attach(find_entry, 1, 0, 1, 1)
    grid.attach(repl_label, 0, 1, 1, 1)
    grid.attach(repl_entry, 1, 1, 1, 1)

    case_item = Gtk.CheckButton(label="Match case")
    word_item = Gtk.CheckButton(label="Whole word")
    wrap_item = Gtk.CheckButton(label="Wrap around")
    case_item.set_active(controller.query.options.match_case)
    word_item.set_active(controller.query.options.whole_word)
    wrap_item.set_active(controller.query.options.wrap)
    grid.attach(case_item, 0, 2, 1, 1)
    grid.attach(word_item, 1, 2, 1, 1)
    grid.attach(wrap_item, 1, 3, 1, 1)

    status = Gtk.Label()
    status.set_xalign(0)
    grid.attach(status, 0, 4, 2, 1)

    def options():
        return case_item.get_active(), word_item.get_active(), wrap_item.get_active()

    def configure():
        needle = find_entry.get_text()
        match_case, whole_word, wrap = options()
        controller.configure(
            needle,
            match_case=match_case,
            whole_word=whole_word,
            wrap=wrap,
        )
        return needle, match_case, whole_word, wrap

    def do_find(backwards=False):
        needle, match_case, whole_word, wrap = configure()
        if not needle:
            status.set_text("Enter text to find.")
            return False
        matches = controller.highlight()
        ok = controller.find(backwards=backwards)
        direction = "previous" if backwards else "next"
        status.set_text(
            (f"Found {direction}. {matches} match(es) highlighted.")
            if ok else "No match found."
        )
        return ok

    def do_find_all():
        needle, _match_case, _whole_word, _wrap = configure()
        if not needle:
            status.set_text("Enter text to find.")
            return
        dialog.hide()
        try:
            run_find_all_dialog(parent, controller)
        finally:
            dialog.show_all()

    def do_replace():
        needle, _match_case, _whole_word, _wrap = configure()
        replacement = repl_entry.get_text()
        if not needle:
            status.set_text("Enter text to find.")
            return
        if controller.current_match is None and not do_find(False):
            return
        if replace_current(replacement):
            controller.highlight()
            status.set_text("Replaced selected match.")
        else:
            status.set_text("No current match to replace.")

    def do_replace_all():
        needle, _match_case, _whole_word, _wrap = configure()
        if not needle:
            status.set_text("Enter text to find.")
            return
        count = replace_all(repl_entry.get_text())
        controller.highlight()
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
        elif response == 18:
            do_find_all()
        elif response == 20:
            do_replace()
        elif response == 30:
            do_replace_all()
    dialog.destroy()
