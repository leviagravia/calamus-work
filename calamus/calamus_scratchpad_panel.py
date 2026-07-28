"""GTK master-list view for the document-local Calamus Scratchpad."""
from __future__ import annotations

from typing import Any, Callable

from calamus_scratchpad import ScratchpadEntry


class ScratchpadPanelViewAdapter:
    def __init__(
        self,
        widget: Any,
        availability: Any,
        search: Any,
        type_filter: Any,
        status_filter: Any,
        tag_filter: Any,
        section_filter_label: Any,
        listbox: Any,
        status: Any,
        action_widgets: tuple[Any, ...],
    ) -> None:
        self.widget = widget
        self._availability = availability
        self.search = search
        self._type_filter = type_filter
        self._status_filter = status_filter
        self._tag_filter = tag_filter
        self._section_filter_label = section_filter_label
        self._listbox = listbox
        self._status = status
        self._action_widgets = action_widgets
        self._rows: dict[str, Any] = {}
        self._syncing_filters = False
        self._syncing_tag_filter = False

    def bind_filters(
        self,
        on_search: Callable[[str], None],
        on_type: Callable[[str], None],
        on_status: Callable[[str], None],
        on_tag: Callable[[str], None],
    ) -> None:
        if not all(callable(callback) for callback in (on_search, on_type, on_status, on_tag)):
            raise TypeError("filter callbacks must be callable")
        self.search.connect(
            "search-changed",
            lambda entry: None if self._syncing_filters else on_search(entry.get_text()),
        )
        self._type_filter.connect(
            "changed",
            lambda combo: None if self._syncing_filters else on_type(combo.get_active_id() or "all"),
        )
        self._status_filter.connect(
            "changed",
            lambda combo: None if self._syncing_filters else on_status(combo.get_active_id() or "active-work"),
        )
        self._tag_filter.connect(
            "changed",
            lambda combo: None if self._syncing_filters or self._syncing_tag_filter else on_tag(combo.get_active_id() or "all"),
        )

    def set_available(self, available: bool, message: str) -> None:
        enabled = bool(available)
        self._availability.set_text(message)
        self._availability.set_tooltip_text(message)
        self.search.set_sensitive(enabled)
        self._type_filter.set_sensitive(enabled)
        self._status_filter.set_sensitive(enabled)
        self._tag_filter.set_sensitive(enabled)
        self._listbox.set_sensitive(enabled)
        for widget in self._action_widgets:
            widget.set_sensitive(enabled)

    def set_tag_options(self, tags: tuple[str, ...], selected: str) -> None:
        self._syncing_tag_filter = True
        try:
            self._tag_filter.remove_all()
            self._tag_filter.append("all", "All tags")
            selected_id = "all"
            for tag in tags:
                key = tag.casefold()
                self._tag_filter.append(key, tag)
                if selected != "all" and selected.casefold() == key:
                    selected_id = key
            self._tag_filter.set_active_id(selected_id)
        finally:
            self._syncing_tag_filter = False

    def set_section_filter_label(self, value: str) -> None:
        self._section_filter_label.set_text(f"Section filter: {value}")
        self._section_filter_label.set_tooltip_text(value)

    def render(
        self,
        entries: tuple[ScratchpadEntry, ...],
        selected_id: str | None,
        status: str,
        missing_section_ids: frozenset[str],
        ambiguous_section_ids: frozenset[str],
    ) -> None:
        from gi.repository import Gtk, Pango

        for child in list(self._listbox.get_children()):
            self._listbox.remove(child)
        self._rows = {}
        for entry in entries:
            row = Gtk.ListBoxRow()
            row.scratchpad_entry_id = entry.id
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            box.set_margin_start(4)
            box.set_margin_end(4)

            primary = Gtk.Label()
            primary.set_markup(f"<b>{_escape(entry.title)}</b>")
            primary.set_xalign(0)
            primary.set_ellipsize(Pango.EllipsizeMode.END)

            secondary = Gtk.Label(label=entry.excerpt)
            secondary.set_xalign(0)
            secondary.set_line_wrap(True)
            secondary.set_max_width_chars(28)
            secondary.set_lines(2)

            details = [entry.type.capitalize(), entry.status.capitalize()]
            if entry.tags:
                details.append(", ".join(entry.tags))
            if entry.sections:
                details.append("; ".join(entry.sections))
            if entry.id in missing_section_ids:
                details.append("Missing section")
            if entry.id in ambiguous_section_ids:
                details.append("Ambiguous section")
            tertiary = Gtk.Label(label=" · ".join(details))
            tertiary.set_xalign(0)
            tertiary.get_style_context().add_class("dim-label")
            tertiary.set_ellipsize(Pango.EllipsizeMode.END)

            box.pack_start(primary, False, False, 0)
            box.pack_start(secondary, False, False, 0)
            box.pack_start(tertiary, False, False, 0)
            row.add(box)
            self._listbox.add(row)
            self._rows[entry.id] = row

        self._listbox.show_all()
        self._status.set_text(status)
        self.select_id(selected_id)

    def selected_id(self) -> str | None:
        row = self._listbox.get_selected_row()
        return getattr(row, "scratchpad_entry_id", None) if row is not None else None

    def select_id(self, entry_id: str | None) -> bool:
        if entry_id is None:
            self._listbox.unselect_all()
            return False
        row = self._rows.get(entry_id)
        if row is None:
            return False
        self._listbox.select_row(row)
        return True

    def reset_filters(self) -> None:
        self._syncing_filters = True
        try:
            self.search.set_text("")
            self._type_filter.set_active_id("all")
            self._status_filter.set_active_id("all")
            self._tag_filter.set_active_id("all")
            self.set_section_filter_label("All sections")
        finally:
            self._syncing_filters = False

    def focus_search(self) -> None:
        if self.search.get_sensitive():
            self.search.grab_focus()


def _dispatch_scratchpad_list_key(key: str, on_add, on_delete, on_refresh) -> bool:
    """Dispatch one list-local Scratchpad key without owning GTK state."""
    if key == "Insert":
        on_add()
        return True
    if key in {"Delete", "KP_Delete"}:
        on_delete()
        return True
    if key == "F5":
        on_refresh()
        return True
    return False


def build_scratchpad_panel_view(
    on_add,
    on_edit,
    on_archive,
    on_delete,
    on_open_section,
    on_insert,
    on_copy,
    on_clear_section_filter,
    on_refresh,
):
    from gi.repository import Gtk, Pango

    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    panel.set_margin_start(4)
    panel.set_margin_end(4)
    panel.set_margin_top(4)
    panel.set_margin_bottom(4)

    availability = Gtk.Label()
    availability.set_xalign(0)
    availability.set_ellipsize(Pango.EllipsizeMode.END)
    availability.get_style_context().add_class("dim-label")
    panel.pack_start(availability, False, False, 0)

    search = Gtk.SearchEntry()
    search.set_name("scratchpad-search")
    search.set_placeholder_text("Search Scratchpad…")
    panel.pack_start(search, False, False, 0)

    filters = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    type_filter = Gtk.ComboBoxText()
    for key, label in (("all", "All types"), ("note", "Notes"), ("idea", "Ideas"), ("draft", "Drafts"), ("task", "Tasks")):
        type_filter.append(key, label)
    type_filter.set_active_id("all")
    type_filter.set_hexpand(True)
    filters.pack_start(type_filter, True, True, 0)

    status_filter = Gtk.ComboBoxText()
    for key, label in (("active-work", "Current work"), ("all", "All states"), ("inbox", "Inbox"), ("active", "Active"), ("resolved", "Resolved"), ("archived", "Archived")):
        status_filter.append(key, label)
    status_filter.set_active_id("active-work")
    status_filter.set_hexpand(True)
    filters.pack_start(status_filter, True, True, 0)
    panel.pack_start(filters, False, False, 0)

    tag_filter = Gtk.ComboBoxText()
    tag_filter.append("all", "All tags")
    tag_filter.set_active_id("all")
    tag_filter.set_hexpand(True)
    panel.pack_start(tag_filter, False, False, 0)

    section_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    section_filter_label = Gtk.Label(label="Section filter: All sections")
    section_filter_label.set_xalign(0)
    section_filter_label.set_ellipsize(Pango.EllipsizeMode.END)
    section_filter_label.set_hexpand(True)
    section_row.pack_start(section_filter_label, True, True, 0)
    clear_section = Gtk.Button(label="All")
    clear_section.set_tooltip_text("Clear current-section filter")
    clear_section.connect("clicked", on_clear_section_filter)
    section_row.pack_end(clear_section, False, False, 0)
    refresh = Gtk.Button(label="Refresh")
    refresh.set_tooltip_text("Reload the current Scratchpad sidecar from disk")
    refresh.connect("clicked", on_refresh)
    section_row.pack_end(refresh, False, False, 0)
    panel.pack_start(section_row, False, False, 0)

    status = Gtk.Label()
    status.set_xalign(0)
    status.set_line_wrap(True)
    panel.pack_start(status, False, False, 0)

    listbox = Gtk.ListBox()
    listbox.set_name("scratchpad-list")
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)
    scroll.add(listbox)
    panel.pack_start(scroll, True, True, 0)

    buttons: list[Any] = [clear_section, refresh]
    primary = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    for label, callback in (("New", on_add), ("Edit", on_edit), ("Archive", on_archive), ("Delete", on_delete)):
        button = Gtk.Button(label=label)
        button.set_size_request(48, 26)
        button.connect("clicked", callback)
        primary.pack_start(button, True, True, 0)
        buttons.append(button)
    panel.pack_start(primary, False, False, 0)

    actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    for label, callback in (("Open Section", on_open_section), ("Insert", on_insert), ("Copy", on_copy)):
        button = Gtk.Button(label=label)
        button.set_size_request(-1, 26)
        button.connect("clicked", callback)
        actions.pack_start(button, True, True, 0)
        buttons.append(button)
    panel.pack_start(actions, False, False, 0)

    adapter = ScratchpadPanelViewAdapter(
        panel,
        availability,
        search,
        type_filter,
        status_filter,
        tag_filter,
        section_filter_label,
        listbox,
        status,
        tuple(buttons),
    )
    listbox.connect("row-activated", lambda *_: on_edit())

    def on_list_key_press(_widget, event):
        from gi.repository import Gdk
        key = Gdk.keyval_name(event.keyval) or ""
        return _dispatch_scratchpad_list_key(key, on_add, on_delete, on_refresh)

    listbox.connect("key-press-event", on_list_key_press)
    return adapter


def _escape(value: str) -> str:
    from gi.repository import GLib
    return GLib.markup_escape_text(value or "")
