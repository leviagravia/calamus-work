"""Read-only shortcut-guide projection from the canonical W104 command catalog."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from calamus_command_catalog import shortcut_guide_entries


@dataclass(frozen=True)
class ShortcutSpec:
    menu: str
    command: str
    shortcut: str
    note: str = ""


SHORTCUTS: tuple[ShortcutSpec, ...] = tuple(
    ShortcutSpec(entry.menu, entry.command, entry.access, entry.note)
    for entry in shortcut_guide_entries()
)


def shortcut_rows() -> list[tuple[str, str, str]]:
    return [(item.menu, item.command, item.shortcut) for item in SHORTCUTS]


def display_to_accelerator(value: str) -> str:
    """Compatibility converter for audit tools; actual bindings come from catalog."""
    value = (value or "").strip()
    if not value or value in {"menu", "automatic"} or value.startswith("Drop "):
        return value
    # Exact special forms first: the historical implementation applied these
    # too late and drifted from the real Gtk accelerator spellings.
    specials = {
        "Ctrl++": "<Control>plus", "Ctrl+-": "<Control>minus", "Ctrl+/": "<Control>slash",
        "Ctrl+PageDown": "<Control>Page_Down", "Ctrl+PageUp": "<Control>Page_Up",
    }
    if value in specials:
        return specials[value]
    value = value.replace("Ctrl+", "<Control>")
    value = value.replace("Alt+", "<Alt>")
    value = value.replace("Shift+", "<Shift>")
    value = value.replace("Quote", "quotedbl")
    return value


def conflicts(shortcuts: Iterable[ShortcutSpec] = SHORTCUTS) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for item in shortcuts:
        if item.shortcut in {"menu", "automatic"} or item.shortcut.startswith("Drop ") or ".." in item.shortcut:
            continue
        for shortcut in item.shortcut.split(" / "):
            key = display_to_accelerator(shortcut.strip())
            seen.setdefault(key, []).append(item.command)
    return {key: values for key, values in seen.items() if len(values) > 1}
