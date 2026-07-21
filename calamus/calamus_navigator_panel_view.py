"""GTK view adapter for the Calamus document Navigator."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from calamus_document_structure import DocumentHeading
from calamus_navigator_panel import NavigatorPanelPresenter


class NavigatorPanelViewAdapter:
    """Render headings and delegate every decision to the W70 controller."""

    def __init__(self, controller, on_hide) -> None:
        if not callable(on_hide):
            raise TypeError("on_hide must be callable")
        self._on_hide = on_hide
        self._syncing_selection = False
        self._refresh_source = None
        self._cursor_source = None

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.widget.set_margin_start(6)
        self.widget.set_margin_end(6)
        self.widget.set_margin_top(6)
        self.widget.set_margin_bottom(6)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title = Gtk.Label()
        title.set_markup("<b>Navigator</b>")
        title.set_xalign(0)
        title.set_hexpand(True)
        header.pack_start(title, True, True, 0)

        close_button = Gtk.Button()
        close_button.set_name("navigator-close-button")
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_size_request(26, 26)
        close_button.set_valign(Gtk.Align.CENTER)
        self._close_button_css = Gtk.CssProvider()
        self._close_button_css.load_from_data(
            b"#navigator-close-button { min-width: 24px; min-height: 24px; padding: 0px; }"
        )
        close_button.get_style_context().add_provider(
            self._close_button_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        close_button.set_tooltip_text("Hide Navigator")
        close_button.add(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
        close_button.connect("clicked", lambda *_: self._on_hide())
        try:
            close_button.get_accessible().set_name("Hide Navigator")
        except Exception:
            pass
        header.pack_end(close_button, False, False, 0)
        self.widget.pack_start(header, False, False, 0)

        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Filter headings…")
        self.widget.pack_start(self.search, False, False, 0)

        self.status = Gtk.Label()
        self.status.set_xalign(0)
        self.widget.pack_start(self.status, False, False, 0)

        self.store = Gtk.ListStore(str, int, object)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.set_headers_visible(True)
        self.tree.set_enable_search(False)
        self.selection = self.tree.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.SINGLE)

        title_renderer = Gtk.CellRendererText()
        self.tree.append_column(Gtk.TreeViewColumn("Section", title_renderer, text=0))
        line_renderer = Gtk.CellRendererText()
        line_renderer.set_property("xalign", 1.0)
        self.tree.append_column(Gtk.TreeViewColumn("Line", line_renderer, text=1))

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.tree)
        self.widget.pack_start(scroll, True, True, 0)

        self.presenter = NavigatorPanelPresenter(controller, self)
        self.search.connect("search-changed", self._on_filter_changed)
        self.search.connect("activate", self._on_filter_activated)
        self.selection.connect("changed", self._on_selection_changed)

    def is_attached(self) -> bool:
        return self.widget.get_parent() is not None

    def focus_filter(self) -> None:
        self.search.grab_focus()

    def cancel_pending(self) -> None:
        for attribute in ("_refresh_source", "_cursor_source"):
            source = getattr(self, attribute)
            if source:
                try:
                    GLib.source_remove(source)
                except Exception:
                    pass
                setattr(self, attribute, None)

    def invalidate(self) -> None:
        if self.is_attached():
            self.schedule_refresh()

    def schedule_refresh(self, delay_ms: int = 180) -> None:
        if not self.is_attached():
            return
        if self._refresh_source:
            try:
                GLib.source_remove(self._refresh_source)
            except Exception:
                pass
        self._refresh_source = GLib.timeout_add(delay_ms, self._run_refresh)

    def _run_refresh(self) -> bool:
        self._refresh_source = None
        self.refresh()
        return False

    def refresh(self) -> tuple[DocumentHeading, ...]:
        headings = self.presenter.refresh(self.search.get_text())
        return headings

    def schedule_cursor_sync(self) -> None:
        if not self.is_attached():
            return
        if self._cursor_source:
            return
        self._cursor_source = GLib.idle_add(self._run_cursor_sync)

    def _run_cursor_sync(self) -> bool:
        self._cursor_source = None
        if self.is_attached():
            self.presenter.sync_cursor()
        return False

    def render(
        self,
        headings: tuple[DocumentHeading, ...],
        current: DocumentHeading | None,
    ) -> None:
        self._syncing_selection = True
        try:
            self.store.clear()
            selected_path = None
            for index, heading in enumerate(headings):
                indent = "    " * max(0, heading.level - 1)
                self.store.append([f"{indent}{heading.display_title}", heading.line, heading])
                if heading == current:
                    selected_path = index
            if selected_path is None:
                self.selection.unselect_all()
            else:
                self.selection.select_path(selected_path)
                self.tree.scroll_to_cell(selected_path, None, True, 0.5, 0.0)
        finally:
            self._syncing_selection = False
        self.status.set_text(
            f"{len(headings)} section(s)."
            if headings else "No matching Markdown headings."
        )

    def select_heading(self, heading: DocumentHeading | None) -> None:
        selected_path = None
        for index, row in enumerate(self.store):
            if row[2] == heading:
                selected_path = index
                break
        self._syncing_selection = True
        try:
            if selected_path is None:
                self.selection.unselect_all()
            else:
                self.selection.select_path(selected_path)
                self.tree.scroll_to_cell(selected_path, None, True, 0.5, 0.0)
        finally:
            self._syncing_selection = False

    def _selected_heading(self) -> DocumentHeading | None:
        model, tree_iter = self.selection.get_selected()
        if tree_iter is None:
            return None
        heading = model[tree_iter][2]
        return heading if isinstance(heading, DocumentHeading) else None

    def _on_filter_changed(self, *_args) -> None:
        self.refresh()

    def _on_filter_activated(self, *_args) -> None:
        heading = self._selected_heading()
        if heading is None and len(self.store):
            heading = self.store[0][2]
        if isinstance(heading, DocumentHeading):
            self.presenter.activate(heading)

    def _on_selection_changed(self, *_args) -> None:
        if self._syncing_selection:
            return
        heading = self._selected_heading()
        if heading is not None:
            self.presenter.activate(heading)


def build_navigator_panel_view(controller, on_hide) -> NavigatorPanelViewAdapter:
    return NavigatorPanelViewAdapter(controller, on_hide)
