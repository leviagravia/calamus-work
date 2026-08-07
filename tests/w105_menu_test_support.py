"""Historical-menu semantic projection derived from W105/W104 authorities.

This is test-only compatibility support.  It intentionally does not live in
production code and does not recreate the retired imperative menu builder.  Old
wiring tests can assert their historical labels/order/callback identity against
a deterministic projection generated from the authoritative W105 MenuModel and
W104 command-target map.
"""
from __future__ import annotations

from calamus_application_commands import APPLICATION_METHOD_TARGETS, CHECK_COMMAND_IDS
from calamus_menu_model import (
    APPLICATION_MENU_MODEL,
    DynamicMenuSlotSpec,
    MenuCommandSpec,
    MenuSeparatorSpec,
    MenuSubmenuSpec,
)

_TOP_VARS = {
    "File": "filem", "Edit": "editm", "Research": "researchm",
    "Navigate": "navigatem", "Writing": "writingm", "Revise": "revisem",
    "View": "viewm", "Options": "optm", "Tools": "toolsm", "Help": "helpm",
}
_CHECK_CALLBACK = {command_id: name for name, command_id in CHECK_COMMAND_IDS.items()}
_CHECK_ATTR = {
    "research.panel": "research_item",
    "navigate.navigator-panel": "navigator_item",
    "navigate.workspace-panel": "workspace_item",
    "writing.typewriter-mode": "typewriter_item",
    "options.word-wrap": "word_wrap_item",
    "options.transparent-mode": "transparent_item",
    "options.always-on-top": "top_item",
    "options.appearance.light": "white_item",
    "options.appearance.dark": "dark_item",
    "options.line-numbers": "line_item",
}
_SUBMENU_ATTR = {
    "New from Template": "template_item",
    "Favorites": "favourites_item",
}
_SUBMENU_VAR = {
    "Opacity": "opacity_menu",
    "Writing Workspace": "workspace_menu",
    "New from Template": "template_menu",
    "Recent Files": "recent_menu",
    "Recent Workspaces": "recent_workspace_menu",
    "Favorites": "favm",
}
_DYNAMIC_SLOT_LINE = {
    "templates": 'self.invoke_command("file.template.open", source="dynamic-menu", data={"path": p})',
    "recent-files": 'self.invoke_command("file.recent.open", source="dynamic-menu", data={"path": p})',
    "recent-workspaces": 'self.invoke_command("file.workspace.recent.open", source="dynamic-menu", data={"path": p})',
    "favourites": 'self.invoke_command("file.favourite.open", source="dynamic-menu", data={"path": p})',
}


def _quoted(label: str) -> str:
    return '"' + label.replace('\\', '\\\\').replace('"', '\\"').replace('\t', '\\t') + '"'


def _callback_for(command_id: str, payload: tuple[tuple[str, object], ...]) -> str | None:
    candidates = []
    for name, target in APPLICATION_METHOD_TARGETS.items():
        if target.command_id == command_id and tuple(target.payload) == tuple(payload):
            candidates.append(name)
    if not candidates:
        return None
    candidates.sort(key=lambda n: (n.startswith("toggle_"), not n.startswith("on_"), n))
    return candidates[0]


def legacy_menu_projection() -> str:
    lines: list[str] = ["def build_menu(app):"]

    def render(menu_var: str, nodes: tuple[object, ...], indent: str = "    ") -> None:
        for node in nodes:
            if isinstance(node, MenuSeparatorSpec):
                lines.append(f"{indent}add_separator({menu_var})")
            elif isinstance(node, DynamicMenuSlotSpec):
                lines.append(f"{indent}# dynamic-slot {node.slot_id}")
                marker = _DYNAMIC_SLOT_LINE.get(node.slot_id)
                if marker:
                    lines.append(f"{indent}{marker}")
            elif isinstance(node, MenuSubmenuSpec):
                attr = _SUBMENU_ATTR.get(node.label)
                subvar = _SUBMENU_VAR.get(node.label, f"submenu_{len(lines)}")
                if attr:
                    lines.append(f"{indent}app.{attr} = Gtk.MenuItem(label={_quoted(node.label)})")
                elif node.label == "Opacity":
                    lines.append(f"{indent}opacity_item = Gtk.MenuItem(label={_quoted(node.label)})")
                else:
                    lines.append(f"{indent}{subvar}_item = Gtk.MenuItem(label={_quoted(node.label)})")
                lines.append(f"{indent}{subvar} = Gtk.Menu()")
                render(subvar, node.items, indent)
            elif isinstance(node, MenuCommandSpec):
                label = _quoted(node.label)
                if node.kind == "check":
                    attr = _CHECK_ATTR[node.command_id]
                    lines.append(f"{indent}app.{attr} = Gtk.CheckMenuItem(label={label})")
                    lines.append(f"{indent}connect_check_command(app.{attr}, app, {_quoted(node.command_id)})")
                    if node.command_id == "options.appearance.light":
                        lines.append(f'{indent}app.appearance_mode == "light"')
                    elif node.command_id == "options.appearance.dark":
                        lines.append(f'{indent}app.appearance_mode == "dark"')
                    elif node.command_id == "options.transparent-mode":
                        lines.append(f"{indent}app.opacity_percent < 100")
                    continue
                callback = _callback_for(node.command_id, node.payload)
                if callback:
                    lines.append(f"{indent}add_item({menu_var}, {label}, app.{callback})")
                elif node.command_id == "options.opacity.set":
                    # Historical source used a loop; retain its semantic shape.
                    lines.append(f'{indent}add_command_item(opacity_menu, f"{{opacity}}%", app, "options.opacity.set", {{"percent": opacity}})')
                else:
                    lines.append(f"{indent}add_command_item({menu_var}, {label}, app, {_quoted(node.command_id)}, {dict(node.payload)!r})")
            else:
                raise TypeError(node)

    for menu in APPLICATION_MENU_MODEL.menus:
        var = _TOP_VARS[menu.label]
        lines.append(f'    {var} = top_menu(app, "{menu.label}")')
        render(var, menu.items)
    lines.append("    command_shortcut_bindings()")
    return "\n".join(lines) + "\n"


def menu_model_source() -> str:
    from pathlib import Path
    return (Path(__file__).resolve().parents[1] / "calamus" / "calamus_menu_model.py").read_text(encoding="utf-8")
