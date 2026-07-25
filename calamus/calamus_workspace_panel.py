"""GTK panel and visibility runtime for the read-only Writing Workspace."""
from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, Pango

from calamus_panel_chrome import build_compact_close_button
from calamus_workspace import WorkspaceItem, WorkspaceSnapshot
from calamus_workspace_tree import WorkspaceTreeView


class WorkspacePanelView:
    def __init__(
        self,
        *,
        on_hide: Callable[[], None],
        on_new_text_file: Callable[[], None],
        on_new_folder: Callable[[], None],
        on_rename_item: Callable[[], None],
        on_duplicate_file: Callable[[], None],
        on_move_to_trash: Callable[[], None],
        on_choose_root: Callable[[], None],
        on_refresh: Callable[[], None],
        on_reveal: Callable[[], None],
        on_activate_item: Callable[[WorkspaceItem], None],
    ) -> None:
        for callback in (on_hide, on_new_text_file, on_new_folder, on_rename_item, on_duplicate_file, on_move_to_trash, on_choose_root, on_refresh, on_reveal, on_activate_item):
            if not callable(callback):
                raise TypeError("workspace panel callbacks must be callable")
        self._on_activate_item = on_activate_item
        self._on_rename_item = on_rename_item
        self._on_duplicate_file = on_duplicate_file
        self._on_move_to_trash = on_move_to_trash
        self._context_menu = None
        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.widget.set_name("calamus-workspace-panel")
        for setter in (self.widget.set_margin_start, self.widget.set_margin_end,
                       self.widget.set_margin_top, self.widget.set_margin_bottom):
            setter(6)

        # Xed/gedit keep the panel title separate from the action toolbar.
        # Putting title, root path and four buttons on one horizontal requisition
        # makes their minimum widths additive and leaks that width to Gtk.Window.
        self.header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.title = Gtk.Label()
        self.title.set_markup("<b>Writing Workspace</b>")
        self.title.set_xalign(0)
        self.title.set_hexpand(True)
        self.title.set_ellipsize(Pango.EllipsizeMode.END)
        self.title.set_max_width_chars(20)
        self.header.pack_start(self.title, True, True, 0)
        self.header.pack_end(build_compact_close_button(
            on_hide,
            name="workspace-close-button",
            tooltip="Hide Writing Workspace",
        ), False, False, 0)
        self.widget.pack_start(self.header, False, False, 0)

        # The action row is independent from the title row, matching mature
        # file-browser sidebars. Its width is therefore the maximum of the rows,
        # never the sum of title + actions.
        self.action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.action_row.set_halign(Gtk.Align.START)
        for index, (icon_name, tooltip, callback) in enumerate((
            ("document-new-symbolic", "Create a new .txt or .md file in the selected folder", on_new_text_file),
            ("folder-new-symbolic", "Create a new folder in the selected folder", on_new_folder),
            ("folder-open-symbolic", "Change the Workspace folder", on_choose_root),
            ("view-refresh-symbolic", "Rescan after files or folders changed outside Calamus", on_refresh),
            ("folder-symbolic", "Reveal the current Workspace folder in File Manager", on_reveal),
        )):
            button = Gtk.Button()
            button.set_name(f"workspace-action-{index}")
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.set_focus_on_click(False)
            button.set_size_request(24, 24)
            button.set_tooltip_text(tooltip)
            image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            if hasattr(image, "set_pixel_size"):
                image.set_pixel_size(14)
            button.add(image)
            button.connect("clicked", lambda _button, action=callback: action())
            self.action_row.pack_start(button, False, False, 0)
        self.widget.pack_start(self.action_row, False, False, 0)

        # Xed/gedit show a bounded location component, not an unconstrained
        # absolute path label. The full root remains available as a tooltip.
        self.root_label = Gtk.Label(label="No folder selected")
        self.root_label.set_name("calamus-workspace-root")
        self.root_label.set_xalign(0)
        self.root_label.set_hexpand(True)
        self.root_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.root_label.set_width_chars(1)
        self.root_label.set_max_width_chars(24)
        self.widget.pack_start(self.root_label, False, False, 0)

        self.hint = Gtk.Label(label="Open, create, rename, duplicate and trash · bounded writing tree")
        self.hint.set_name("calamus-workspace-hint")
        self.hint.set_xalign(0)
        self.hint.set_hexpand(True)
        self.hint.set_ellipsize(Pango.EllipsizeMode.END)
        self.hint.set_width_chars(1)
        self.hint.set_max_width_chars(24)
        self.widget.pack_start(self.hint, False, False, 0)

        self.status = Gtk.Label()
        self.status.set_name("calamus-workspace-status")
        self.status.set_xalign(0)
        self.status.set_hexpand(True)
        self.status.set_ellipsize(Pango.EllipsizeMode.END)
        self.status.set_width_chars(1)
        self.status.set_max_width_chars(24)
        self.widget.pack_start(self.status, False, False, 0)

        self.tree = WorkspaceTreeView()
        self.tree.connect("file-activated", self._on_file_activated)
        self.tree.connect("folder-activated", self._on_folder_activated)
        self.tree.connect("item-context-menu", self._on_item_context_menu)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        if hasattr(self.scroll, "set_propagate_natural_width"):
            self.scroll.set_propagate_natural_width(False)
        if hasattr(self.scroll, "set_min_content_width"):
            self.scroll.set_min_content_width(1)
        self.scroll.set_hexpand(True)
        self.scroll.set_vexpand(True)
        self.scroll.add(self.tree)
        self.widget.pack_start(self.scroll, True, True, 0)

    def render(self, snapshot: WorkspaceSnapshot | None) -> None:
        self.tree.render(snapshot)
        if snapshot is None:
            self.root_label.set_text("No folder selected")
            self.status.set_text("Choose one local folder for the Writing Workspace.")
            return
        display_root = os.path.basename(snapshot.root.rstrip(os.sep)) or snapshot.root
        self.root_label.set_text(display_root)
        self.root_label.set_tooltip_text(snapshot.root)
        files = sum(1 for item in snapshot.items if not item.is_directory)
        folders = sum(1 for item in snapshot.items if item.is_directory)
        warnings = f" — {len(snapshot.diagnostics)} warning(s)" if snapshot.diagnostics else ""
        self.status.set_text(f"{files} file(s), {folders} folder(s){warnings}")

    def selected_item(self) -> WorkspaceItem | None:
        return self.tree.selected_item()

    def select_path(self, path: str) -> bool:
        return self.tree.select_absolute_path(os.path.abspath(path))

    def focus_tree(self) -> None:
        self.tree.grab_focus()

    def _on_item_context_menu(self, tree, item: WorkspaceItem, event) -> None:
        # The tree owns only pointer/keyboard selection semantics.  This menu is
        # a thin capability adapter: every action delegates to the same App
        # gateway used by File → Writing Workspace.  It owns no filesystem logic.
        menu = Gtk.Menu()

        rename = Gtk.MenuItem(label="Rename…")
        rename.connect("activate", lambda _menu_item: self._on_rename_item())
        menu.append(rename)

        # W83 duplicates only one regular internal .txt/.md file.  Folders,
        # symlinks and other document types therefore do not expose the action.
        if item.internal_text and not item.is_directory and not item.is_symlink:
            duplicate = Gtk.MenuItem(label="Duplicate")
            duplicate.connect(
                "activate", lambda _menu_item: self._on_duplicate_file()
            )
            menu.append(duplicate)

        # W84 exposes only the canonical system-Trash gateway.  No permanent
        # delete action exists, and symbolic links remain outside the bounded
        # mutation scope.
        if not item.is_symlink and not item.name.endswith(".source-notes.md"):
            menu.append(Gtk.SeparatorMenuItem())
            trash = Gtk.MenuItem(label="Move to Trash")
            trash.connect(
                "activate", lambda _menu_item: self._on_move_to_trash()
            )
            menu.append(trash)

        menu.show_all()
        self._context_menu = menu
        if event is not None and hasattr(menu, "popup_at_pointer"):
            menu.popup_at_pointer(event)
        elif hasattr(menu, "popup_at_widget"):
            menu.popup_at_widget(
                tree, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None
            )
        else:
            menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def _on_file_activated(self, _tree, item: WorkspaceItem) -> None:
        self._on_activate_item(item)

    def _on_folder_activated(self, tree: WorkspaceTreeView, item: WorkspaceItem) -> None:
        tree_path = tree.path_for_relative(item.relative_path)
        if tree_path is None:
            return
        if tree.row_expanded(tree_path):
            tree.collapse_row(tree_path)
        else:
            tree.expand_row(tree_path, False)


class WorkspacePanelRuntime:
    def __init__(self, host: Any, view: WorkspacePanelView, menu_item: Any, editor_focus: Callable[[], None], on_visibility_changed: Callable[[bool], None]) -> None:
        if not callable(editor_focus) or not callable(on_visibility_changed):
            raise TypeError("workspace runtime callbacks must be callable")
        self._host = host
        self._view = view
        self._menu_item = menu_item
        self._editor_focus = editor_focus
        self._on_visibility_changed = on_visibility_changed
        self._syncing = False
        self._host.subscribe(self._host_visibility_changed)

    @property
    def is_visible(self) -> bool:
        return bool(self._host.is_visible)

    def set_visible(self, visible: bool) -> bool:
        target = bool(visible)
        if target:
            self._host.show()
            self._view.focus_tree()
        else:
            self._host.hide()
            self._editor_focus()
        self._sync_menu(target)
        self._on_visibility_changed(target)
        return target

    def toggle(self) -> bool:
        return self.set_visible(not self.is_visible)

    def hide(self) -> bool:
        return self.set_visible(False)

    def on_menu_toggled(self, menu_item: Any) -> None:
        if not self._syncing:
            self.set_visible(menu_item.get_active())

    def _host_visibility_changed(self, visible: bool) -> None:
        self._sync_menu(visible)
        self._on_visibility_changed(bool(visible))

    def _sync_menu(self, visible: bool) -> None:
        if self._menu_item.get_active() == bool(visible):
            return
        self._syncing = True
        try:
            self._menu_item.set_active(bool(visible))
        finally:
            self._syncing = False
