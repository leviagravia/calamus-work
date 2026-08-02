"""GTK Bibliography Manager panel backed by the canonical References controller."""
from __future__ import annotations

from typing import Any, Callable

from calamus_bibliography import BibliographyContext, format_reference_detail
from calamus_bibliography_search import (
    DEFAULT_BIBLIOGRAPHY_SEARCH_DELAY_MS,
    CoalescedQueryDispatcher,
)
from calamus_references import ReferenceRecord


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


class ReferencePanelViewAdapter:
    def __init__(
        self,
        widget: Any,
        search: Any,
        listbox: Any,
        status: Any,
        detail: Any,
        filters: dict[str, Any],
    ) -> None:
        self.widget = widget
        self.search = search
        self._listbox = listbox
        self._status = status
        self._detail = detail
        self._filters = filters
        self._rows: dict[str, Any] = {}
        self._filter_guard = False
        self._render_guard = False
        self._selection_callback: Callable[[], None] | None = None
        self._selection_handler_id: int | None = None
        self._search_dispatcher: CoalescedQueryDispatcher | None = None
        self._search_handler_id: int | None = None
        self._search_suppressed = False

    def bind_search(
        self, callback: Callable[[str], None],
        *, delay_ms: int = DEFAULT_BIBLIOGRAPHY_SEARCH_DELAY_MS,
    ) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        if self._search_handler_id is not None:
            raise RuntimeError("search callback is already bound")
        GLib = _glib()
        self._search_dispatcher = CoalescedQueryDispatcher(
            delay_ms=delay_ms,
            schedule=lambda delay, function: GLib.timeout_add(delay, function),
            cancel=lambda source_id: GLib.source_remove(source_id),
            deliver=callback,
        )

        def changed(entry):
            if self._search_suppressed:
                return
            self._search_dispatcher.submit(entry.get_text())

        self._search_handler_id = self.search.connect("changed", changed)
        if hasattr(self.widget, "connect"):
            self.widget.connect("destroy", lambda *_: self.dispose())

    @property
    def search_pending(self) -> bool:
        return bool(self._search_dispatcher and self._search_dispatcher.pending)

    @property
    def search_delivery_count(self) -> int:
        return self._search_dispatcher.delivery_count if self._search_dispatcher else 0

    @property
    def last_delivered_query(self) -> str:
        return self._search_dispatcher.last_delivered_query if self._search_dispatcher else ""

    def clear_search(self) -> None:
        self._search_suppressed = True
        try:
            if self._search_dispatcher is not None:
                self._search_dispatcher.cancel_pending()
            if self.search.get_text():
                self.search.set_text("")
        finally:
            self._search_suppressed = False

    def dispose(self) -> None:
        if self._search_dispatcher is not None:
            self._search_dispatcher.dispose()
            self._search_dispatcher = None

    def bind_filter(self, name: str, callback: Callable[[str], None]) -> None:
        combo = self._filters[name]
        def changed(widget):
            if self._filter_guard:
                return
            value = widget.get_active_id() or "all"
            callback(value)
        combo.connect("changed", changed)

    def bind_selection(self, callback: Callable[[], None]) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        if self._selection_handler_id is not None:
            raise RuntimeError("selection callback is already bound")
        self._selection_callback = callback
        self._selection_handler_id = self._listbox.connect(
            "row-selected", self._on_row_selected
        )

    def _on_row_selected(self, *_args) -> None:
        # Rendering replaces ListBoxRow objects. Gtk emits row-selected(None)
        # while the selected row is being unparented and emits again when the
        # replacement selection is installed. Never let those lifecycle
        # emissions re-enter the controller with a destroyed/partial row tree.
        if self._render_guard or self._selection_callback is None:
            return
        self._selection_callback()

    def set_filter_options(self, types: tuple[str, ...], tags: tuple[str, ...]) -> None:
        self._filter_guard = True
        try:
            for name, values in (("reference_type", types), ("tag", tags)):
                combo = self._filters[name]
                active = combo.get_active_id() or "all"
                combo.remove_all()
                combo.append("all", "All types" if name == "reference_type" else "All tags")
                for value in values:
                    combo.append(value, value)
                combo.set_active_id(active if active in {"all", *values} else "all")
        finally:
            self._filter_guard = False

    def render(self, records: tuple[ReferenceRecord, ...], selected_key: str | None, status: str) -> None:
        Gtk, Pango = _gtk_pango()
        if self._render_guard:
            raise RuntimeError("bibliography rows cannot be rendered re-entrantly")

        # Construct the complete replacement generation before touching the
        # currently visible/selected rows. A widget-construction failure leaves
        # the previous stable list intact instead of exposing a partial tree.
        replacement: list[tuple[str, Any]] = []
        for record in records:
            row = Gtk.ListBoxRow()
            row.reference_key = record.key
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            box.set_margin_start(4)
            box.set_margin_end(4)
            primary = Gtk.Label()
            primary.set_markup(f"<b>{_escape(record.author_year)}</b>")
            primary.set_xalign(0)
            primary.set_ellipsize(Pango.EllipsizeMode.END)
            secondary = Gtk.Label(label=record.title)
            secondary.set_xalign(0)
            secondary.set_ellipsize(Pango.EllipsizeMode.END)
            tertiary = Gtk.Label(label=f"{record.type}  ·  {record.key}")
            tertiary.set_xalign(0)
            tertiary.get_style_context().add_class("dim-label")
            tertiary.set_ellipsize(Pango.EllipsizeMode.END)
            box.pack_start(primary, False, False, 0)
            box.pack_start(secondary, False, False, 0)
            box.pack_start(tertiary, False, False, 0)
            row.add(box)
            replacement.append((record.key, row))

        self._render_guard = True
        handler = self._selection_handler_id
        if handler is not None and hasattr(self._listbox, "handler_block"):
            self._listbox.handler_block(handler)
        try:
            # Swap the complete row generation while semantic selection
            # callbacks are suspended. No controller callback may observe a
            # removed row, a partial list, or an old-generation selection.
            for child in list(self._listbox.get_children()):
                self._listbox.remove(child)
            rows: dict[str, Any] = {}
            for key, row in replacement:
                self._listbox.add(row)
                rows[key] = row
            self._rows = rows
            self._listbox.show_all()
            self._status.set_text(status)
            self.select_key(selected_key)
        finally:
            if handler is not None and hasattr(self._listbox, "handler_unblock"):
                self._listbox.handler_unblock(handler)
            self._render_guard = False

    def render_detail(self, record: ReferenceRecord | None, context: BibliographyContext) -> None:
        buffer = self._detail.get_buffer()
        buffer.set_text(format_reference_detail(record, context) if record is not None else "No reference selected.")

    def selected_key(self) -> str | None:
        row = self._listbox.get_selected_row()
        return getattr(row, "reference_key", None) if row is not None else None

    def select_key(self, key: str | None) -> bool:
        if key is None:
            self._listbox.unselect_all()
            return False
        row = self._rows.get(key)
        if row is None:
            return False
        self._listbox.select_row(row)
        return True

    def focus_search(self) -> None:
        self.search.grab_focus()


def _combo(items: tuple[tuple[str, str], ...]):
    Gtk = _gtk()
    combo = Gtk.ComboBoxText()
    for identity, label in items:
        combo.append(identity, label)
    combo.set_active(0)
    return combo


def build_reference_panel_view(
    on_add, on_edit, on_duplicate, on_delete, on_copy_key, on_quick_cite,
    on_show_uses, on_open_file, on_reveal_file, on_related, on_refresh,
):
    Gtk = _gtk()
    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    panel.set_name("bibliography-panel")
    panel.set_margin_start(4)
    panel.set_margin_end(4)
    panel.set_margin_top(4)
    panel.set_margin_bottom(4)

    title = Gtk.Label()
    title.set_markup("<b>Bibliography</b>")
    title.set_xalign(0)
    panel.pack_start(title, False, False, 0)

    search = Gtk.SearchEntry()
    search.set_name("bibliography-search")
    search.set_placeholder_text("Search all bibliography fields…")
    panel.pack_start(search, False, False, 0)

    filters = {
        "reference_type": _combo((("all", "All types"),)),
        "tag": _combo((("all", "All tags"),)),
        "use": _combo((("all", "All uses"), ("cited", "Cited"), ("source-notes", "Source Notes"), ("unused", "Unused"))),
        "file": _combo((("all", "All files"), ("present", "File available"), ("missing", "File missing"), ("unset", "No file"))),
        "integrity": _combo((("all", "All integrity"), ("error", "Errors"), ("warning", "Warnings"), ("advisory", "Advisories"), ("clean", "Clean"))),
        "sort": _combo((("author-year-title", "Author / year"), ("title", "Title"), ("year", "Year"), ("key", "Key"), ("type", "Type"))),
    }
    for name, widget in filters.items():
        widget.set_name(f"bibliography-{name.replace('_', '-')}")
    grid = Gtk.Grid(column_spacing=4, row_spacing=4)
    grid.attach(filters["reference_type"], 0, 0, 1, 1)
    grid.attach(filters["tag"], 1, 0, 1, 1)
    grid.attach(filters["use"], 0, 1, 1, 1)
    grid.attach(filters["file"], 1, 1, 1, 1)
    grid.attach(filters["integrity"], 0, 2, 1, 1)
    grid.attach(filters["sort"], 1, 2, 1, 1)
    panel.pack_start(grid, False, False, 0)

    status = Gtk.Label()
    status.set_xalign(0)
    panel.pack_start(status, False, False, 0)

    listbox = Gtk.ListBox()
    listbox.set_name("bibliography-list")
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    list_scroll = Gtk.ScrolledWindow()
    list_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    list_scroll.add(listbox)

    detail = Gtk.TextView()
    detail.set_name("bibliography-detail")
    detail.set_editable(False)
    detail.set_cursor_visible(False)
    detail.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    detail.set_left_margin(5)
    detail.set_right_margin(5)
    detail_scroll = Gtk.ScrolledWindow()
    detail_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    detail_scroll.add(detail)

    split = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
    split.pack1(list_scroll, resize=True, shrink=False)
    split.pack2(detail_scroll, resize=True, shrink=False)
    split.set_position(260)
    panel.pack_start(split, True, True, 0)

    def row(buttons):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        for label, callback in buttons:
            button = Gtk.Button(label=label)
            button.set_name("bibliography-" + label.casefold().replace(" ", "-").replace("…", "").replace(".", ""))
            button.set_size_request(-1, 26)
            button.connect("clicked", callback)
            box.pack_start(button, True, True, 0)
        panel.pack_start(box, False, False, 0)

    row((("New", on_add), ("Edit", on_edit), ("Duplicate", on_duplicate), ("Delete", on_delete)))
    row((("Quick Cite", on_quick_cite), ("Copy Key", on_copy_key), ("Show Uses", on_show_uses)))
    row((("Open File", on_open_file), ("Reveal", on_reveal_file), ("Related References…", on_related), ("Refresh", on_refresh)))

    adapter = ReferencePanelViewAdapter(panel, search, listbox, status, detail, filters)
    listbox.connect("row-activated", lambda *_: on_edit())
    return adapter


def _escape(value: str) -> str:
    GLib = _glib()
    return GLib.markup_escape_text(value or "")
