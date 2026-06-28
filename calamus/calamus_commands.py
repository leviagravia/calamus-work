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



def line_bounds_at_offset(text: str, cursor: int) -> Range:
    """Return start/end offsets for the logical line containing cursor.

    The returned end excludes the newline character, matching the legacy
    App.current_line_bounds_from_text behavior.
    """
    text = text if isinstance(text, str) else ""
    pos = clamp_offset(cursor, text)
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    if end == -1:
        end = len(text)
    return start, end


def duplicate_line_or_selection_plan(text: str, cursor: int, selection: Range | None = None):
    """Return a pure insertion plan for Duplicate Line/Selection.

    Return value:
        (insert_pos, insertion, selection_tuple, duplicates_selection)

    Buffer mutation and command/undo grouping intentionally remain in
    the application boundary.
    """
    text = text if isinstance(text, str) else ""

    if selection is not None:
        start, end = normalize_range(selection[0], selection[1], text)
        if start != end:
            selected = text[start:end]
            insert_pos = end
            return insert_pos, selected, (end, end + len(selected)), True

    cursor = clamp_offset(cursor, text)
    start, end = line_bounds_at_offset(text, cursor)
    line = text[start:end]
    if end < len(text) and text[end:end + 1] == "\n":
        insert_pos = end + 1
        insertion = line + "\n"
    else:
        insert_pos = end
        insertion = "\n" + line
    new_cursor = insert_pos + len(insertion)
    return insert_pos, insertion, (new_cursor, new_cursor), False


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
