"""GTK-only projection for Calamus W96 Document Overview Core.

The module is importable without PyGObject.  GTK is loaded only by the builder,
keeping tests and source provenance usable in headless environments.
"""
from __future__ import annotations

from typing import Any, Callable

from calamus_document_overview_model import (
    DOCUMENT_OVERVIEW_CATEGORIES,
    DocumentOverviewRow,
)



def _gtk_pango():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Pango", "1.0")
    from gi.repository import Gtk, Pango
    return Gtk, Pango


class DocumentOverviewViewAdapter:
    def __init__(
        self,
        window,
        document_label,
        state_label,
        category_list,
        item_list,
        item_heading,
        detail_title,
        detail_body,
        status,
        refresh_button,
        primary_button,
        secondary_button,
    ) -> None:
        self.window = window
        self.document_label = document_label
        self.state_label = state_label
        self.category_list = category_list
        self.item_list = item_list
        self.item_heading = item_heading
        self.detail_title = detail_title
        self.detail_body = detail_body
        self.status = status
        self.refresh_button = refresh_button
        self.primary_button = primary_button
        self.secondary_button = secondary_button
        self._category_rows: dict[str, Any] = {}
        self._category_labels: dict[str, Any] = {}
        self._item_rows: dict[str, Any] = {}
        self._rendering = False
        self._callbacks_bound = False

    def bind(
        self,
        *,
        on_category: Callable[[str], object],
        on_item: Callable[[str | None], object],
        on_refresh: Callable[[], object],
        on_primary: Callable[[], object],
        on_secondary: Callable[[], object],
    ) -> None:
        callbacks = (on_category, on_item, on_refresh, on_primary, on_secondary)
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("Document Overview callbacks must be callable")
        if self._callbacks_bound:
            raise RuntimeError("Document Overview callbacks are already bound")
        self._callbacks_bound = True
        self.category_list.connect(
            "row-selected",
            lambda _box, row: None
            if self._rendering or row is None
            else on_category(getattr(row, "overview_category", "overview")),
        )
        self.item_list.connect(
            "row-selected",
            lambda _box, row: None
            if self._rendering
            else on_item(getattr(row, "overview_item_id", None) if row is not None else None),
        )
        self.refresh_button.connect("clicked", lambda *_: on_refresh())
        self.primary_button.connect("clicked", lambda *_: on_primary())
        self.secondary_button.connect("clicked", lambda *_: on_secondary())

    def render_header(self, *, name: str, path: str, modified: bool, refreshed_at: str, stale: bool) -> None:
        self.document_label.set_text(name)
        self.document_label.set_tooltip_text(path or "Untitled document")
        parts = ["modified" if modified else "saved"]
        if not path:
            parts.append("untitled")
        if stale:
            parts.append("refresh required")
        elif refreshed_at:
            parts.append(f"refreshed {refreshed_at}")
        self.state_label.set_text(" · ".join(parts))
        self.status.set_text(
            "Document changed. Overview is stale; no refresh has run yet."
            if stale
            else "Read-only projection of the current document."
        )

    def render_categories(self, selected_id: str, counts: dict[str, int]) -> None:
        """Update the persistent category selector without replacing event targets.

        Category rows are structural navigation widgets, not snapshot data.  They
        are created once for the lifetime of this view and only their labels and
        selection are updated.  Replacing the selected GtkListBoxRow from inside
        its synchronous ``row-selected`` callback leaves GTK processing a native
        pointer event against a destroyed row and can produce use-after-destroy
        criticals or a segmentation fault.
        """
        Gtk, _Pango = _gtk_pango()
        self._rendering = True
        try:
            if not self._category_rows:
                for category_id, label in DOCUMENT_OVERVIEW_CATEGORIES:
                    row = Gtk.ListBoxRow()
                    row.overview_category = category_id
                    item = Gtk.Label(label=label)
                    item.set_xalign(0)
                    item.set_margin_start(8)
                    item.set_margin_end(8)
                    item.set_margin_top(7)
                    item.set_margin_bottom(7)
                    row.add(item)
                    self.category_list.add(row)
                    self._category_rows[category_id] = row
                    self._category_labels[category_id] = item
                self.category_list.show_all()

            for category_id, label in DOCUMENT_OVERVIEW_CATEGORIES:
                count = max(0, int(counts.get(category_id, 0)))
                text = f"{label}  ({count})" if category_id != "overview" else label
                self._category_labels[category_id].set_text(text)

            self.category_list.select_row(self._category_rows.get(selected_id))
        finally:
            self._rendering = False

    def render_items(self, heading: str, rows: tuple[DocumentOverviewRow, ...], selected_id: str | None) -> None:
        Gtk, Pango = _gtk_pango()
        self.item_heading.set_text(heading)
        self._rendering = True
        try:
            for child in list(self.item_list.get_children()):
                self.item_list.remove(child)
            self._item_rows = {}
            for item in rows:
                row = Gtk.ListBoxRow()
                row.overview_item_id = item.id
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                box.set_margin_start(7)
                box.set_margin_end(7)
                box.set_margin_top(5)
                box.set_margin_bottom(5)
                title = Gtk.Label(label=item.title)
                title.set_xalign(0)
                title.set_ellipsize(Pango.EllipsizeMode.END)
                title.set_tooltip_text(item.title)
                subtitle = Gtk.Label(label=item.subtitle)
                subtitle.set_xalign(0)
                subtitle.set_ellipsize(Pango.EllipsizeMode.END)
                subtitle.get_style_context().add_class("dim-label")
                box.pack_start(title, False, False, 0)
                if item.subtitle:
                    box.pack_start(subtitle, False, False, 0)
                row.add(box)
                self.item_list.add(row)
                self._item_rows[item.id] = row
            self.item_list.show_all()
            row = self._item_rows.get(selected_id or "")
            if row is not None:
                self.item_list.select_row(row)
            else:
                self.item_list.unselect_all()
        finally:
            self._rendering = False

    def render_detail(
        self,
        *,
        title: str,
        body: str,
        primary_label: str = "",
        secondary_label: str = "",
        enabled: bool = True,
    ) -> None:
        self.detail_title.set_text(title)
        self.detail_body.set_text(body)
        self.primary_button.set_label(primary_label or "Action")
        self.primary_button.set_visible(bool(primary_label))
        self.primary_button.set_sensitive(bool(primary_label) and enabled)
        self.secondary_button.set_label(secondary_label or "Action")
        self.secondary_button.set_visible(bool(secondary_label))
        self.secondary_button.set_sensitive(bool(secondary_label) and enabled)

    def set_stale(self, stale: bool) -> None:
        if stale:
            self.status.set_text(
                "Document changed. Overview is stale; no refresh has run yet."
            )

    def present(self) -> None:
        self.window.show_all()
        self.window.present()

    def hide(self) -> None:
        """Relinquish the foreground to the editor without closing the dossier."""
        self.window.hide()

    def destroy(self) -> None:
        self.window.destroy()


def build_document_overview_view(parent) -> DocumentOverviewViewAdapter:
    Gtk, Pango = _gtk_pango()

    window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    window.set_name("document-overview-window")
    window.set_title("Document Overview")
    window.set_default_size(980, 700)
    window.set_resizable(True)
    window.set_transient_for(parent)
    window.set_destroy_with_parent(True)
    window.set_modal(False)

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    root.set_margin_start(10)
    root.set_margin_end(10)
    root.set_margin_top(10)
    root.set_margin_bottom(10)
    window.add(root)

    header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    document_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    document_box.set_hexpand(True)
    document_label = Gtk.Label()
    document_label.set_name("document-overview-document")
    document_label.set_xalign(0)
    document_label.set_ellipsize(Pango.EllipsizeMode.END)
    state_label = Gtk.Label()
    state_label.set_name("document-overview-state")
    state_label.set_xalign(0)
    state_label.get_style_context().add_class("dim-label")
    document_box.pack_start(document_label, False, False, 0)
    document_box.pack_start(state_label, False, False, 0)
    header.pack_start(document_box, True, True, 0)
    refresh_button = Gtk.Button(label="Refresh")
    refresh_button.set_name("document-overview-refresh")
    close_button = Gtk.Button(label="Close")
    close_button.set_name("document-overview-close")
    close_button.connect("clicked", lambda *_: window.destroy())
    header.pack_end(close_button, False, False, 0)
    header.pack_end(refresh_button, False, False, 0)
    root.pack_start(header, False, False, 0)

    main = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
    main.set_wide_handle(True)
    main.set_position(210)
    main.set_hexpand(True)
    main.set_vexpand(True)
    root.pack_start(main, True, True, 0)

    category_list = Gtk.ListBox()
    category_list.set_name("document-overview-categories")
    category_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    category_scroll = Gtk.ScrolledWindow()
    category_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    category_scroll.set_size_request(185, -1)
    category_scroll.add(category_list)
    main.pack1(category_scroll, resize=False, shrink=False)

    right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    right.set_hexpand(True)
    right.set_vexpand(True)
    main.pack2(right, resize=True, shrink=True)

    item_heading = Gtk.Label()
    item_heading.set_name("document-overview-item-heading")
    item_heading.set_xalign(0)
    right.pack_start(item_heading, False, False, 0)

    item_list = Gtk.ListBox()
    item_list.set_name("document-overview-items")
    item_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    item_scroll = Gtk.ScrolledWindow()
    item_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    item_scroll.set_vexpand(True)
    item_scroll.add(item_list)
    right.pack_start(item_scroll, True, True, 0)

    detail_frame = Gtk.Frame(label="Details")
    detail_frame.set_name("document-overview-detail")
    detail_frame.set_size_request(-1, 170)
    detail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    detail_box.set_margin_start(8)
    detail_box.set_margin_end(8)
    detail_box.set_margin_top(8)
    detail_box.set_margin_bottom(8)
    detail_title = Gtk.Label()
    detail_title.set_xalign(0)
    detail_title.set_ellipsize(Pango.EllipsizeMode.END)
    detail_body = Gtk.Label()
    detail_body.set_xalign(0)
    detail_body.set_yalign(0)
    detail_body.set_line_wrap(True)
    detail_body.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    detail_body.set_selectable(True)
    detail_scroll = Gtk.ScrolledWindow()
    detail_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    detail_scroll.add_with_viewport(detail_body)
    detail_box.pack_start(detail_title, False, False, 0)
    detail_box.pack_start(detail_scroll, True, True, 0)
    actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    primary_button = Gtk.Button(label="Action")
    primary_button.set_name("document-overview-primary-action")
    primary_button.set_no_show_all(True)
    secondary_button = Gtk.Button(label="Action")
    secondary_button.set_name("document-overview-secondary-action")
    secondary_button.set_no_show_all(True)
    actions.pack_start(primary_button, False, False, 0)
    actions.pack_start(secondary_button, False, False, 0)
    detail_box.pack_start(actions, False, False, 0)
    detail_frame.add(detail_box)
    right.pack_start(detail_frame, False, True, 0)

    status = Gtk.Label()
    status.set_name("document-overview-status")
    status.set_xalign(0)
    status.set_ellipsize(Pango.EllipsizeMode.END)
    root.pack_start(status, False, False, 0)

    return DocumentOverviewViewAdapter(
        window,
        document_label,
        state_label,
        category_list,
        item_list,
        item_heading,
        detail_title,
        detail_body,
        status,
        refresh_button,
        primary_button,
        secondary_button,
    )
