"""GTK dialogs for explicit Clip Collection operations."""
from __future__ import annotations

from typing import Any, Callable, Iterable

from calamus_clip_search import clip_preview, search_clips
from calamus_clips import ClipValidationError, validate_shortcut


def run_clip_editor_dialog(
    parent,
    *,
    title: str = "",
    shortcut: str = "",
    text: str = "",
    dialog_title: str = "New Clip",
    existing_shortcuts: Iterable[str] = (),
    current_shortcut: str = "",
) -> dict[str, str] | None:
    from gi.repository import Gtk

    existing = {value.casefold() for value in existing_shortcuts if isinstance(value, str) and value}
    existing.discard(current_shortcut.casefold())
    dialog = Gtk.Dialog(title=dialog_title, transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Save", Gtk.ResponseType.OK)
    dialog.set_default_size(620, 500)

    grid = Gtk.Grid(column_spacing=8, row_spacing=7)
    grid.set_margin_start(10)
    grid.set_margin_end(10)
    grid.set_margin_top(10)
    grid.set_margin_bottom(10)
    dialog.get_content_area().pack_start(grid, True, True, 0)

    title_label = Gtk.Label(label="Title")
    title_label.set_xalign(0)
    title_entry = Gtk.Entry()
    title_entry.set_name("calamus-clip-title-entry")
    title_entry.set_text(title)
    title_entry.set_hexpand(True)
    grid.attach(title_label, 0, 0, 1, 1)
    grid.attach(title_entry, 1, 0, 1, 1)

    shortcut_label = Gtk.Label(label="Shortcut")
    shortcut_label.set_xalign(0)
    shortcut_entry = Gtk.Entry()
    shortcut_entry.set_name("calamus-clip-shortcut-entry")
    shortcut_entry.set_text(shortcut)
    shortcut_entry.set_placeholder_text("Optional: firma, intro-articolo")
    shortcut_entry.set_tooltip_text("One unique mnemonic; it is not a tag.")
    grid.attach(shortcut_label, 0, 1, 1, 1)
    grid.attach(shortcut_entry, 1, 1, 1, 1)

    body_label = Gtk.Label(label="Body")
    body_label.set_xalign(0)
    body = Gtk.TextView()
    body.set_name("calamus-clip-body-view")
    body.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    body.get_buffer().set_text(text)
    body_scroll = Gtk.ScrolledWindow()
    body_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    body_scroll.set_vexpand(True)
    body_scroll.add(body)
    grid.attach(body_label, 0, 2, 1, 1)
    grid.attach(body_scroll, 1, 2, 1, 1)

    hint = Gtk.Label(label="Use {{cursor}} once to choose the caret position after insertion.")
    hint.set_xalign(0)
    hint.set_line_wrap(True)
    hint.get_style_context().add_class("dim-label")
    grid.attach(hint, 1, 3, 1, 1)

    dialog.show_all()
    title_entry.grab_focus()
    result = None
    while True:
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            break
        buffer = body.get_buffer()
        start, end = buffer.get_bounds()
        body_text = buffer.get_text(start, end, True)
        try:
            normalized = validate_shortcut(shortcut_entry.get_text())
            if normalized and normalized in existing:
                raise ClipValidationError(f"Shortcut '{normalized}' is already assigned to another clip.")
            if not body_text.strip():
                raise ClipValidationError("Clip body cannot be empty.")
            if body_text.count("{{cursor}}") > 1:
                raise ClipValidationError("A clip may contain at most one {{cursor}} marker.")
        except ClipValidationError as error:
            _message(dialog, Gtk.MessageType.ERROR, "Clip Collection", str(error))
            continue
        result = {
            "title": title_entry.get_text().strip(),
            "shortcut": normalized,
            "text": body_text,
        }
        break
    dialog.destroy()
    return result


def confirm_clip_delete(parent, clip: dict[str, Any]) -> bool:
    from gi.repository import Gtk

    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.NONE,
        text="Delete this clip permanently?",
    )
    dialog.format_secondary_text(clip.get("title", "Clip"))
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Delete", Gtk.ResponseType.OK)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK


def confirm_duplicate_body(parent, existing: dict[str, Any]) -> str:
    from gi.repository import Gtk

    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.NONE,
        text="An existing clip has the same body.",
    )
    dialog.format_secondary_text(existing.get("title", "Clip"))
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Select Existing", 10)
    dialog.add_button("Create Anyway", 20)
    response = dialog.run()
    dialog.destroy()
    return {10: "select", 20: "create"}.get(response, "cancel")


def show_stale_clip_message(parent, message: str) -> None:
    from gi.repository import Gtk
    _message(parent, Gtk.MessageType.WARNING, "Clip Collection changed outside Calamus", message)


def run_clip_selector_dialog(parent, clips: Iterable[dict[str, Any]]) -> str | None:
    from gi.repository import Gtk, Pango

    source = [dict(item) for item in clips]
    dialog = Gtk.Dialog(title="Insert Clip", transient_for=parent, modal=True)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Insert", Gtk.ResponseType.OK)
    dialog.set_default_size(620, 500)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    box.set_margin_start(10)
    box.set_margin_end(10)
    box.set_margin_top(10)
    box.set_margin_bottom(10)
    dialog.get_content_area().pack_start(box, True, True, 0)

    search = Gtk.SearchEntry()
    search.set_name("calamus-clip-selector-search")
    search.set_placeholder_text("Type a shortcut, title or body text")
    box.pack_start(search, False, False, 0)
    status = Gtk.Label()
    status.set_xalign(0)
    status.get_style_context().add_class("dim-label")
    box.pack_start(status, False, False, 0)

    listbox = Gtk.ListBox()
    listbox.set_name("calamus-clip-selector-list")
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    listbox.set_activate_on_single_click(False)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)
    scroll.add(listbox)
    box.pack_start(scroll, True, True, 0)

    visible: list[dict[str, Any]] = []

    def selected_id() -> str | None:
        row = listbox.get_selected_row()
        value = getattr(row, "_calamus_clip_id", None) if row is not None else None
        return value if isinstance(value, str) and value else None

    def render(*_args):
        nonlocal visible
        previous = selected_id()
        visible = search_clips(source, search.get_text())
        for child in list(listbox.get_children()):
            listbox.remove(child)
        for clip in visible:
            row = Gtk.ListBoxRow()
            row._calamus_clip_id = clip.get("id", "")
            item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            item_box.set_margin_top(4)
            item_box.set_margin_bottom(4)
            item_box.set_margin_start(4)
            item_box.set_margin_end(4)
            shortcut = clip.get("shortcut", "") or "—"
            heading = Gtk.Label(label=f"[{shortcut}]  {clip.get('title', 'Clip')}")
            heading.set_xalign(0)
            heading.set_ellipsize(Pango.EllipsizeMode.END)
            item_box.pack_start(heading, False, False, 0)
            preview = Gtk.Label(label=clip_preview(clip.get("text", ""), 120))
            preview.set_xalign(0)
            preview.set_ellipsize(Pango.EllipsizeMode.END)
            preview.get_style_context().add_class("dim-label")
            item_box.pack_start(preview, False, False, 0)
            row.add(item_box)
            listbox.add(row)
        status.set_text(f"{len(visible)} of {len(source)} clips" if search.get_text() else f"{len(source)} clips")
        listbox.show_all()
        target = next((row for row in listbox.get_children() if getattr(row, "_calamus_clip_id", None) == previous), None)
        if target is None and listbox.get_children():
            target = listbox.get_children()[0]
        if target is not None:
            listbox.select_row(target)

    search.connect("search-changed", render)
    listbox.connect("row-activated", lambda *_args: dialog.response(Gtk.ResponseType.OK))
    dialog.connect("key-press-event", lambda _d, event: _selector_keypress(dialog, listbox, event))
    render()
    dialog.show_all()
    search.grab_focus()
    response = dialog.run()
    result = selected_id() if response == Gtk.ResponseType.OK else None
    dialog.destroy()
    return result


def _selector_keypress(dialog, listbox, event) -> bool:
    from gi.repository import Gdk, Gtk
    if event.keyval == Gdk.KEY_Escape:
        dialog.response(Gtk.ResponseType.CANCEL)
        return True
    if event.keyval in (Gdk.KEY_Down, Gdk.KEY_Up):
        rows = listbox.get_children()
        if not rows:
            return False
        selected = listbox.get_selected_row()
        index = selected.get_index() if selected is not None else 0
        index = min(len(rows) - 1, index + 1) if event.keyval == Gdk.KEY_Down else max(0, index - 1)
        listbox.select_row(rows[index])
        return True
    if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
        if listbox.get_selected_row() is not None:
            dialog.response(Gtk.ResponseType.OK)
            return True
    return False


def _message(parent, message_type, title: str, secondary: str) -> None:
    from gi.repository import Gtk
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        modal=True,
        message_type=message_type,
        buttons=Gtk.ButtonsType.OK,
        text=title,
    )
    dialog.format_secondary_text(secondary)
    dialog.run()
    dialog.destroy()
