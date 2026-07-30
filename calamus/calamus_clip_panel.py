"""GTK boundary for the W95 Clip Collection client."""
from __future__ import annotations

from typing import Any, Callable

from calamus_clip_search import clip_preview


class ClipCollectionViewAdapter:
    """Own list/detail widgets while exposing only stable IDs to the controller."""

    def __init__(
        self,
        panel: Any,
        listbox: Any,
        *,
        search_entry: Any = None,
        status_label: Any = None,
        detail_buffer: Any = None,
        action_widgets: tuple[Any, ...] = (),
        double_click_type: Any = None,
        on_activate: Callable[[], None] | None = None,
        on_selection_changed: Callable[[str | None], None] | None = None,
    ) -> None:
        if panel is None or listbox is None:
            raise TypeError("panel and listbox are required")
        if on_activate is not None and not callable(on_activate):
            raise TypeError("on_activate must be callable")
        self._panel = panel
        self._listbox = listbox
        self._search_entry = search_entry
        self._status_label = status_label
        self._detail_buffer = detail_buffer
        self._action_widgets = tuple(action_widgets)
        self._double_click_type = double_click_type
        self._on_activate = on_activate or (lambda: None)
        self._on_selection_changed = on_selection_changed
        self._rows_by_id: dict[str, Any] = {}
        self._clips_by_id: dict[str, dict[str, Any]] = {}

    @property
    def widget(self) -> Any:
        return self._panel

    def render(self, clips: list[dict[str, Any]], *, total: int, query: str) -> None:
        from gi.repository import Gtk, Pango

        for child in list(self._listbox.get_children()):
            self._listbox.remove(child)
        self._rows_by_id.clear()
        self._clips_by_id = {
            item.get("id", ""): dict(item)
            for item in clips
            if isinstance(item.get("id"), str) and item.get("id")
        }
        for position, clip in enumerate(clips, start=1):
            clip_id = clip.get("id", "")
            row = Gtk.ListBoxRow()
            row._calamus_clip_id = clip_id
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            box.set_margin_top(4)
            box.set_margin_bottom(4)
            box.set_margin_start(4)
            box.set_margin_end(4)

            shortcut = clip.get("shortcut", "") or "—"
            title = clip.get("title", "Clip")
            heading = Gtk.Label(label=f"[{shortcut}]  {title}")
            heading.set_xalign(0)
            heading.set_ellipsize(Pango.EllipsizeMode.END)
            heading.set_max_width_chars(36)
            box.pack_start(heading, False, False, 0)

            preview = Gtk.Label(label=clip_preview(clip.get("text", ""), 110))
            preview.set_xalign(0)
            preview.set_ellipsize(Pango.EllipsizeMode.END)
            preview.set_max_width_chars(42)
            preview.get_style_context().add_class("dim-label")
            box.pack_start(preview, False, False, 0)

            row.add(box)
            self._listbox.add(row)
            self._rows_by_id[clip_id] = row

        if self._status_label is not None:
            if query:
                self._status_label.set_text(f"{len(clips)} of {total} clips")
            else:
                self._status_label.set_text(f"{total} clips")
        self._listbox.show_all()
        self._sync_detail_and_actions()

    def selected_id(self) -> str | None:
        row = self._listbox.get_selected_row()
        clip_id = getattr(row, "_calamus_clip_id", None) if row is not None else None
        return clip_id if isinstance(clip_id, str) and clip_id else None

    def select_id(self, clip_id: str) -> bool:
        row = self._rows_by_id.get(clip_id)
        if row is None:
            return False
        self._listbox.select_row(row)
        self._sync_detail_and_actions()
        return True

    # Compatibility helpers retained for existing tests and numeric wiring.
    def selected_index(self) -> int | None:
        row = self._listbox.get_selected_row()
        return row.get_index() if row is not None else None

    def select_index(self, index: int) -> bool:
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            return False
        row = self._listbox.get_row_at_index(index)
        if row is None:
            return False
        self._listbox.select_row(row)
        self._sync_detail_and_actions()
        return True

    def focus_search(self) -> None:
        if self._search_entry is not None:
            self._search_entry.grab_focus()
            if hasattr(self._search_entry, "select_region"):
                self._search_entry.select_region(0, -1)

    def on_row_selected(self, *_args) -> None:
        self._sync_detail_and_actions()

    def on_button_press(self, listbox: Any, event: Any) -> bool:
        if self._double_click_type is None:
            return False
        if event.type != self._double_click_type or getattr(event, "button", 0) != 1:
            return False
        row = listbox.get_row_at_y(int(event.y))
        if row is None:
            return False
        listbox.select_row(row)
        self._sync_detail_and_actions()
        self._on_activate()
        return True

    def _sync_detail_and_actions(self) -> None:
        clip_id = self.selected_id()
        selected = self._clips_by_id.get(clip_id or "")
        if self._detail_buffer is not None:
            self._detail_buffer.set_text(selected.get("text", "") if selected else "")
        for widget in self._action_widgets:
            widget.set_sensitive(selected is not None)
        if self._on_selection_changed is not None:
            self._on_selection_changed(clip_id)


def build_clip_collection_view(
    *,
    on_search,
    on_new,
    on_capture,
    on_insert,
    on_copy,
    on_edit,
    on_duplicate,
    on_delete,
    on_refresh,
    on_open_file,
    on_activate,
    show_title: bool = True,
):
    from gi.repository import Gdk, Gtk, Pango

    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    panel.set_hexpand(True)
    panel.set_vexpand(True)
    panel.set_margin_start(3)
    panel.set_margin_end(3)
    panel.set_margin_top(3)
    panel.set_margin_bottom(3)

    if show_title:
        title = Gtk.Label(label="Clip Collection")
        title.set_name("calamus-clip-title")
        title.set_xalign(0)
        title.set_ellipsize(Pango.EllipsizeMode.END)
        panel.pack_start(title, False, False, 0)

    search = Gtk.SearchEntry()
    search.set_placeholder_text("Search shortcut, title or body")
    search.set_hexpand(True)
    panel.pack_start(search, False, False, 0)

    status = Gtk.Label(label="0 clips")
    status.set_xalign(0)
    status.get_style_context().add_class("dim-label")
    panel.pack_start(status, False, False, 0)

    clip_list = Gtk.ListBox()
    clip_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
    clip_list.set_activate_on_single_click(False)
    clip_list.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    list_scroll = Gtk.ScrolledWindow()
    list_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    list_scroll.set_hexpand(True)
    list_scroll.set_vexpand(True)
    if hasattr(list_scroll, "set_propagate_natural_width"):
        list_scroll.set_propagate_natural_width(False)
    list_scroll.add(clip_list)
    panel.pack_start(list_scroll, True, True, 0)

    detail = Gtk.TextView()
    detail.set_editable(False)
    detail.set_cursor_visible(False)
    detail.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    detail.set_left_margin(5)
    detail.set_right_margin(5)
    detail_scroll = Gtk.ScrolledWindow()
    detail_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    detail_scroll.set_size_request(-1, 96)
    detail_scroll.set_hexpand(True)
    detail_scroll.add(detail)
    panel.pack_start(detail_scroll, False, True, 0)

    def full_button(label, callback):
        button = Gtk.Button(label=label)
        button.set_hexpand(True)
        button.connect("clicked", callback)
        panel.pack_start(button, False, False, 0)
        return button

    new_button = full_button("New", on_new)
    capture_button = full_button("Capture Selection", on_capture)
    insert_button = full_button("Insert", on_insert)
    copy_button = full_button("Copy Body", on_copy)

    manage = Gtk.MenuButton(label="Manage")
    manage.set_hexpand(True)
    menu = Gtk.Menu()
    manage_items = []
    for label, callback in (
        ("Edit", on_edit),
        ("Duplicate", on_duplicate),
        ("Delete", on_delete),
        ("Refresh", on_refresh),
        ("Open Clip File", on_open_file),
    ):
        item = Gtk.MenuItem(label=label)
        item.connect("activate", callback)
        menu.append(item)
        manage_items.append(item)
    menu.show_all()
    manage.set_popup(menu)
    panel.pack_start(manage, False, False, 0)

    selected_actions = (insert_button, copy_button, manage_items[0], manage_items[1], manage_items[2])
    adapter = ClipCollectionViewAdapter(
        panel,
        clip_list,
        search_entry=search,
        status_label=status,
        detail_buffer=detail.get_buffer(),
        action_widgets=selected_actions,
        double_click_type=Gdk.EventType._2BUTTON_PRESS,
        on_activate=on_activate,
    )
    search.connect("search-changed", lambda entry: on_search(entry.get_text()))
    clip_list.connect("row-selected", adapter.on_row_selected)
    clip_list.connect("row-activated", lambda *_args: on_activate())
    clip_list.connect("button-press-event", adapter.on_button_press)
    panel.show_all()
    adapter._sync_detail_and_actions()
    return adapter
