"""GTK view for the Calamus Authoring Bridge Research client."""
from __future__ import annotations

from typing import Any, Callable

from calamus_authoring_bridge import BridgeOccurrence, BridgeSubject


def _gtk_pango():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Pango", "1.0")
    from gi.repository import Gtk, Pango
    return Gtk, Pango


def _gtk():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    return Gtk


def _glib():
    from gi.repository import GLib
    return GLib

class AuthoringBridgeViewAdapter:
    def __init__(
        self,
        widget: Any,
        mode_selector: Any,
        subject_selector: Any,
        listbox: Any,
        status: Any,
    ) -> None:
        self.widget = widget
        self._mode_selector = mode_selector
        self._subject_selector = subject_selector
        self._listbox = listbox
        self._status = status
        self._rows: dict[str, Any] = {}
        self._syncing = False

    def bind_controls(
        self,
        on_mode: Callable[[str], None],
        on_subject: Callable[[str | None], None],
    ) -> None:
        if not all(callable(callback) for callback in (on_mode, on_subject)):
            raise TypeError("Authoring Bridge control callbacks must be callable")

        def mode_changed(combo):
            if not self._syncing:
                on_mode(combo.get_active_id() or "reference")

        def subject_changed(combo):
            if not self._syncing:
                on_subject(combo.get_active_id())

        self._mode_selector.connect("changed", mode_changed)
        self._subject_selector.connect("changed", subject_changed)

    def set_subjects(
        self,
        mode: str,
        subjects: tuple[BridgeSubject, ...],
        selected_id: str | None,
    ) -> None:
        self._syncing = True
        try:
            self._mode_selector.set_active_id(mode)
            self._subject_selector.remove_all()
            for subject in subjects:
                self._subject_selector.append(subject.identifier, subject.label)
            if selected_id is not None:
                self._subject_selector.set_active_id(selected_id)
            elif subjects:
                self._subject_selector.set_active(0)
            self._subject_selector.set_sensitive(bool(subjects))
        finally:
            self._syncing = False

    def render(
        self,
        occurrences: tuple[BridgeOccurrence, ...],
        selected_id: str | None,
        status: str,
    ) -> None:
        Gtk, Pango = _gtk_pango()

        for child in list(self._listbox.get_children()):
            self._listbox.remove(child)
        self._rows = {}
        for occurrence in occurrences:
            row = Gtk.ListBoxRow()
            row.bridge_occurrence_id = occurrence.id
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            box.set_margin_start(4)
            box.set_margin_end(4)

            primary = Gtk.Label()
            primary.set_markup(f"<b>{_escape(occurrence.label)}</b>")
            primary.set_xalign(0)
            primary.set_ellipsize(Pango.EllipsizeMode.END)

            secondary = Gtk.Label(label=occurrence.detail)
            secondary.set_xalign(0)
            secondary.set_line_wrap(True)
            secondary.set_max_width_chars(30)
            secondary.set_lines(2)

            if occurrence.line is not None:
                location = f"Line {occurrence.line} · {occurrence.kind.replace('-', ' ')}"
            elif occurrence.navigation_kind == "reference":
                location = f"References · {occurrence.kind.replace('-', ' ')}"
            else:
                location = f"Source Notes · {occurrence.kind.replace('-', ' ')}"
            tertiary = Gtk.Label(label=location)
            tertiary.set_xalign(0)
            tertiary.get_style_context().add_class("dim-label")
            tertiary.set_ellipsize(Pango.EllipsizeMode.END)

            box.pack_start(primary, False, False, 0)
            box.pack_start(secondary, False, False, 0)
            box.pack_start(tertiary, False, False, 0)
            row.add(box)
            self._listbox.add(row)
            self._rows[occurrence.id] = row

        self._listbox.show_all()
        self._status.set_text(status)
        self.select_occurrence_id(selected_id)

    def selected_occurrence_id(self) -> str | None:
        row = self._listbox.get_selected_row()
        return getattr(row, "bridge_occurrence_id", None) if row is not None else None

    def select_occurrence_id(self, occurrence_id: str | None) -> bool:
        if occurrence_id is None:
            self._listbox.unselect_all()
            return False
        row = self._rows.get(occurrence_id)
        if row is None:
            return False
        self._listbox.select_row(row)
        return True

    def focus_subject(self) -> None:
        if self._subject_selector.get_sensitive():
            self._subject_selector.grab_focus()
        else:
            self._mode_selector.grab_focus()


def build_authoring_bridge_view(
    on_open,
    on_refresh,
    on_create_source_note,
    on_insert_heading_link,
):
    Gtk = _gtk()

    callbacks = (on_open, on_refresh, on_create_source_note, on_insert_heading_link)
    if any(not callable(callback) for callback in callbacks):
        raise TypeError("Authoring Bridge action callbacks must be callable")

    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    panel.set_margin_start(4)
    panel.set_margin_end(4)
    panel.set_margin_top(4)
    panel.set_margin_bottom(4)

    mode_selector = Gtk.ComboBoxText()
    mode_selector.append("reference", "Backlinks by Reference")
    mode_selector.append("heading", "Backlinks by Heading")
    mode_selector.append("related", "Related References")
    mode_selector.append("issues", "Broken Research Links")
    mode_selector.set_active_id("reference")
    mode_selector.set_hexpand(True)
    panel.pack_start(mode_selector, False, False, 0)

    subject_selector = Gtk.ComboBoxText()
    subject_selector.set_hexpand(True)
    panel.pack_start(subject_selector, False, False, 0)

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

    navigation = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
    open_button = Gtk.Button(label="Open")
    open_button.set_size_request(62, 26)
    open_button.connect("clicked", on_open)
    refresh_button = Gtk.Button(label="Refresh")
    refresh_button.set_size_request(68, 26)
    refresh_button.connect("clicked", on_refresh)
    navigation.pack_start(open_button, True, True, 0)
    navigation.pack_start(refresh_button, True, True, 0)
    panel.pack_start(navigation, False, False, 0)

    authoring = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    source_note_button = Gtk.Button(label="Source Note from Selection…")
    source_note_button.set_size_request(-1, 26)
    source_note_button.connect("clicked", on_create_source_note)
    link_button = Gtk.Button(label="Insert Link to Heading…")
    link_button.set_size_request(-1, 26)
    link_button.connect("clicked", on_insert_heading_link)
    authoring.pack_start(source_note_button, False, False, 0)
    authoring.pack_start(link_button, False, False, 0)
    panel.pack_start(authoring, False, False, 0)

    adapter = AuthoringBridgeViewAdapter(
        panel,
        mode_selector,
        subject_selector,
        listbox,
        status,
    )
    listbox.connect("row-activated", lambda *_: on_open())
    return adapter


def _escape(value: str) -> str:
    GLib = _glib()
    return GLib.markup_escape_text(value or "")
