"""Central Calamus command/shortcut registry."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ShortcutSpec:
    menu: str
    command: str
    shortcut: str
    note: str = ""


SHORTCUTS: tuple[ShortcutSpec, ...] = (
    ShortcutSpec("File", "New", "Ctrl+N"),
    ShortcutSpec("File", "New from Template", "menu"),
    ShortcutSpec("File", "Open", "Ctrl+O"),
    ShortcutSpec("File", "Save", "Ctrl+S"),
    ShortcutSpec("File", "Save As", "Ctrl+Shift+S"),
    ShortcutSpec("File", "Print Preview", "Ctrl+Shift+P"),
    ShortcutSpec("File", "Print", "Ctrl+P"),
    ShortcutSpec("File", "Open file by drag-and-drop", "Drop .txt into window"),
    ShortcutSpec("File", "Quit", "Ctrl+Q"),
    ShortcutSpec("Edit", "Undo", "Ctrl+Z"),
    ShortcutSpec("Edit", "Redo", "Ctrl+Y / Ctrl+Shift+Z"),
    ShortcutSpec("Edit", "Cut", "Ctrl+X"),
    ShortcutSpec("Edit", "Copy", "Ctrl+C"),
    ShortcutSpec("Edit", "Paste", "Ctrl+V"),
    ShortcutSpec("Edit", "Paste as Plain Text", "Ctrl+Shift+V"),
    ShortcutSpec("Edit", "Select All", "Ctrl+A"),
    ShortcutSpec("Edit", "Duplicate Line / Selection", "Ctrl+D"),
    ShortcutSpec("Edit", "Find / Replace", "Ctrl+F"),
    ShortcutSpec("Edit", "Replace", "Ctrl+H"),
    ShortcutSpec("Edit", "Replace All", "Ctrl+Shift+H"),
    ShortcutSpec("Edit", "Find Next", "Ctrl+G"),
    ShortcutSpec("Edit", "Find Previous", "Ctrl+Shift+G"),
    ShortcutSpec("Navigate", "Navigator Panel", "Ctrl+Alt+N"),
    ShortcutSpec("Navigate", "Go to Line", "Ctrl+L"),
    ShortcutSpec("Navigate", "Go to Section", "Ctrl+Shift+L"),
    ShortcutSpec("Navigate", "Next Heading", "Ctrl+PageDown"),
    ShortcutSpec("Navigate", "Previous Heading", "Ctrl+PageUp"),
    ShortcutSpec("Revise", "UPPERCASE selection", "Ctrl+Alt+U"),
    ShortcutSpec("Revise", "Lowercase selection", "Ctrl+Alt+Shift+U"),
    ShortcutSpec("Revise", "Title Case", "Ctrl+Alt+Y"),
    ShortcutSpec("Revise", "Sentence case", "Ctrl+Alt+Shift+Y"),
    ShortcutSpec("Revise", "Insert Date/Time", "Ctrl+Alt+D"),
    ShortcutSpec("Revise", "Insert Bookmark Here", "Ctrl+F2"),
    ShortcutSpec("Revise", "Next Bookmark", "F2"),
    ShortcutSpec("Revise", "Previous Bookmark", "Shift+F2"),
    ShortcutSpec("Revise", "Manage Bookmarks", "menu"),
    ShortcutSpec("Revise", "Paste Clean from PDF", "Ctrl+Alt+V"),
    ShortcutSpec("Revise", "Clean Selected Text from PDF", "Ctrl+Alt+Shift+V"),
    ShortcutSpec("Revise", "Smart Typography", "Ctrl+Alt+M"),
    ShortcutSpec("Revise", "Reflow Paragraph", "Ctrl+Alt+J"),
    ShortcutSpec("Revise", "Join Lines", "Ctrl+J"),
    ShortcutSpec("Revise", "Sort A-Z", "Ctrl+Alt+Up", "May conflict with some desktop workspace shortcuts."),
    ShortcutSpec("Revise", "Sort Z-A", "Ctrl+Alt+Down", "May conflict with some desktop workspace shortcuts."),
    ShortcutSpec("Favourites", "Add to Favourites", "Ctrl+Alt+B"),
    ShortcutSpec("Favourites", "Edit Favourites", "Ctrl+Shift+D"),
    ShortcutSpec("Favourites", "Reload Favourites", "Ctrl+Alt+R"),
    ShortcutSpec("View", "Focus Mode", "F9"),
    ShortcutSpec("View", "Distraction-Free Mode", "F11"),
    ShortcutSpec("View", "Highlight Current Line", "Ctrl+Alt+I"),
    ShortcutSpec("View", "Clip Collection", "Ctrl+Alt+C"),
    ShortcutSpec("View", "Insert Clip 1-9", "Ctrl+Alt+1..9"),
    ShortcutSpec("View", "Clip panel adjusts editor wrapping", "automatic"),
    ShortcutSpec("View", "Character Map", "Ctrl+Alt+F10"),
    ShortcutSpec("Options", "Word Wrap", "Alt+Z"),
    ShortcutSpec("Options", "Font", "Ctrl+Shift+F"),
    ShortcutSpec("Options", "Transparent Mode", "Ctrl+Shift+T"),
    ShortcutSpec("Options", "Always on Top", "Ctrl+Shift+A"),
    ShortcutSpec("Options", "Line Numbers", "Ctrl+Alt+L"),
    ShortcutSpec("Options", "Font Bigger", "Ctrl++"),
    ShortcutSpec("Options", "Font Smaller", "Ctrl+-"),
    ShortcutSpec("Tools", "External Spellcheck", "F7"),
    ShortcutSpec("Tools", "Document Statistics", "Ctrl+Alt+W"),
    ShortcutSpec("Help", "Keyboard Shortcuts", "Ctrl+/"),
    ShortcutSpec("Help", "About", "F1"),
)


def shortcut_rows() -> list[tuple[str, str, str]]:
    return [(item.menu, item.command, item.shortcut) for item in SHORTCUTS]


def display_to_accelerator(shortcut: str) -> str:
    value = (shortcut or "").strip()
    if not value or value in {"menu", "automatic"} or value.startswith("Drop "):
        return value
    replacements = (("Ctrl+", "<Control>"), ("Alt+", "<Alt>"), ("Shift+", "<Shift>"))
    for old, new in replacements:
        value = value.replace(old, new)
    value = value.replace("Quote", "quotedbl")
    value = value.replace("Ctrl++", "<Control>plus")
    value = value.replace("Ctrl+-", "<Control>minus")
    value = value.replace("Ctrl+/", "<Control>slash")
    return value


def normalize_shortcut(shortcut: str) -> str:
    return (shortcut or "").replace("<Ctrl>", "<Control>").replace("Ctrl+", "<Control>").strip()


def conflicts(shortcuts: Iterable[ShortcutSpec] = SHORTCUTS) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for spec in shortcuts:
        if spec.shortcut in {"menu", "automatic"} or spec.shortcut.startswith("Drop "):
            continue
        for raw in spec.shortcut.split(" / "):
            key = raw.strip()
            if not key or ".." in key:
                continue
            seen.setdefault(key, []).append(spec.command)
    return {key: names for key, names in seen.items() if len(names) > 1}
