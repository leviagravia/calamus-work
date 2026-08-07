"""GTK application-menu and shortcut projection for Calamus.

W105 makes the application menu a projection of GTK-free menu/state values.
This module is the single application-menu owner allowed to create menu widgets
and call their set_active()/set_sensitive()/visibility methods.
"""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from calamus_application_commands import command_target_for_callback
from calamus_command_catalog import build_command_registry, shortcut_bindings as command_shortcut_bindings
from calamus_menu_model import (
    APPLICATION_MENU_MODEL,
    DynamicMenuRow,
    DynamicMenuSlotSpec,
    MenuBarSpec,
    MenuCommandSpec,
    MenuSeparatorSpec,
    MenuSubmenuSpec,
    validate_menu_model,
)
from calamus_ui_state import UiStateSnapshot


def top_menu(app, label: str) -> Gtk.Menu:
    """Historical GTK helper retained for local compatibility tests.

    W105 application-menu construction itself uses MenuGtkAdapter.
    """
    item = Gtk.MenuItem(label=label)
    menu = Gtk.Menu()
    item.set_submenu(menu)
    app.menubar.append(item)
    return menu


def add_item(menu: Gtk.Menu, label: str, callback):
    """Compatibility constructor routed through stable W104 command IDs."""
    item = Gtk.MenuItem(label=label)
    owner = getattr(callback, "__self__", None)
    if owner is not None and hasattr(owner, "invoke_command"):
        target = command_target_for_callback(callback)
        if target is None:
            raise RuntimeError(
                f"Uncatalogued Calamus menu callback: {getattr(callback, '__name__', callback)!r}"
            )
        item.connect(
            "activate",
            lambda *_args, app=owner, command_id=target.command_id, data=target.data():
                app.invoke_command(command_id, source="menu", data=data),
        )
    else:
        item.connect("activate", callback)
    menu.append(item)
    return item


def add_command_item(menu: Gtk.Menu, label: str, app, command_id: str, data=None):
    item = Gtk.MenuItem(label=label)
    payload = dict(data or {})
    item.connect(
        "activate",
        lambda *_args, cid=command_id, values=payload: app.invoke_command(
            cid, source="menu", data=values
        ),
    )
    menu.append(item)
    return item


def add_separator(menu: Gtk.Menu) -> None:
    menu.append(Gtk.SeparatorMenuItem())


class MenuGtkAdapter:
    """Single GTK renderer/projector for the global application menu."""

    def __init__(self, menubar: Gtk.MenuBar, invoke_command) -> None:
        if menubar is None or not callable(getattr(menubar, "append", None)):
            raise TypeError("menubar does not implement the GTK menu-bar protocol")
        if not callable(invoke_command):
            raise TypeError("invoke_command must be callable")
        self._menubar = menubar
        self._invoke_command = invoke_command
        self._command_widgets: dict[str, list[Gtk.MenuItem]] = {}
        self._dynamic_menus: dict[str, Gtk.Menu] = {}
        self._dynamic_widgets: dict[str, list[Gtk.Widget]] = {}
        self._projection_depth = 0
        self._built = False

    @property
    def projection_active(self) -> bool:
        return self._projection_depth > 0

    def build(self, model: MenuBarSpec = APPLICATION_MENU_MODEL) -> "MenuGtkAdapter":
        if self._built:
            raise RuntimeError("application menu already built")
        registry = build_command_registry()
        validate_menu_model(registry.command_ids(), model)
        for menu_spec in model.menus:
            top_item = Gtk.MenuItem(label=menu_spec.label)
            menu = Gtk.Menu()
            top_item.set_submenu(menu)
            self._menubar.append(top_item)
            self._render_nodes(menu, menu_spec.items)
        self._built = True
        return self

    def _render_nodes(self, menu: Gtk.Menu, nodes: tuple[object, ...]) -> None:
        for node in nodes:
            if isinstance(node, MenuSeparatorSpec):
                menu.append(Gtk.SeparatorMenuItem())
                continue
            if isinstance(node, DynamicMenuSlotSpec):
                if node.slot_id in self._dynamic_menus:
                    raise RuntimeError(f"duplicate dynamic menu slot: {node.slot_id}")
                self._dynamic_menus[node.slot_id] = menu
                self._dynamic_widgets[node.slot_id] = []
                continue
            if isinstance(node, MenuSubmenuSpec):
                item = Gtk.MenuItem(label=node.label)
                submenu = Gtk.Menu()
                item.set_submenu(submenu)
                menu.append(item)
                self._render_nodes(submenu, node.items)
                continue
            if isinstance(node, MenuCommandSpec):
                item = (
                    Gtk.CheckMenuItem(label=node.label)
                    if node.kind == "check"
                    else Gtk.MenuItem(label=node.label)
                )
                payload = node.data()
                if node.kind == "check":
                    item.connect(
                        "toggled",
                        lambda widget, cid=node.command_id: self._on_check_toggled(cid, widget),
                    )
                else:
                    item.connect(
                        "activate",
                        lambda *_args, cid=node.command_id, values=payload: self._invoke_command(
                            cid, source="menu", data=dict(values)
                        ),
                    )
                menu.append(item)
                self._command_widgets.setdefault(node.command_id, []).append(item)
                continue
            raise TypeError(f"unsupported menu model node: {node!r}")

    def _on_check_toggled(self, command_id: str, widget) -> None:
        if self.projection_active:
            return
        self._invoke_command(
            command_id,
            source="menu",
            data={"active": bool(widget.get_active())},
        )

    def project(self, snapshot: UiStateSnapshot) -> None:
        if not isinstance(snapshot, UiStateSnapshot):
            raise TypeError("snapshot must be UiStateSnapshot")
        self._projection_depth += 1
        try:
            for command_id, state in snapshot.states.items():
                for widget in self._command_widgets.get(command_id, ()):
                    if widget.get_sensitive() != state.enabled:
                        widget.set_sensitive(state.enabled)
                    if state.checked is not None and isinstance(widget, Gtk.CheckMenuItem):
                        if bool(widget.get_active()) != bool(state.checked):
                            widget.set_active(bool(state.checked))
                    if state.visible:
                        widget.show()
                    else:
                        widget.hide()
        finally:
            self._projection_depth -= 1

    def render_dynamic(self, slot_id: str, rows: tuple[DynamicMenuRow, ...]) -> tuple[object, ...]:
        slot_id = str(slot_id)
        menu = self._dynamic_menus.get(slot_id)
        if menu is None:
            raise KeyError(f"unknown dynamic menu slot: {slot_id}")
        for widget in tuple(self._dynamic_widgets.get(slot_id, ())):
            menu.remove(widget)
        created: list[object] = []
        for row in tuple(rows):
            if not isinstance(row, DynamicMenuRow):
                raise TypeError("dynamic menu rows must be DynamicMenuRow")
            if row.separator:
                item = Gtk.SeparatorMenuItem()
            else:
                item = Gtk.MenuItem(label=row.label)
                if row.tooltip:
                    item.set_tooltip_text(row.tooltip)
                if row.command_id:
                    payload = row.data()
                    item.connect(
                        "activate",
                        lambda *_args, cid=row.command_id, values=payload: self._invoke_command(
                            cid, source="dynamic-menu", data=dict(values)
                        ),
                    )
                if not row.enabled:
                    item.set_sensitive(False)
            menu.append(item)
            created.append(item)
        self._dynamic_widgets[slot_id] = created
        menu.show_all()
        return tuple(created)

    def widgets_for_command(self, command_id: str) -> tuple[object, ...]:
        return tuple(self._command_widgets.get(str(command_id), ()))

    def dynamic_menu(self, slot_id: str):
        return self._dynamic_menus.get(str(slot_id))

    def dynamic_widgets(self, slot_id: str) -> tuple[object, ...]:
        return tuple(self._dynamic_widgets.get(str(slot_id), ()))


def build_menu(app) -> MenuGtkAdapter:
    adapter = MenuGtkAdapter(app.menubar, app.invoke_command).build()
    app.menu_ui_adapter = adapter
    controller = getattr(app, "ui_state_controller", None)
    if controller is not None:
        controller.bind_projector(adapter)
        app.refresh_ui_state()

    # Dynamic application-menu families are data projections owned by App's
    # existing storage authorities; only the GTK rendering lives here.
    app.populate_template_menu()
    app.populate_recent_menu()
    app.populate_favourites_menu()
    app.populate_recent_workspaces_menu()
    return adapter


def shortcut_bindings(app):
    rows = []
    for accelerator, command_id, data in command_shortcut_bindings():
        payload = dict(data)
        rows.append((
            accelerator,
            lambda *_args, cid=command_id, values=payload: app.invoke_command(
                cid, source="shortcut", data=values
            ),
        ))
    return tuple(rows)


def shortcut_conflicts(bindings: tuple[tuple[str, object], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for shortcut, _callback in bindings:
        counts[shortcut] = counts.get(shortcut, 0) + 1
    return {shortcut: count for shortcut, count in counts.items() if count > 1}


def add_shortcuts(app) -> None:
    acc = Gtk.AccelGroup()
    app.add_accel_group(acc)
    bindings = shortcut_bindings(app)
    conflicts = shortcut_conflicts(bindings)
    if conflicts:
        raise RuntimeError(f"Duplicate Calamus shortcuts: {conflicts}")
    for shortcut, callback in bindings:
        key, mod = Gtk.accelerator_parse(shortcut)
        acc.connect(key, mod, Gtk.AccelFlags.VISIBLE, lambda *args, cb=callback: (cb(), True)[1])
