"""Pure document-structure model for Calamus.

The structure is derived from the current UTF-8 text buffer.  It is never a
second document authority and never persists a parallel outline.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


_ATX_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,}).*$")
_LINE_ENDINGS = ("\r\n", "\n", "\r", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029")


def _strip_line_ending(line: str) -> str:
    for ending in _LINE_ENDINGS:
        if line.endswith(ending):
            return line[: -len(ending)]
    return line


def _closing_fence(line: str, marker: str, minimum: int) -> bool:
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3 or not stripped:
        return False
    run = 0
    for character in stripped:
        if character == marker:
            run += 1
        else:
            break
    return run >= minimum and stripped[run:].strip(" \t") == ""


@dataclass(frozen=True)
class DocumentHeading:
    """One ATX Markdown heading in the current document."""

    level: int
    title: str
    line: int
    start_offset: int
    section_end_offset: int

    def __post_init__(self) -> None:
        if not isinstance(self.level, int) or isinstance(self.level, bool):
            raise TypeError("level must be int")
        if not 1 <= self.level <= 6:
            raise ValueError("level must be between 1 and 6")
        if not isinstance(self.title, str):
            raise TypeError("title must be str")
        if not isinstance(self.line, int) or isinstance(self.line, bool):
            raise TypeError("line must be int")
        if self.line < 1:
            raise ValueError("line must be one-based")
        for name, value in (
            ("start_offset", self.start_offset),
            ("section_end_offset", self.section_end_offset),
        ):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be int")
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.section_end_offset < self.start_offset:
            raise ValueError("section_end_offset cannot precede start_offset")

    @property
    def display_title(self) -> str:
        return self.title or "(Untitled heading)"


@dataclass(frozen=True)
class DocumentStructure:
    """Immutable heading index derived from one text snapshot."""

    headings: tuple[DocumentHeading, ...] = ()
    text_length: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.headings, tuple):
            object.__setattr__(self, "headings", tuple(self.headings))
        if not isinstance(self.text_length, int) or isinstance(self.text_length, bool):
            raise TypeError("text_length must be int")
        if self.text_length < 0:
            raise ValueError("text_length cannot be negative")
        previous = -1
        for heading in self.headings:
            if not isinstance(heading, DocumentHeading):
                raise TypeError("headings must contain DocumentHeading values")
            if heading.start_offset <= previous:
                raise ValueError("headings must be strictly ordered by offset")
            if heading.section_end_offset > self.text_length:
                raise ValueError("heading section end exceeds text length")
            previous = heading.start_offset

    def current_heading(self, cursor_offset: int) -> DocumentHeading | None:
        cursor = _validated_offset(cursor_offset, self.text_length)
        current = None
        for heading in self.headings:
            if heading.start_offset > cursor:
                break
            current = heading
        return current

    def next_heading(self, cursor_offset: int) -> DocumentHeading | None:
        cursor = _validated_offset(cursor_offset, self.text_length)
        for heading in self.headings:
            if heading.start_offset > cursor:
                return heading
        return None

    def previous_heading(self, cursor_offset: int) -> DocumentHeading | None:
        cursor = _validated_offset(cursor_offset, self.text_length)
        previous = None
        for heading in self.headings:
            if heading.start_offset >= cursor:
                break
            previous = heading
        return previous

    def filtered(self, query: str) -> tuple[DocumentHeading, ...]:
        if not isinstance(query, str):
            raise TypeError("query must be str")
        needle = query.strip().casefold()
        if not needle:
            return self.headings
        return tuple(
            heading for heading in self.headings
            if needle in heading.title.casefold()
        )


def _validated_offset(offset: int, text_length: int) -> int:
    if not isinstance(offset, int) or isinstance(offset, bool):
        raise TypeError("cursor_offset must be int")
    if offset < 0:
        raise ValueError("cursor_offset cannot be negative")
    return min(offset, text_length)


def build_document_structure(text: str) -> DocumentStructure:
    """Parse ATX Markdown headings outside fenced code blocks.

    The parser accepts headings with up to three leading spaces and one to six
    ``#`` characters followed by whitespace or end-of-line.  Optional closing
    hashes are removed from the display title.  Setext headings are deliberately
    excluded from the first canonical core.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")

    raw_headings: list[dict[str, object]] = []
    open_sections: list[int] = []
    fence_marker: str | None = None
    fence_length = 0
    offset = 0

    for line_number, chunk in enumerate(text.splitlines(keepends=True), start=1):
        line = _strip_line_ending(chunk)

        if fence_marker is not None:
            if _closing_fence(line, fence_marker, fence_length):
                fence_marker = None
                fence_length = 0
            offset += len(chunk)
            continue

        fence = _FENCE_OPEN_RE.match(line)
        if fence:
            run = fence.group(1)
            fence_marker = run[0]
            fence_length = len(run)
            offset += len(chunk)
            continue

        match = _ATX_HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            raw_title = match.group(2) or ""
            title = re.sub(r"[ \t]+#+[ \t]*$", "", raw_title).strip()

            while open_sections and int(raw_headings[open_sections[-1]]["level"]) >= level:
                index = open_sections.pop()
                raw_headings[index]["section_end_offset"] = offset

            raw_headings.append(
                {
                    "level": level,
                    "title": title,
                    "line": line_number,
                    "start_offset": offset,
                    "section_end_offset": len(text),
                }
            )
            open_sections.append(len(raw_headings) - 1)

        offset += len(chunk)

    # ``splitlines`` returns no row for an empty string, and no extra row after
    # a terminal newline.  That is correct because only actual heading starts
    # are indexed and every open section reaches the text boundary.
    headings = tuple(DocumentHeading(**values) for values in raw_headings)
    return DocumentStructure(headings=headings, text_length=len(text))
