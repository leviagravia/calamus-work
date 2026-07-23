"""GTK master-list view for document-specific Calamus Source Notes."""
from __future__ import annotations

from typing import Any, Callable

from calamus_source_notes import SourceNote


class SourceNotePanelViewAdapter:
    def __init__(
        self,
        widget: Any,
        availability: Any,
        search: Any,
        kind_filter: Any,
        reference_filter: Any,
        listbox: Any,
        status: Any,
        action_widgets: tuple[Any, ...],
    ) -> None:
        self.widget = widget
        self._availability = availability
        self.search = search
        self._kind_filter = kind_filter
        self._reference_filter = reference_filter
        self._listbox = listbox
        self._status = status
        self._action_widgets = action_widgets
        self._rows: dict[str, Any] = {}
        self._syncing_reference_filter = False

    def bind_filters(
        self,
        on_search: Callable[[str], None],
        on_kind: Callable[[str], None],
        on_reference: Callable[[str], None],
    ) -> None:
        if not all(callable(callback) for callback in (on_search, on_kind, on_reference)):
            raise TypeError("filter callbacks must be callable")
        self.search.connect("search-changed", lambda entry: on_search(entry.get_text()))
        self._kind_filter.connect(
            "changed",
            lambda combo: on_kind(combo.get_active_id() or "all"),
        )

        def reference_changed(combo):
            if not self._syncing_reference_filter:
                on_reference(combo.get_active_id() or "all")

        self._reference_filter.connect("changed", reference_changed)

    def set_available(self, available: bool, message: str) -> None:
        enabled = bool(available)
        self._availability.set_text(message)
        self._availability.set_tooltip_text(message)
        self.search.set_sensitive(enabled)
        self._kind_filter.set_sensitive(enabled)
        self._reference_filter.set_sensitive(enabled)
        self._listbox.set_sensitive(enabled)
        for widget in self._action_widgets:
            widget.set_sensitive(enabled)

    def set_reference_options(self, keys: tuple[str, ...], selected: str) -> None:
        self._syncing_reference_filter = True
        try:
            self._reference_filter.remove_all()
            self._reference_filter.append("all", "All sources")
            for key in keys:
                self._reference_filter.append(key, key)
            target = selected if selected == "all" or selected in keys else "all"
            self._reference_filter.set_active_id(target)
        finally:
            self._syncing_reference_filter = False

    def render(
        self,
        notes: tuple[SourceNote, ...],
        selected_id: str | None,
        status: str,
        missing_reference_ids: frozenset[str],
        missing_target_ids: frozenset[str],
        ambiguous_target_ids: frozenset[str],
    ) -> None:
        from gi.repository import Gtk, Pango

        for child in list(self._listbox.get_children()):
            self._listbox.remove(child)
        self._rows = {}
        for note in notes:
            row = Gtk.ListBoxRow()
            row.source_note_id = note.id
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            box.set_margin_start(4)
            box.set_margin_end(4)

            primary = Gtk.Label()
            heading = note.kind.capitalize()
            if note.reference_key:
                heading += f" · {note.reference_key}"
            if note.target:
                heading += f" · {note.target}"
            primary.set_markup(f"<b>{_escape(heading)}</b>")
            primary.set_xalign(0)
            primary.set_ellipsize(Pango.EllipsizeMode.END)

            secondary = Gtk.Label(label=note.excerpt)
            secondary.set_xalign(0)
            secondary.set_line_wrap(True)
            secondary.set_max_width_chars(28)
            secondary.set_lines(2)

            details: list[str] = []
            if note.locator_text:
                details.append(note.locator_text)
            if note.tags:
                details.append(", ".join(note.tags))
            if note.id in missing_reference_ids:
                details.append("Missing reference")
            if note.id in missing_target_ids:
                details.append("Missing target")
            if note.id in ambiguous_target_ids:
                details.append("Ambiguous target")
            tertiary = Gtk.Label(label=" · ".join(details) or note.id)
            tertiary.set_xalign(0)
            tertiary.get_style_context().add_class("dim-label")
            tertiary.set_ellipsize(Pango.EllipsizeMode.END)

            box.pack_start(primary, False, False, 0)
            box.pack_start(secondary, False, False, 0)
            box.pack_start(tertiary, False, False, 0)
            row.add(box)
            self._listbox.add(row)
            self._rows[note.id] = row

        self._listbox.show_all()
        self._status.set_text(status)
        self.select_id(selected_id)

    def selected_id(self) -> str | None:
        row = self._listbox.get_selected_row()
        return getattr(row, "source_note_id", None) if row is not None else None

    def select_id(self, note_id: str | None) -> bool:
        if note_id is None:
            self._listbox.unselect_all()
            return False
        row = self._rows.get(note_id)
        if row is None:
            return False
        self._listbox.select_row(row)
        return True

    def focus_search(self) -> None:
        if self.search.get_sensitive():
            self.search.grab_focus()


def build_source_note_panel_view(
    on_add,
    on_edit,
    on_delete,
    on_open_reference,
    on_open_target,
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
    search.set_placeholder_text("Search Source Notes…")
    panel.pack_start(search, False, False, 0)

    kind_filter = Gtk.ComboBoxText()
    for key, label in (
        ("all", "All types"),
        ("quote", "Quotes"),
        ("paraphrase", "Paraphrases"),
        ("comment", "Comments"),
    ):
        kind_filter.append(key, label)
    kind_filter.set_active_id("all")
    kind_filter.set_hexpand(True)
    panel.pack_start(kind_filter, False, False, 0)

    reference_filter = Gtk.ComboBoxText()
    reference_filter.append("all", "All sources")
    reference_filter.set_active_id("all")
    reference_filter.set_hexpand(True)
    panel.pack_start(reference_filter, False, False, 0)

    status = Gtk.Label()
    status.set_xalign(0)
    status.set_line_wrap(True)
    panel.pack_start(status, False, False, 0)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.set_vexpand(True)
    scroll.add(listbox)
    panel.pack_start(scroll, True, True, 0)

    primary = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    buttons: list[Any] = []
    for label, callback in (
        ("Add", on_add),
        ("Edit", on_edit),
        ("Delete", on_delete),
    ):
        button = Gtk.Button(label=label)
        button.set_size_request(52, 26)
        button.connect("clicked", callback)
        primary.pack_start(button, True, True, 0)
        buttons.append(button)
    panel.pack_start(primary, False, False, 0)

    links = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    for label, callback in (
        ("Open Reference", on_open_reference),
        ("Open Target", on_open_target),
    ):
        button = Gtk.Button(label=label)
        button.set_size_request(-1, 26)
        button.connect("clicked", callback)
        links.pack_start(button, True, True, 0)
        buttons.append(button)
    panel.pack_start(links, False, False, 0)

    adapter = SourceNotePanelViewAdapter(
        panel,
        availability,
        search,
        kind_filter,
        reference_filter,
        listbox,
        status,
        tuple(buttons),
    )
    listbox.connect("row-activated", lambda *_: on_edit())
    return adapter


def _escape(value: str) -> str:
    from gi.repository import GLib
    return GLib.markup_escape_text(value or "")
