"""GTK dialogs for Calamus line and document-structure navigation."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from calamus_document_structure import DocumentHeading


def _margins(widget, value=10):
    widget.set_margin_start(value)
    widget.set_margin_end(value)
    widget.set_margin_top(value)
    widget.set_margin_bottom(value)


def run_go_to_line_dialog(parent, controller) -> bool:
    total_lines = controller.line_count()
    dialog = Gtk.Dialog(title="Go to Line", transient_for=parent, modal=True)
    dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Go", Gtk.ResponseType.OK)
    content = dialog.get_content_area()
    content.set_spacing(8)
    _margins(content)

    label = Gtk.Label(label=f"Line number (1-{total_lines}):")
    label.set_xalign(0)
    entry = Gtk.Entry()
    entry.set_text("1")
    entry.set_activates_default(True)
    content.pack_start(label, False, False, 0)
    content.pack_start(entry, False, False, 0)
    status = Gtk.Label()
    status.set_xalign(0)
    content.pack_start(status, False, False, 0)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()
    entry.grab_focus()

    navigated = False
    while True:
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            break
        try:
            requested = int(entry.get_text().strip())
        except ValueError:
            status.set_text("Invalid line number.")
            entry.select_region(0, -1)
            continue
        controller.go_to_line(requested)
        navigated = True
        break
    dialog.destroy()
    return navigated


def run_go_to_section_dialog(parent, controller) -> bool:
    """Show a compact, filterable view of current Markdown headings."""
    dialog = Gtk.Dialog(title="Go to Section", transient_for=parent, modal=True)
    dialog.add_buttons("Close", Gtk.ResponseType.CLOSE, "Go", Gtk.ResponseType.OK)
    dialog.set_default_size(560, 420)
    content = dialog.get_content_area()
    content.set_spacing(8)
    _margins(content)

    label = Gtk.Label(label="Filter headings:")
    label.set_xalign(0)
    entry = Gtk.SearchEntry()
    entry.set_activates_default(True)
    content.pack_start(label, False, False, 0)
    content.pack_start(entry, False, False, 0)

    status = Gtk.Label()
    status.set_xalign(0)
    content.pack_start(status, False, False, 0)

    store = Gtk.ListStore(str, int, object)
    tree = Gtk.TreeView(model=store)
    tree.set_headers_visible(True)
    selection = tree.get_selection()
    selection.set_mode(Gtk.SelectionMode.SINGLE)
    tree.append_column(Gtk.TreeViewColumn("Section", Gtk.CellRendererText(), text=0))
    tree.append_column(Gtk.TreeViewColumn("Line", Gtk.CellRendererText(), text=1))

    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(tree)
    content.pack_start(scroll, True, True, 0)

    go_button = dialog.get_widget_for_response(Gtk.ResponseType.OK)
    go_button.set_sensitive(False)

    def selected_heading() -> DocumentHeading | None:
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            return None
        heading = model[tree_iter][2]
        return heading if isinstance(heading, DocumentHeading) else None

    def update_button(_selection=None) -> None:
        go_button.set_sensitive(selected_heading() is not None)

    def refill(*_args) -> None:
        store.clear()
        query = entry.get_text()
        headings = controller.headings(query)
        current = controller.current_heading() if not query.strip() else None
        selected_path = None
        for index, heading in enumerate(headings):
            indent = "    " * max(0, heading.level - 1)
            store.append([f"{indent}{heading.display_title}", heading.line, heading])
            if heading == current:
                selected_path = index
        status.set_text(
            f"{len(headings)} section(s)."
            if headings else "No matching Markdown headings."
        )
        if headings:
            selection.select_path(selected_path if selected_path is not None else 0)

    def activate_selected() -> bool:
        heading = selected_heading()
        if heading is None:
            return False
        controller.navigate_heading(heading)
        return True

    selection.connect("changed", update_button)
    entry.connect("search-changed", refill)
    entry.connect("activate", lambda *_: dialog.response(Gtk.ResponseType.OK))
    tree.connect("row-activated", lambda *_: dialog.response(Gtk.ResponseType.OK))
    dialog.set_default_response(Gtk.ResponseType.OK)
    refill()
    dialog.show_all()
    entry.grab_focus()

    navigated = False
    while True:
        response = dialog.run()
        if response in (Gtk.ResponseType.CLOSE, Gtk.ResponseType.DELETE_EVENT):
            break
        if response == Gtk.ResponseType.OK and activate_selected():
            navigated = True
            break
    dialog.destroy()
    return navigated
