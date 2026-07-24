"""GTK semantic tree view for the Writing Workspace.

The view normalizes selection before activation, then emits semantic file or
folder events. It never opens a document and never performs filesystem I/O.
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GObject, Gtk

from calamus_workspace import WorkspaceItem, WorkspaceSnapshot, parent_relative_path

COL_ICON = 0
COL_NAME = 1
COL_ITEM = 2


class WorkspaceTreeView(Gtk.TreeView):
    __gsignals__ = {
        "file-activated": (GObject.SignalFlags.RUN_LAST, None, (object,)),
        "folder-activated": (GObject.SignalFlags.RUN_LAST, None, (object,)),
        "item-context-menu": (GObject.SignalFlags.RUN_LAST, None, (object, object)),
    }

    def __init__(self) -> None:
        self.store = Gtk.TreeStore(str, str, object)
        super().__init__(model=self.store)
        self.set_name("calamus-workspace-tree")
        self.set_headers_visible(False)
        self.set_enable_search(True)
        self.set_search_column(COL_NAME)
        self.set_activate_on_single_click(False)
        self.set_tooltip_text("Double-click a file, or select it and press Enter, to open it.")

        icon_renderer = Gtk.CellRendererPixbuf()
        icon_renderer.set_property("stock-size", Gtk.IconSize.MENU)
        text_renderer = Gtk.CellRendererText()
        text_renderer.set_property("ellipsize", 3)
        text_renderer.set_property("weight", 500)
        column = Gtk.TreeViewColumn("Writing Workspace")
        # A fixed, expanding column lets the Gtk.Paned own the sidebar width.
        # Long filenames are rendered with ellipsis instead of becoming a
        # top-level minimum-width request.
        column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        column.set_fixed_width(1)
        column.set_expand(True)
        column.pack_start(icon_renderer, False)
        column.add_attribute(icon_renderer, "icon-name", COL_ICON)
        column.pack_start(text_renderer, True)
        column.add_attribute(text_renderer, "text", COL_NAME)
        self.append_column(column)
        self._text_renderer = text_renderer

        self.selection = self.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.connect("row-activated", self._on_row_activated)
        self.connect("key-press-event", self._on_key_press)
        self.connect("button-press-event", self._on_button_press)
        self.connect("popup-menu", self._on_popup_menu)

    def render(self, snapshot: WorkspaceSnapshot | None) -> None:
        # Xed exposes restore-expand-state and Geany stores fold state before
        # rebuilding a tree.  Manual Refresh must update the filesystem
        # projection without destroying the writer's navigation context.
        expanded = self.expanded_relative_paths()
        selected = self.selected_item()
        selected_relative = selected.relative_path if selected is not None else None

        self.store.clear()
        if snapshot is None:
            return
        row_by_relative: dict[str, object] = {}
        for item in snapshot.items:
            parent = parent_relative_path(item)
            parent_iter = row_by_relative.get(parent) if parent else None
            icon = self._icon_for(item)
            tree_iter = self.store.append(parent_iter, [icon, item.name, item])
            row_by_relative[item.relative_path] = tree_iter

        for relative in sorted(expanded, key=lambda value: (value.count("/"), value)):
            tree_path = self.path_for_relative(relative)
            if tree_path is not None:
                self.expand_row(tree_path, False)
        if selected_relative:
            tree_path = self.path_for_relative(selected_relative)
            if tree_path is not None:
                self.selection.select_path(tree_path)

    def expanded_relative_paths(self) -> tuple[str, ...]:
        expanded: list[str] = []

        def visit(model, tree_path, tree_iter, _data):
            item = model[tree_iter][COL_ITEM]
            if (
                isinstance(item, WorkspaceItem)
                and item.is_directory
                and self.row_expanded(tree_path)
            ):
                expanded.append(item.relative_path)
            return False

        self.store.foreach(visit, None)
        return tuple(expanded)

    def selected_item(self) -> WorkspaceItem | None:
        model, tree_iter = self.selection.get_selected()
        if tree_iter is None:
            return None
        item = model[tree_iter][COL_ITEM]
        return item if isinstance(item, WorkspaceItem) else None

    def path_for_relative(self, relative_path: str):
        found = None

        def visit(model, tree_path, tree_iter, _data):
            nonlocal found
            item = model[tree_iter][COL_ITEM]
            if isinstance(item, WorkspaceItem) and item.relative_path == relative_path:
                found = tree_path.copy()
                return True
            return False

        self.store.foreach(visit, None)
        return found

    def select_absolute_path(self, absolute_path: str) -> bool:
        target = None

        def visit(model, tree_path, tree_iter, _data):
            nonlocal target
            item = model[tree_iter][COL_ITEM]
            if isinstance(item, WorkspaceItem) and item.path == absolute_path:
                target = tree_path.copy()
                return True
            return False

        self.store.foreach(visit, None)
        if target is None:
            return False
        self.expand_to_path(target)
        self.selection.unselect_all()
        self.selection.select_path(target)
        self.scroll_to_cell(target, None, True, 0.5, 0.0)
        return True

    def activate_tree_path(self, tree_path) -> bool:
        try:
            tree_iter = self.store.get_iter(tree_path)
        except (TypeError, ValueError):
            return False
        self.selection.unselect_all()
        self.selection.select_path(tree_path)
        item = self.store[tree_iter][COL_ITEM]
        if not isinstance(item, WorkspaceItem):
            return False
        if item.is_directory:
            self.emit("folder-activated", item)
        else:
            self.emit("file-activated", item)
        return True

    def _on_row_activated(self, _tree, tree_path, _column) -> None:
        self.activate_tree_path(tree_path)

    def _on_key_press(self, _tree, event) -> bool:
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            model, tree_iter = self.selection.get_selected()
            if tree_iter is None:
                return False
            return self.activate_tree_path(model.get_path(tree_iter))
        return False

    def _select_context_path(self, tree_path):
        try:
            tree_iter = self.store.get_iter(tree_path)
        except (TypeError, ValueError):
            return None
        item = self.store[tree_iter][COL_ITEM]
        if not isinstance(item, WorkspaceItem):
            return None
        self.selection.unselect_all()
        self.selection.select_path(tree_path)
        self.set_cursor(tree_path, self.get_column(0), False)
        return item

    def _on_button_press(self, _tree, event) -> bool:
        if getattr(event, "button", 0) != Gdk.BUTTON_SECONDARY:
            return False
        hit = self.get_path_at_pos(int(event.x), int(event.y))
        if hit is None:
            return False
        item = self._select_context_path(hit[0])
        if item is None:
            return False
        self.emit("item-context-menu", item, event)
        return True

    def _on_popup_menu(self, _tree) -> bool:
        item = self.selected_item()
        if item is None:
            return False
        self.emit("item-context-menu", item, None)
        return True

    def _icon_for(self, item: WorkspaceItem) -> str:
        if item.is_symlink:
            return "emblem-symbolic-link"
        if item.is_directory:
            return "folder-symbolic"
        if item.internal_text:
            return "text-x-generic-symbolic"
        return "document-open-symbolic"
