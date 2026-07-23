"""Pure document-structure model for Calamus.

The structure is derived from the current UTF-8 text buffer.  It is never a
second document authority and never persists a parallel outline.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import shlex


_ATX_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,}).*$")
_TRAILING_ATTRIBUTE_RE = re.compile(r"(?:^|[ \t]+)\{([^{}]*)\}[ \t]*$")
_LINE_ENDINGS = ("\r\n", "\n", "\r", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029")
_DIAGNOSTIC_KINDS = frozenset(
    {
        "malformed-heading-identifier",
        "multiple-heading-identifiers",
        "duplicate-heading-identifier",
    }
)


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


def _split_attribute_tokens(content: str) -> tuple[str, ...] | None:
    lexer = shlex.shlex(content, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return tuple(lexer)
    except ValueError:
        return None


def _attribute_token_kind(token: str) -> str | None:
    if token.startswith("#"):
        return "identifier"
    if len(token) > 1 and token.startswith("."):
        return "class"
    if "=" in token and token.split("=", 1)[0]:
        return "key-value"
    return None


def is_valid_heading_identifier(identifier: str) -> bool:
    if not identifier:
        return False
    if not (identifier[0].isalpha() or identifier[0] == "_"):
        return False
    return all(
        character.isalnum() or character in "_-."
        for character in identifier[1:]
    )


@dataclass(frozen=True)
class DocumentStructureDiagnostic:
    """One non-destructive document-structure diagnostic."""

    kind: str
    line: int
    start_offset: int
    message: str
    identifier: str | None = None
    related_lines: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in _DIAGNOSTIC_KINDS:
            raise ValueError("unsupported document-structure diagnostic kind")
        if not isinstance(self.line, int) or isinstance(self.line, bool):
            raise TypeError("line must be int")
        if self.line < 1:
            raise ValueError("line must be one-based")
        if not isinstance(self.start_offset, int) or isinstance(self.start_offset, bool):
            raise TypeError("start_offset must be int")
        if self.start_offset < 0:
            raise ValueError("start_offset cannot be negative")
        if not isinstance(self.message, str):
            raise TypeError("message must be str")
        if self.identifier is not None and not isinstance(self.identifier, str):
            raise TypeError("identifier must be str or None")
        if not isinstance(self.related_lines, tuple):
            object.__setattr__(self, "related_lines", tuple(self.related_lines))
        for related_line in self.related_lines:
            if not isinstance(related_line, int) or isinstance(related_line, bool):
                raise TypeError("related_lines must contain int values")
            if related_line < 1:
                raise ValueError("related lines must be one-based")


@dataclass(frozen=True)
class DocumentHeading:
    """One ATX Markdown heading in the current document."""

    level: int
    title: str
    line: int
    start_offset: int
    section_end_offset: int
    identifier: str | None = None

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
        if self.identifier is not None:
            if not isinstance(self.identifier, str):
                raise TypeError("identifier must be str or None")
            if not is_valid_heading_identifier(self.identifier):
                raise ValueError("identifier must use the canonical heading-ID grammar")

    @property
    def display_title(self) -> str:
        return self.title or "(Untitled heading)"


@dataclass(frozen=True)
class DocumentStructure:
    """Immutable heading index derived from one text snapshot."""

    headings: tuple[DocumentHeading, ...] = ()
    text_length: int = 0
    diagnostics: tuple[DocumentStructureDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.headings, tuple):
            object.__setattr__(self, "headings", tuple(self.headings))
        if not isinstance(self.diagnostics, tuple):
            object.__setattr__(self, "diagnostics", tuple(self.diagnostics))
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
        for diagnostic in self.diagnostics:
            if not isinstance(diagnostic, DocumentStructureDiagnostic):
                raise TypeError(
                    "diagnostics must contain DocumentStructureDiagnostic values"
                )
            if diagnostic.start_offset > self.text_length:
                raise ValueError("diagnostic offset exceeds text length")

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

    def headings_for_identifier(self, identifier: str) -> tuple[DocumentHeading, ...]:
        if not isinstance(identifier, str):
            raise TypeError("identifier must be str")
        target = identifier.strip()
        if target.startswith("#"):
            target = target[1:]
        if not target:
            return ()
        if not is_valid_heading_identifier(target):
            raise ValueError("identifier must use the canonical heading-ID grammar")
        return tuple(
            heading for heading in self.headings
            if heading.identifier == target
        )

    def unique_heading_for_identifier(self, identifier: str) -> DocumentHeading | None:
        matches = self.headings_for_identifier(identifier)
        return matches[0] if len(matches) == 1 else None

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


def _parse_heading_title(
    raw_title: str,
    *,
    line: int,
    start_offset: int,
) -> tuple[str, str | None, tuple[DocumentStructureDiagnostic, ...]]:
    stripped = raw_title.rstrip(" \t")
    attribute_match = _TRAILING_ATTRIBUTE_RE.search(stripped)
    attribute_tokens: tuple[str, ...] | None = None
    attribute_like = False

    if attribute_match:
        attribute_tokens = _split_attribute_tokens(attribute_match.group(1))
        if attribute_tokens is None:
            attribute_like = any(
                marker in attribute_match.group(1) for marker in ("#", ".", "=")
            )
        else:
            attribute_like = any(
                _attribute_token_kind(token) is not None for token in attribute_tokens
            )

    if not attribute_match or not attribute_like:
        title = re.sub(r"[ \t]+#+[ \t]*$", "", raw_title).strip()
        return title, None, ()

    title_source = stripped[: attribute_match.start()].rstrip(" \t")
    title = re.sub(r"[ \t]+#+[ \t]*$", "", title_source).strip()
    diagnostics: list[DocumentStructureDiagnostic] = []

    if attribute_tokens is None:
        diagnostics.append(
            DocumentStructureDiagnostic(
                kind="malformed-heading-identifier",
                line=line,
                start_offset=start_offset,
                message="Malformed Pandoc heading attribute block.",
            )
        )
        return title, None, tuple(diagnostics)

    token_kinds = tuple(_attribute_token_kind(token) for token in attribute_tokens)
    identifier_tokens = tuple(
        token for token, kind in zip(attribute_tokens, token_kinds)
        if kind == "identifier"
    )
    invalid_tokens = tuple(
        token for token, kind in zip(attribute_tokens, token_kinds)
        if kind is None
    )

    if len(identifier_tokens) > 1:
        diagnostics.append(
            DocumentStructureDiagnostic(
                kind="multiple-heading-identifiers",
                line=line,
                start_offset=start_offset,
                message="A heading may contain only one explicit identifier.",
                related_lines=(line,),
            )
        )
        return title, None, tuple(diagnostics)

    if not identifier_tokens:
        return title, None, ()

    candidate = identifier_tokens[0][1:]
    if invalid_tokens or not is_valid_heading_identifier(candidate):
        diagnostics.append(
            DocumentStructureDiagnostic(
                kind="malformed-heading-identifier",
                line=line,
                start_offset=start_offset,
                message="The explicit heading identifier is malformed.",
                identifier=candidate or None,
            )
        )
        return title, None, tuple(diagnostics)

    return title, candidate, ()


def build_document_structure(text: str) -> DocumentStructure:
    """Parse ATX Markdown headings outside fenced code blocks.

    The parser accepts headings with up to three leading spaces and one to six
    ``#`` characters followed by whitespace or end-of-line.  Optional closing
    hashes and one trailing Pandoc attribute block are removed from the display
    title.  A valid explicit ``{#identifier}`` is exposed as stable heading
    identity.  Setext headings are deliberately excluded from the canonical
    core.
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")

    raw_headings: list[dict[str, object]] = []
    diagnostics: list[DocumentStructureDiagnostic] = []
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
            title, identifier, heading_diagnostics = _parse_heading_title(
                raw_title,
                line=line_number,
                start_offset=offset,
            )
            diagnostics.extend(heading_diagnostics)

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
                    "identifier": identifier,
                }
            )
            open_sections.append(len(raw_headings) - 1)

        offset += len(chunk)

    headings = tuple(DocumentHeading(**values) for values in raw_headings)

    identifiers: dict[str, list[DocumentHeading]] = {}
    for heading in headings:
        if heading.identifier is not None:
            identifiers.setdefault(heading.identifier, []).append(heading)
    for identifier, matches in identifiers.items():
        if len(matches) > 1:
            diagnostics.append(
                DocumentStructureDiagnostic(
                    kind="duplicate-heading-identifier",
                    line=matches[0].line,
                    start_offset=matches[0].start_offset,
                    message=f"Duplicate heading identifier: {identifier}",
                    identifier=identifier,
                    related_lines=tuple(item.line for item in matches),
                )
            )

    return DocumentStructure(
        headings=headings,
        text_length=len(text),
        diagnostics=tuple(diagnostics),
    )
