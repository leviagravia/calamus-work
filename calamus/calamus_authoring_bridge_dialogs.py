"""GTK dialogs for explicit Calamus Authoring Bridge authoring actions."""
from __future__ import annotations

from calamus_authoring_bridge import format_heading_link


def run_heading_link_dialog(
    parent,
    heading_options,
    *,
    default_identifier: str = "",
    default_label: str = "",
) -> tuple[str, str] | None:
    """Choose one explicit unique heading target and visible link label."""
    from gi.repository import Gtk

    options = tuple(heading_options)
    if not options:
        return None
    dialog = Gtk.Dialog(
        title="Insert Link to Heading",
        transient_for=parent,
        modal=True,
    )
    dialog.set_name("calamus-heading-link-dialog")
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Insert", Gtk.ResponseType.OK)
    dialog.set_default_size(560, 230)

    grid = Gtk.Grid(column_spacing=8, row_spacing=8)
    grid.set_border_width(12)
    dialog.get_content_area().pack_start(grid, True, True, 0)

    target_label = Gtk.Label(label="Heading")
    target_label.set_xalign(0)
    target_combo = Gtk.ComboBoxText()
    target_combo.set_name("heading-link-target")
    titles: dict[str, str] = {}
    for identifier, display, title in options:
        target_combo.append(identifier, display)
        titles[identifier] = title
    initial = default_identifier if default_identifier in titles else options[0][0]
    target_combo.set_active_id(initial)
    target_combo.set_hexpand(True)
    grid.attach(target_label, 0, 0, 1, 1)
    grid.attach(target_combo, 1, 0, 1, 1)

    label_label = Gtk.Label(label="Link text")
    label_label.set_xalign(0)
    label_entry = Gtk.Entry()
    label_entry.set_name("heading-link-label")
    label_entry.set_text(default_label.strip() or titles[initial])
    label_entry.set_hexpand(True)
    grid.attach(label_label, 0, 1, 1, 1)
    grid.attach(label_entry, 1, 1, 1, 1)

    preview = Gtk.Label()
    preview.set_name("heading-link-preview")
    preview.set_xalign(0)
    preview.set_selectable(True)
    preview.set_line_wrap(True)
    grid.attach(Gtk.Label(label="Preview"), 0, 2, 1, 1)
    grid.attach(preview, 1, 2, 1, 1)

    hint = Gtk.Label(
        label=(
            "Only explicit, unique Pandoc-compatible {#heading-id} targets are shown. "
            "The insertion is one Undo unit."
        )
    )
    hint.set_xalign(0)
    hint.set_line_wrap(True)
    grid.attach(hint, 0, 3, 2, 1)

    def refresh_preview(*_):
        identifier = target_combo.get_active_id() or ""
        try:
            preview.set_text(format_heading_link(label_entry.get_text(), identifier))
        except (TypeError, ValueError) as error:
            preview.set_text(str(error))

    target_combo.connect("changed", refresh_preview)
    label_entry.connect("changed", refresh_preview)
    refresh_preview()

    dialog.show_all()
    result = None
    while True:
        response = dialog.run()
        if response != Gtk.ResponseType.OK:
            break
        identifier = target_combo.get_active_id() or ""
        label = label_entry.get_text()
        try:
            format_heading_link(label, identifier)
        except (TypeError, ValueError) as error:
            message = Gtk.MessageDialog(
                transient_for=dialog,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=str(error),
            )
            message.run()
            message.destroy()
            continue
        result = identifier, label.strip()
        break
    dialog.destroy()
    return result
