"""Pure command helpers for Calamus editor actions.

The GTK application remains responsible for applying text to Gtk.TextBuffer;
this module keeps edit transformations testable and independent from GTK.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple

Range = Tuple[int, int]


def clamp_offset(offset: int, text: str) -> int:
    try:
        value = int(offset)
    except (TypeError, ValueError):
        value = 0
    return max(0, min(len(text), value))


def normalize_range(start: int, end: int, text: str) -> Range:
    a = clamp_offset(start, text)
    b = clamp_offset(end, text)
    return (a, b) if a <= b else (b, a)


def replace_range(text: str, start: int, end: int, replacement: str) -> tuple[str, Range]:
    a, b = normalize_range(start, end, text)
    replacement = replacement if isinstance(replacement, str) else ""
    new_text = text[:a] + replacement + text[b:]
    return new_text, (a, a + len(replacement))


def insert_at(text: str, offset: int, insertion: str) -> tuple[str, Range]:
    pos = clamp_offset(offset, text)
    insertion = insertion if isinstance(insertion, str) else ""
    return replace_range(text, pos, pos, insertion)


def transform_range(text: str, start: int, end: int, transform: Callable[[str], str]) -> tuple[str, Range]:
    a, b = normalize_range(start, end, text)
    replacement = transform(text[a:b])
    return replace_range(text, a, b, replacement)


@dataclass(frozen=True)
class CommandSpec:
    name: str
    shortcut: str | None = None
    mutates_document: bool = False


COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("New", "<Control>N"),
    CommandSpec("Open", "<Control>O"),
    CommandSpec("Save", "<Control>S"),
    CommandSpec("Save As", "<Control><Shift>S"),
    CommandSpec("Insert Date/Time", "<Control><Alt>D", True),
    CommandSpec("Paste Clean from PDF", "<Control><Alt>V", True),
    CommandSpec("Clean Selected Text from PDF", "<Control><Alt><Shift>V", True),
    CommandSpec("Sort A-Z", "<Control><Alt>Up", True),
    CommandSpec("Sort Z-A", "<Control><Alt>Down", True),
    CommandSpec("Clip Collection", "<Control><Alt>C"),
    CommandSpec("Character Map", "<Control><Alt>F10"),
)


def shortcut_conflicts(commands: tuple[CommandSpec, ...] = COMMANDS) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for command in commands:
        if command.shortcut:
            key = command.shortcut.replace("<Ctrl>", "<Control>")
            seen.setdefault(key, []).append(command.name)
    return {shortcut: names for shortcut, names in seen.items() if len(names) > 1}
