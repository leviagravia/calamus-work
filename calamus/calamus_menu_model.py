"""GTK-free declarative application menu model for Calamus W105.

The model freezes application-menu hierarchy, ordering and command identity.
It contains no GTK objects, callbacks, application object, persistence or
subsystem logic. Dynamic rows are immutable projection values rendered by the
GTK adapter in :mod:`calamus_ui`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Iterable, Mapping


@dataclass(frozen=True)
class MenuCommandSpec:
    command_id: str
    label: str
    kind: str = "normal"  # normal | check
    payload: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        command_id = self.command_id.strip()
        label = self.label
        if not command_id:
            raise ValueError("menu command_id must not be empty")
        if not isinstance(label, str) or not label:
            raise ValueError("menu label must not be empty")
        if self.kind not in {"normal", "check"}:
            raise ValueError(f"unsupported menu command kind: {self.kind!r}")
        object.__setattr__(self, "command_id", command_id)
        object.__setattr__(self, "payload", tuple(sorted(self.payload)))

    def data(self) -> dict[str, object]:
        return dict(self.payload)


@dataclass(frozen=True)
class MenuSeparatorSpec:
    pass


@dataclass(frozen=True)
class DynamicMenuSlotSpec:
    slot_id: str

    def __post_init__(self) -> None:
        slot_id = self.slot_id.strip()
        if not slot_id:
            raise ValueError("dynamic slot_id must not be empty")
        object.__setattr__(self, "slot_id", slot_id)


@dataclass(frozen=True)
class MenuSubmenuSpec:
    label: str
    items: tuple[object, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("submenu label must not be empty")
        object.__setattr__(self, "items", tuple(self.items))


@dataclass(frozen=True)
class MenuSpec:
    label: str
    items: tuple[object, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("menu label must not be empty")
        object.__setattr__(self, "items", tuple(self.items))


@dataclass(frozen=True)
class MenuBarSpec:
    menus: tuple[MenuSpec, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "menus", tuple(self.menus))


@dataclass(frozen=True)
class DynamicMenuRow:
    """One immutable dynamic menu projection row.

    A separator has ``separator=True`` and no command. A disabled placeholder
    has no command and ``enabled=False``. Command rows always carry a stable
    W104 command ID and an immutable primitive payload.
    """

    label: str = ""
    command_id: str = ""
    payload: tuple[tuple[str, object], ...] = field(default_factory=tuple)
    tooltip: str = ""
    enabled: bool = True
    separator: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", tuple(sorted(self.payload)))
        if self.separator:
            if self.command_id or self.label or self.tooltip:
                raise ValueError("separator row cannot carry command presentation")
            return
        if not self.label:
            raise ValueError("dynamic menu row label must not be empty")
        if self.command_id and not self.enabled:
            raise ValueError("disabled command row is not a placeholder")

    def data(self) -> dict[str, object]:
        return dict(self.payload)


def _c(command_id: str, label: str, **payload: object) -> MenuCommandSpec:
    return MenuCommandSpec(command_id, label, payload=tuple(payload.items()))


def _k(command_id: str, label: str) -> MenuCommandSpec:
    return MenuCommandSpec(command_id, label, kind="check")


def _s() -> MenuSeparatorSpec:
    return MenuSeparatorSpec()


def _d(slot_id: str) -> DynamicMenuSlotSpec:
    return DynamicMenuSlotSpec(slot_id)


def _m(label: str, *items: object) -> MenuSubmenuSpec:
    return MenuSubmenuSpec(label, tuple(items))


APPLICATION_MENU_MODEL = MenuBarSpec((
    MenuSpec("File", (
        _c("file.new", "New\tCtrl+N"),
        _m("New from Template", _d("templates")),
        _c("file.open", "Open…\tCtrl+O"),
        _m("Recent Files", _d("recent-files")),
        _s(),
        _m("Writing Workspace",
            _c("file.workspace.show-panel", "Show Workspace Panel"),
            _c("file.workspace.new-text-file", "New Text File…"),
            _c("file.workspace.new-folder", "New Folder…"),
            _c("file.workspace.rename", "Rename Selected Item…"),
            _c("file.workspace.duplicate", "Duplicate Selected Text File"),
            _c("file.workspace.trash", "Move Selected Item to Trash"),
            _s(),
            _c("file.workspace.select-folder", "Change Workspace Folder…"),
            _m("Recent Workspaces", _d("recent-workspaces")),
            _s(),
            _c("file.workspace.refresh", "Rescan Folder Contents"),
            _c("file.workspace.reveal", "Reveal Workspace Folder in File Manager"),
            _c("file.workspace.close", "Close Workspace"),
        ),
        _s(),
        _c("file.save", "Save\tCtrl+S"),
        _c("file.save-as", "Save As…\tCtrl+Shift+S"),
        _c("file.template.save", "Save as Template…"),
        _c("file.template.manage", "Manage Templates…"),
        _m("Favorites",
            _c("file.favourite.add", "Add to Favourites\tCtrl+Alt+B"),
            _c("file.favourite.edit", "Edit Favourites…\tCtrl+Shift+D"),
            _c("file.favourite.reload", "Reload Favourites\tCtrl+Alt+R"),
            _s(),
            _d("favourites"),
        ),
        _s(),
        _c("file.print-preview", "Print Preview…\tCtrl+Shift+P"),
        _c("file.print", "Print…\tCtrl+P"),
        _s(),
        _c("file.quit", "Quit\tCtrl+Q"),
    )),
    MenuSpec("Edit", (
        _c("edit.undo", "Undo\tCtrl+Z"),
        _c("edit.redo", "Redo\tCtrl+Y"),
        _s(),
        _c("edit.cut", "Cut\tCtrl+X"),
        _c("edit.copy", "Copy\tCtrl+C"),
        _c("edit.paste", "Paste\tCtrl+V"),
        _c("edit.paste-plain", "Paste as Plain Text\tCtrl+Shift+V"),
        _c("edit.select-all", "Select All\tCtrl+A"),
        _c("edit.duplicate-line-selection", "Duplicate Line / Selection\tCtrl+D"),
        _s(),
        _c("edit.find-replace", "Find / Replace…\tCtrl+F"),
        _c("edit.find-all", "Find All…"),
        _c("edit.find-next", "Find Next Word\tCtrl+G"),
        _c("edit.find-previous", "Find Previous\tCtrl+Shift+G"),
        _c("edit.find-replace", "Replace\tCtrl+H"),
        _c("edit.replace-all", "Replace All\tCtrl+Shift+H"),
    )),
    MenuSpec("Research", (
        _k("research.panel", "Research Panel\tCtrl+Alt+C"),
        _s(),
        _c("research.clips", "Clip Collection"),
        _c("research.insert-clip", "Insert Clip…\tCtrl+Alt+K"),
        _c("research.scratchpad", "Scratchpad\tCtrl+Alt+S"),
        _c("research.bibliography", "Bibliography"),
        _c("research.open-bibliography", "Open Bibliography File"),
        _c("research.export-bibliography-markdown", "Export Bibliography as Markdown…"),
        _c("research.export-bibliography-text", "Export Bibliography as Text…"),
        _c("research.tags", "Tags"),
        _c("research.reference-sets", "Reference Sets"),
        _c("research.source-notes", "Source Notes"),
        _c("research.authoring-bridge", "Authoring Bridge"),
        _s(),
        _c("research.capture-scratchpad", "Capture Selection in Scratchpad…\tCtrl+Alt+Shift+S"),
        _c("research.new-scratchpad-section", "New Scratchpad Entry for Current Section…"),
        _c("research.show-scratchpad-section", "Show Scratchpad for Current Section"),
        _s(),
        _c("research.create-source-note", "Create Source Note from Selection…"),
        _c("research.insert-heading-link", "Insert Link to Heading…"),
        _s(),
        _c("research.quick-cite", "Quick Cite…\tCtrl+Alt+Q"),
        _c("research.open-citation", "Open Citation in Bibliography\tCtrl+Alt+Shift+Q"),
        _s(),
        _c("research.rename-reference-key", "Rename Reference Key…"),
        _c("research.check", "Research Check…"),
        _c("research.tag-integrity", "Tag Integrity…"),
        _s(),
        _c("research.import-bib", "Import BibTeX/BibLaTeX…"),
        _c("research.export-bib", "Export References as BibTeX/BibLaTeX…"),
        _c("research.export-apparatus", "Export Research Apparatus…"),
        _c("research.export-pandoc", "Export with Pandoc/citeproc…"),
    )),
    MenuSpec("Navigate", (
        _k("navigate.navigator-panel", "Navigator Panel\tCtrl+Alt+N"),
        _k("navigate.workspace-panel", "Writing Workspace"),
        _c("navigate.document-overview", "Document Overview"),
        _s(),
        _c("navigate.go-line", "Go to Line…\tCtrl+L"),
        _c("navigate.go-section", "Go to Section…\tCtrl+Shift+L"),
        _s(),
        _c("navigate.bookmark.toggle", "Insert Bookmark Here\tCtrl+F2"),
        _c("navigate.bookmark.next", "Next Bookmark\tF2"),
        _c("navigate.bookmark.previous", "Previous Bookmark\tShift+F2"),
        _c("navigate.bookmark.manage", "Manage Bookmarks…"),
        _s(),
        _c("navigate.heading.next", "Next Heading\tCtrl+PageDown"),
        _c("navigate.heading.previous", "Previous Heading\tCtrl+PageUp"),
    )),
    MenuSpec("Writing", (
        _k("writing.typewriter-mode", "Typewriter Mode\tShift+F9"),
        _s(),
        _c("writing.insert-date", "Insert Date"),
        _c("writing.insert-time", "Insert Time"),
        _c("writing.insert-date-time", "Insert Date and Time\tCtrl+Alt+D"),
    )),
    MenuSpec("Revise", (
        _c("edit.uppercase", "UPPERCASE (convert selected)\tCtrl+Alt+U"),
        _c("edit.lowercase", "Lowercase (convert selected)\tCtrl+Alt+Shift+U"),
        _c("writing.title-case", "Title Case\tCtrl+Alt+Y"),
        _c("writing.sentence-case", "Sentence case\tCtrl+Alt+Shift+Y"),
        _s(),
        _c("edit.paste-clean-pdf", "Paste Clean from PDF\tCtrl+Alt+V"),
        _c("writing.clean-pdf", "Clean Selected Text from PDF\tCtrl+Alt+Shift+V"),
        _c("writing.smart-typography", "Smart Typography\tCtrl+Alt+M"),
        _c("writing.reflow-paragraph", "Reflow Paragraph\tCtrl+Alt+J"),
        _c("writing.join-lines", "Join Lines\tCtrl+J"),
        _c("writing.remove-extra-spaces", "Remove Extra Spaces"),
        _c("writing.remove-trailing-spaces", "Remove Trailing Spaces"),
        _c("writing.sort-lines", "Sort Alphabetically A-Z\tCtrl+Alt+Up", reverse=False),
        _c("writing.sort-lines", "Sort Alphabetically Z-A\tCtrl+Alt+Down", reverse=True),
    )),
    MenuSpec("View", (
        _c("view.focus-mode", "Focus Mode\tF9"),
        _c("view.distraction-free", "Distraction-Free Mode\tF11"),
        _c("view.current-line-highlight", "Highlight Current Line\tCtrl+Alt+I"),
        _c("view.character-map", "Character Map\tCtrl+Alt+F10"),
    )),
    MenuSpec("Options", (
        _k("options.word-wrap", "Word Wrap\tAlt+Z"),
        _c("options.font", "Font…\tCtrl+Shift+F"),
        _k("options.transparent-mode", "Transparent Mode\tCtrl+Shift+T"),
        _k("options.always-on-top", "Always on Top\tCtrl+Shift+A"),
        _s(),
        _k("options.appearance.light", "White Background"),
        _k("options.appearance.dark", "Dark Mode"),
        _k("options.line-numbers", "Line Numbers"),
        _s(),
        _c("options.font-size.adjust", "Font Bigger\tCtrl++", delta=1),
        _c("options.font-size.adjust", "Font Smaller\tCtrl+-", delta=-1),
        _s(),
        _m("Opacity",
            _c("options.opacity.select", "Opacity Selection…"),
            _s(),
            *tuple(_c("options.opacity.set", f"{opacity}%", percent=opacity) for opacity in (100, 90, 88, 80, 70, 60, 50, 40, 30)),
        ),
    )),
    MenuSpec("Tools", (
        _c("tools.spellcheck", "External Spellcheck\tF7"),
        _c("writing.statistics", "Document Statistics\tCtrl+Alt+W"),
        _s(),
        _c("tools.language", "Language…"),
        _c("tools.system-info", "System Info…"),
    )),
    MenuSpec("Help", (
        _c("help.user-guide", "User Guide…"),
        _c("help.keyboard-shortcuts", "Keyboard Shortcuts\tCtrl+/"),
        _s(),
        _c("help.about", "About\tF1"),
    )),
))

TOP_LEVEL_MENU_ORDER = tuple(menu.label for menu in APPLICATION_MENU_MODEL.menus)
CHECK_COMMAND_IDS = (
    "research.panel",
    "navigate.navigator-panel",
    "navigate.workspace-panel",
    "writing.typewriter-mode",
    "options.word-wrap",
    "options.transparent-mode",
    "options.always-on-top",
    "options.appearance.light",
    "options.appearance.dark",
    "options.line-numbers",
)
DYNAMIC_SLOT_IDS = ("templates", "recent-files", "recent-workspaces", "favourites")
WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS = (
    "file.workspace.new-text-file",
    "file.workspace.new-folder",
    "file.workspace.rename",
    "file.workspace.duplicate",
    "file.workspace.trash",
)


def _walk_nodes(items: Iterable[object]):
    for item in items:
        yield item
        if isinstance(item, MenuSubmenuSpec):
            yield from _walk_nodes(item.items)


def command_nodes(model: MenuBarSpec = APPLICATION_MENU_MODEL) -> tuple[MenuCommandSpec, ...]:
    return tuple(
        node
        for menu in model.menus
        for node in _walk_nodes(menu.items)
        if isinstance(node, MenuCommandSpec)
    )


def dynamic_slots(model: MenuBarSpec = APPLICATION_MENU_MODEL) -> tuple[str, ...]:
    return tuple(
        node.slot_id
        for menu in model.menus
        for node in _walk_nodes(menu.items)
        if isinstance(node, DynamicMenuSlotSpec)
    )


def validate_menu_model(command_ids: Iterable[str], model: MenuBarSpec = APPLICATION_MENU_MODEL) -> None:
    known = set(command_ids)
    if TOP_LEVEL_MENU_ORDER != (
        "File", "Edit", "Research", "Navigate", "Writing",
        "Revise", "View", "Options", "Tools", "Help",
    ):
        raise ValueError("application top-level menu order drift")
    missing = sorted({node.command_id for node in command_nodes(model)} - known)
    if missing:
        raise ValueError(f"menu references unknown command IDs: {missing}")
    slots = dynamic_slots(model)
    if slots != DYNAMIC_SLOT_IDS:
        raise ValueError(f"dynamic slot drift: {slots!r}")
    checks = tuple(node.command_id for node in command_nodes(model) if node.kind == "check")
    if checks != CHECK_COMMAND_IDS:
        raise ValueError(f"check command drift: {checks!r}")


def template_rows(templates: Iterable[tuple[str, str]]) -> tuple[DynamicMenuRow, ...]:
    rows = tuple(
        DynamicMenuRow(str(name), "file.template.open", (("path", str(path)),))
        for name, path in templates
    )
    return rows or (DynamicMenuRow("No templates", enabled=False),)


def recent_file_rows(paths: Iterable[str]) -> tuple[DynamicMenuRow, ...]:
    values = tuple(str(path) for path in paths)
    if not values:
        return (DynamicMenuRow("No recent files", enabled=False),)
    rows = [
        DynamicMenuRow(
            os.path.basename(path) or path,
            "file.recent.open",
            (("path", path),),
            tooltip=path,
        )
        for path in values
    ]
    rows.extend((DynamicMenuRow(separator=True), DynamicMenuRow("Clear Recent Files", "file.recent.clear")))
    return tuple(rows)


def favourite_rows(paths: Iterable[str]) -> tuple[DynamicMenuRow, ...]:
    values = tuple(str(path) for path in paths)
    if not values:
        return (DynamicMenuRow("No favourites", enabled=False),)
    return tuple(
        DynamicMenuRow(
            os.path.basename(path) or path,
            "file.favourite.open",
            (("path", path),),
            tooltip=path,
        )
        for path in values
    )


def recent_workspace_rows(paths: Iterable[str]) -> tuple[DynamicMenuRow, ...]:
    values = tuple(str(path) for path in paths)
    if not values:
        return (DynamicMenuRow("No recent workspaces", enabled=False),)
    return tuple(
        DynamicMenuRow(path, "file.workspace.recent.open", (("path", path),))
        for path in values
    )
