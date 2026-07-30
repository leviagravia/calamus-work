"""Deterministic, non-executable Clip body expansion."""
from __future__ import annotations

from dataclasses import dataclass

from calamus_clips import ClipValidationError

_CURSOR_MARKER = "{{cursor}}"


@dataclass(frozen=True)
class ClipExpansion:
    text: str
    cursor_offset: int


def expand_clip_text(text: str) -> ClipExpansion:
    if not isinstance(text, str):
        raise TypeError("clip body must be text")
    count = text.count(_CURSOR_MARKER)
    if count > 1:
        raise ClipValidationError("A clip may contain at most one {{cursor}} marker.")
    if count == 0:
        return ClipExpansion(text, len(text))
    offset = text.index(_CURSOR_MARKER)
    return ClipExpansion(text.replace(_CURSOR_MARKER, "", 1), offset)
