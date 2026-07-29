"""GTK view for the transient Tags client in the Calamus Research Panel.

The view deliberately uses ``Gtk.ListBox`` rows and keeps rendering free of
viewport operations.  A Tags client can be activated while its ``Gtk.Stack``
child is not mapped yet; row construction is synchronous, while visual
selection is applied only from a cancellable post-map idle callback.  Tags does
not steal focus when activated.
"""
from __future__ import annotations

from typing import Callable

from calamus_tags_controller import TAG_SORT_NAME, TAG_SORT_USAGE
from calamus_tag_integrity import (
    TAG_SCOPE_ALL,
    TAG_SCOPE_REFERENCES,
    TAG_SCOPE_SCRATCHPAD,
    TAG_SCOPE_SOURCE_NOTES,
    TagInventoryItem,
    TagUse,
)


class TagsPanelViewAdapter:
    def __init__(
        self,
        widget,
        search,
        scope,
        sort,
        issues_only,
        tags_list,
        uses_list,
        status,
        uses_status,
    ) -> None:
        self.widget = widget
        self.search = search
        self.scope = scope
        self.sort = sort
        self.issues_only = issues_only
        self.tags_list = tags_list
        self.uses_list = uses_list
        self.status = status
        self.uses_status = uses_status
        self._tag_rows: dict[str, object] = {}
        self._use_rows: list[object] = []
        self._rendering = False
        self._on_tag_selected: Callable[[str | None], None] | None = None
        self._selection_source_id = 0
        self._selection_map_handler_id = 0
        self._pending_tag_identity: str | None = None
        self._pending_use_index: int | None = None
        self._destroyed = False
        self.widget.connect("unmap", self._on_unmap)
        self.widget.connect("destroy", self._on_destroy)

    def bind_controls(
        self,
        on_query: Callable[[str], object],
        on_scope: Callable[[str], object],
        on_sort: Callable[[str], object],
        on_issues: Callable[[bool], object],
        on_tag_selected: Callable[[str | None], object],
    ) -> None:
        if not all(callable(callback) for callback in (
            on_query, on_scope, on_sort, on_issues, on_tag_selected,
        )):
            raise TypeError("Tags panel callbacks must be callable")
        self._on_tag_selected = on_tag_selected
        self.search.connect(
            "search-changed",
            lambda entry: None if self._rendering else on_query(entry.get_text()),
        )
        self.scope.connect(
            "changed",
            lambda combo: None if self._rendering else on_scope(
                combo.get_active_id() or TAG_SCOPE_ALL
            ),
        )
        self.sort.connect(
            "changed",
            lambda combo: None if self._rendering else on_sort(
                combo.get_active_id() or TAG_SORT_NAME
            ),
        )
        self.issues_only.connect(
            "toggled",
            lambda button: None if self._rendering else on_issues(button.get_active()),
        )
        self.tags_list.connect("row-selected", self._selection_changed)

    def render_tags(
        self,
        items: tuple[TagInventoryItem, ...],
        selected_identity: str | None,
        status: str,
    ) -> None:
        """Replace the derived rows without touching scroll adjustments."""
        from gi.repository import Gtk, Pango

        self._rendering = True
        try:
            for child in list(self.tags_list.get_children()):
                self.tags_list.remove(child)
            self._tag_rows = {}
            for item in items:
                row = Gtk.ListBoxRow()
                row.tag_identity = item.identity

                outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                outer.set_margin_top(4)
                outer.set_margin_bottom(4)
                outer.set_margin_start(4)
                outer.set_margin_end(4)

                swatch = Gtk.Label(label="●")
                swatch.set_tooltip_text(f"Derived colour for {item.canonical}")
                try:
                    swatch.set_markup(
                        f'<span foreground="{item.color}">●</span>'
                    )
                except Exception:
                    swatch.set_text("●")
                outer.pack_start(swatch, False, False, 0)

                text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                text.set_hexpand(True)
                primary = Gtk.Label()
                primary.set_markup(f"<b>{_escape(item.canonical)}</b>")
                primary.set_xalign(0)
                primary.set_ellipsize(Pango.EllipsizeMode.END)
                primary.set_width_chars(1)
                primary.set_max_width_chars(30)
                primary.set_tooltip_text(item.canonical)
                details = Gtk.Label(
                    label=(
                        f"{item.total_count} use(s) · "
                        f"R {item.reference_count} · "
                        f"N {item.source_note_count} · "
                        f"S {item.scratchpad_count}"
                    )
                )
                details.set_xalign(0)
                details.get_style_context().add_class("dim-label")
                details.set_ellipsize(Pango.EllipsizeMode.END)
                details.set_width_chars(1)
                details.set_max_width_chars(30)
                text.pack_start(primary, False, False, 0)
                text.pack_start(details, False, False, 0)
                outer.pack_start(text, True, True, 0)

                issue = Gtk.Label(label="⚠" if item.needs_normalization else "")
                issue.set_tooltip_text(
                    "Stored spelling variants need normalization"
                    if item.needs_normalization else ""
                )
                outer.pack_end(issue, False, False, 0)

                row.add(outer)
                self.tags_list.add(row)
                self._tag_rows[item.identity] = row

            self.tags_list.show_all()
            self.tags_list.unselect_all()
            self._pending_tag_identity = (
                selected_identity if selected_identity in self._tag_rows else None
            )
            self.status.set_text(status)
        finally:
            self._rendering = False
        self._queue_selection_sync()

    def render_uses(
        self,
        uses: tuple[TagUse, ...],
        selected_index: int | None,
        status: str,
    ) -> None:
        """Render exact owners as rows; no forced reveal or adjustment access."""
        from gi.repository import Gtk, Pango

        self._rendering = True
        try:
            for child in list(self.uses_list.get_children()):
                self.uses_list.remove(child)
            self._use_rows = []
            for use in uses:
                row = Gtk.ListBoxRow()
                row.tag_use = use
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
                box.set_margin_top(3)
                box.set_margin_bottom(3)
                box.set_margin_start(4)
                box.set_margin_end(4)

                owner = Gtk.Label(label=use.owner_label)
                owner.set_xalign(0)
                owner.set_ellipsize(Pango.EllipsizeMode.END)
                owner.set_width_chars(1)
                owner.set_max_width_chars(30)
                owner.set_tooltip_text(use.owner_label)
                details = Gtk.Label(
                    label=f"{_authority_label(use.authority)} · stored as {use.variant}"
                )
                details.set_xalign(0)
                details.get_style_context().add_class("dim-label")
                details.set_ellipsize(Pango.EllipsizeMode.END)
                details.set_width_chars(1)
                details.set_max_width_chars(30)
                box.pack_start(owner, False, False, 0)
                box.pack_start(details, False, False, 0)
                row.add(box)
                self.uses_list.add(row)
                self._use_rows.append(row)

            self.uses_list.show_all()
            self.uses_list.unselect_all()
            self._pending_use_index = (
                selected_index
                if selected_index is not None and 0 <= selected_index < len(self._use_rows)
                else None
            )
            self.uses_status.set_text(status)
        finally:
            self._rendering = False
        self._queue_selection_sync()

    def selected_tag_identity(self) -> str | None:
        row = self.tags_list.get_selected_row()
        if row is not None:
            return getattr(row, "tag_identity", None)
        return self._pending_tag_identity

    def selected_use(self) -> TagUse | None:
        row = self.uses_list.get_selected_row()
        if row is not None:
            return getattr(row, "tag_use", None)
        index = self._pending_use_index
        if index is not None and 0 <= index < len(self._use_rows):
            return getattr(self._use_rows[index], "tag_use", None)
        return None

    def set_query(self, value: str) -> None:
        text = value if isinstance(value, str) else ""
        if self.search.get_text() != text:
            self._rendering = True
            try:
                self.search.set_text(text)
            finally:
                self._rendering = False

    def set_scope(self, value: str) -> None:
        target = value if value in {
            TAG_SCOPE_ALL, TAG_SCOPE_REFERENCES, TAG_SCOPE_SOURCE_NOTES, TAG_SCOPE_SCRATCHPAD
        } else TAG_SCOPE_ALL
        if self.scope.get_active_id() != target:
            self._rendering = True
            try:
                self.scope.set_active_id(target)
            finally:
                self._rendering = False

    def cancel_deferred_actions(self) -> None:
        if self._selection_source_id:
            from gi.repository import GLib
            try:
                GLib.source_remove(self._selection_source_id)
            except Exception:
                pass
            self._selection_source_id = 0
        if self._selection_map_handler_id:
            try:
                self.widget.disconnect(self._selection_map_handler_id)
            except Exception:
                pass
            self._selection_map_handler_id = 0

    def set_sort(self, value: str) -> None:
        target = value if value in {TAG_SORT_NAME, TAG_SORT_USAGE} else TAG_SORT_NAME
        if self.sort.get_active_id() != target:
            self._rendering = True
            try:
                self.sort.set_active_id(target)
            finally:
                self._rendering = False

    def set_issues_only(self, active: bool) -> None:
        if self.issues_only.get_active() != bool(active):
            self._rendering = True
            try:
                self.issues_only.set_active(bool(active))
            finally:
                self._rendering = False

    def _selection_changed(self, _listbox, row) -> None:
        if self._rendering or self._on_tag_selected is None:
            return
        identity = getattr(row, "tag_identity", None) if row is not None else None
        self._on_tag_selected(identity)

    def _queue_selection_sync(self) -> None:
        if self._destroyed:
            return
        if self.widget.get_mapped():
            self._queue_selection_idle()
        elif not self._selection_map_handler_id:
            self._selection_map_handler_id = self.widget.connect(
                "map", self._on_map_for_selection
            )

    def _on_map_for_selection(self, *_):
        if self._selection_map_handler_id:
            try:
                self.widget.disconnect(self._selection_map_handler_id)
            except Exception:
                pass
            self._selection_map_handler_id = 0
        self._queue_selection_idle()

    def _queue_selection_idle(self) -> None:
        if self._destroyed or self._selection_source_id:
            return
        from gi.repository import GLib
        self._selection_source_id = GLib.idle_add(self._run_deferred_selection)

    def _run_deferred_selection(self) -> bool:
        self._selection_source_id = 0
        if self._destroyed or not self.widget.get_mapped():
            return False
        self._rendering = True
        try:
            tag_row = self._tag_rows.get(self._pending_tag_identity or "")
            if tag_row is None:
                self.tags_list.unselect_all()
            else:
                self.tags_list.select_row(tag_row)
            index = self._pending_use_index
            if index is None or not (0 <= index < len(self._use_rows)):
                self.uses_list.unselect_all()
            else:
                self.uses_list.select_row(self._use_rows[index])
        finally:
            self._rendering = False
        return False

    def _on_unmap(self, *_):
        self.cancel_deferred_actions()

    def _on_destroy(self, *_):
        self._destroyed = True
        self.cancel_deferred_actions()


def build_tags_panel_view(
    on_open,
    on_rename,
    on_remove,
    on_normalize,
    on_refresh,
    on_show_all,
) -> TagsPanelViewAdapter:
    from gi.repository import Gtk

    callbacks = (on_open, on_rename, on_remove, on_normalize, on_refresh, on_show_all)
    if any(not callable(callback) for callback in callbacks):
        raise TypeError("Tags panel action callbacks must be callable")

    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    panel.set_name("tags-panel")
    panel.set_margin_start(4)
    panel.set_margin_end(4)
    panel.set_margin_top(4)
    panel.set_margin_bottom(4)
    panel.set_size_request(-1, -1)
    panel.set_hexpand(True)

    search = Gtk.SearchEntry()
    search.set_name("tags-search")
    search.set_placeholder_text("Search tags or uses")
    search.set_width_chars(1)
    search.set_hexpand(True)
    panel.pack_start(search, False, False, 0)

    show_all_button = Gtk.Button(label="All tags A–Z")
    show_all_button.set_name("tags-show-all-az")
    show_all_button.set_tooltip_text(
        "Clear search and filters, use all authorities, and sort the complete tag list A–Z"
    )
    show_all_button.set_hexpand(True)
    show_all_button.connect("clicked", on_show_all)
    panel.pack_start(show_all_button, False, False, 0)

    # Controls are stacked deliberately. A single horizontal row made its
    # natural width larger than the historical right-panel width and could
    # lock Gtk.Paned after hide/show.
    scope = Gtk.ComboBoxText()
    scope.set_name("tags-scope")
    scope.append(TAG_SCOPE_ALL, "All authorities")
    scope.append(TAG_SCOPE_REFERENCES, "References")
    scope.append(TAG_SCOPE_SOURCE_NOTES, "Source Notes")
    scope.append(TAG_SCOPE_SCRATCHPAD, "Scratchpad")
    scope.set_active_id(TAG_SCOPE_ALL)
    scope.set_hexpand(True)
    panel.pack_start(scope, False, False, 0)

    sort = Gtk.ComboBoxText()
    sort.set_name("tags-sort")
    sort.append(TAG_SORT_NAME, "Name (A–Z)")
    sort.append(TAG_SORT_USAGE, "Most used")
    sort.set_active_id(TAG_SORT_NAME)
    sort.set_hexpand(True)
    panel.pack_start(sort, False, False, 0)

    issues_only = Gtk.CheckButton(label="Variants only")
    issues_only.set_name("tags-issues-only")
    panel.pack_start(issues_only, False, False, 0)

    status = Gtk.Label()
    status.set_name("tags-status")
    status.set_xalign(0)
    status.set_line_wrap(True)
    status.set_width_chars(1)
    status.set_max_width_chars(30)
    panel.pack_start(status, False, False, 0)

    tags_list = Gtk.ListBox()
    tags_list.set_name("tags-list")
    tags_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    tags_list.set_activate_on_single_click(False)
    tags_scroll = Gtk.ScrolledWindow()
    tags_scroll.set_name("tags-scroll")
    tags_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    tags_scroll.set_min_content_width(1)
    tags_scroll.set_propagate_natural_width(False)
    tags_scroll.set_vexpand(True)
    tags_scroll.add(tags_list)
    panel.pack_start(tags_scroll, True, True, 0)

    uses_status = Gtk.Label()
    uses_status.set_name("tag-uses-status")
    uses_status.set_xalign(0)
    uses_status.set_width_chars(1)
    uses_status.set_max_width_chars(30)
    panel.pack_start(uses_status, False, False, 0)

    uses_list = Gtk.ListBox()
    uses_list.set_name("tag-uses-list")
    uses_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    uses_list.set_activate_on_single_click(False)
    uses_scroll = Gtk.ScrolledWindow()
    uses_scroll.set_name("tag-uses-scroll")
    uses_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    uses_scroll.set_min_content_width(1)
    uses_scroll.set_propagate_natural_width(False)
    uses_scroll.set_size_request(-1, 132)
    uses_scroll.add(uses_list)
    panel.pack_start(uses_scroll, False, True, 0)

    # Full-width actions keep the natural width bounded at narrow panel sizes.
    actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
    open_button = Gtk.Button(label="Open")
    open_button.set_name("tags-open")
    rename_button = Gtk.Button(label="Rename / Merge…")
    rename_button.set_name("tags-rename")
    refresh_button = Gtk.Button(label="Refresh")
    refresh_button.set_name("tags-refresh")
    remove_button = Gtk.Button(label="Remove…")
    remove_button.set_name("tags-remove")
    normalize_button = Gtk.Button(label="Normalize All…")
    normalize_button.set_name("tags-normalize")
    for button, callback in (
        (open_button, on_open),
        (rename_button, on_rename),
        (refresh_button, on_refresh),
        (remove_button, on_remove),
        (normalize_button, on_normalize),
    ):
        button.set_hexpand(True)
        button.connect("clicked", callback)
        actions.pack_start(button, False, False, 0)
    panel.pack_start(actions, False, False, 0)

    uses_list.connect("row-activated", lambda *_: on_open())

    return TagsPanelViewAdapter(
        panel,
        search,
        scope,
        sort,
        issues_only,
        tags_list,
        uses_list,
        status,
        uses_status,
    )


def _authority_label(authority: str) -> str:
    return {
        TAG_SCOPE_REFERENCES: "Reference",
        TAG_SCOPE_SOURCE_NOTES: "Source Note",
        TAG_SCOPE_SCRATCHPAD: "Scratchpad",
    }.get(authority, authority)


def _escape(value: str) -> str:
    from gi.repository import GLib
    return GLib.markup_escape_text(value or "")
