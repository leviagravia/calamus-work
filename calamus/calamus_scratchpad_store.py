"""Canonical UTF-8 Markdown sidecar persistence for Calamus Scratchpad."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from calamus_research_file import FileToken, atomic_write_utf8, file_token
from calamus_scratchpad import ScratchpadEntry

_HEADER = "# Calamus Scratchpad v1"
_RECORD_PREFIX = "## "
_BODY_HEADING = "### Body"
_FIELD_LABELS = (
    ("Type", "type"),
    ("Title", "title"),
    ("Status", "status"),
    ("Tags", "tags"),
    ("Sections", "sections"),
    ("Created", "created"),
    ("Updated", "updated"),
)
_KNOWN_FIELDS = {label.casefold(): attribute for label, attribute in _FIELD_LABELS}


@dataclass(frozen=True)
class ScratchpadDiagnostic:
    line: int
    message: str


@dataclass(frozen=True)
class ScratchpadSnapshot:
    entries: tuple[ScratchpadEntry, ...]
    token: FileToken
    diagnostics: tuple[ScratchpadDiagnostic, ...] = ()


@dataclass(frozen=True)
class ScratchpadSaveResult:
    status: str
    token: FileToken
    message: str = ""

    @property
    def saved(self) -> bool:
        return self.status == "saved"


def scratchpad_path(document_path: Any) -> str | None:
    if not isinstance(document_path, str) or not document_path.strip():
        return None
    return os.path.abspath(os.path.expanduser(document_path.strip())) + ".scratchpad.md"


def _fence_for(text: str) -> str:
    longest = current = 0
    for character in text:
        if character == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return "`" * max(3, longest + 1)


def serialize_scratchpad_markdown(entries: tuple[ScratchpadEntry, ...] | list[ScratchpadEntry]) -> str:
    lines = [_HEADER, ""]
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, ScratchpadEntry):
            raise TypeError("entries must contain ScratchpadEntry values")
        if entry.id in seen:
            raise ValueError(f"duplicate Scratchpad entry id: {entry.id}")
        seen.add(entry.id)
        lines.extend([f"{_RECORD_PREFIX}{entry.id}", ""])
        for label, attribute in _FIELD_LABELS:
            value = getattr(entry, attribute)
            if attribute in {"tags", "sections"}:
                value = ", ".join(value)
            lines.append(f"{label}: {value}")
        for label, value in entry.extra_fields:
            lines.append(f"{label}: {value}")
        fence = _fence_for(entry.body)
        lines.extend(["", _BODY_HEADING, "", fence + "text", entry.body.rstrip(), fence, ""])
    return "\n".join(lines).rstrip() + "\n"


def _parse_fenced_block(lines: list[str], index: int, diagnostics: list[ScratchpadDiagnostic]) -> tuple[list[str], int]:
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        diagnostics.append(ScratchpadDiagnostic(index + 1, "Body has no fenced block."))
        return [], index
    opener = lines[index].strip()
    ticks = len(opener) - len(opener.lstrip("`"))
    if ticks < 3 or opener[ticks:].strip().casefold() not in {"", "text", "markdown", "md"}:
        diagnostics.append(ScratchpadDiagnostic(index + 1, "Body must use a Markdown text fence."))
        return [], index
    fence = "`" * ticks
    index += 1
    content: list[str] = []
    while index < len(lines) and lines[index].strip() != fence:
        content.append(lines[index])
        index += 1
    if index >= len(lines):
        diagnostics.append(ScratchpadDiagnostic(index + 1, "Body fence is not closed."))
        return content, index
    return content, index + 1


def parse_scratchpad_markdown(text: Any) -> tuple[tuple[ScratchpadEntry, ...], tuple[ScratchpadDiagnostic, ...]]:
    if not isinstance(text, str):
        return (), (ScratchpadDiagnostic(1, "Scratchpad file is not text."),)
    lines = text.splitlines()
    diagnostics: list[ScratchpadDiagnostic] = []
    entries: list[ScratchpadEntry] = []
    first_content = next(((position + 1, line.strip()) for position, line in enumerate(lines) if line.strip()), None)
    if first_content is not None and first_content[1] != _HEADER:
        diagnostics.append(ScratchpadDiagnostic(first_content[0], f"Expected Scratchpad header: {_HEADER}."))
    seen: set[str] = set()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith(_RECORD_PREFIX) or line.strip() in {_HEADER, _BODY_HEADING}:
            index += 1
            continue
        start_line = index + 1
        entry_id = line[len(_RECORD_PREFIX):].strip()
        index += 1
        fields: dict[str, Any] = {"tags": [], "sections": []}
        extras: list[tuple[str, str]] = []
        while index < len(lines) and lines[index].strip() != _BODY_HEADING:
            current = lines[index]
            if current.startswith(_RECORD_PREFIX):
                diagnostics.append(ScratchpadDiagnostic(start_line, f"{entry_id}: missing {_BODY_HEADING}."))
                break
            if ":" in current and current.strip():
                label, value = current.split(":", 1)
                clean_label = " ".join(label.split()).strip()
                clean_value = value.strip()
                attribute = _KNOWN_FIELDS.get(clean_label.casefold())
                if attribute in {"tags", "sections"}:
                    fields[attribute].extend(item.strip() for item in clean_value.split(",") if item.strip())
                elif attribute:
                    fields[attribute] = clean_value
                else:
                    extras.append((clean_label, clean_value))
            index += 1
        if index >= len(lines) or lines[index].strip() != _BODY_HEADING:
            while index < len(lines) and not lines[index].startswith(_RECORD_PREFIX):
                index += 1
            continue
        index += 1
        body_lines, index = _parse_fenced_block(lines, index, diagnostics)
        if not entry_id:
            diagnostics.append(ScratchpadDiagnostic(start_line, "Scratchpad heading has no id."))
            continue
        if entry_id in seen:
            diagnostics.append(ScratchpadDiagnostic(start_line, f"Duplicate Scratchpad entry id: {entry_id}."))
            continue
        try:
            entry = ScratchpadEntry(
                id=entry_id,
                type=fields.get("type", "note"),
                title=fields.get("title", ""),
                status=fields.get("status", "inbox"),
                tags=tuple(fields.get("tags", ())),
                sections=tuple(fields.get("sections", ())),
                created=fields.get("created", ""),
                updated=fields.get("updated", ""),
                body="\n".join(body_lines).strip("\n"),
                extra_fields=tuple(extras),
            )
        except ValueError as error:
            diagnostics.append(ScratchpadDiagnostic(start_line, f"{entry_id}: {error}."))
            continue
        seen.add(entry.id)
        entries.append(entry)
    return tuple(entries), tuple(diagnostics)


class MarkdownScratchpadStore:
    def __init__(self, path: str) -> None:
        if not isinstance(path, str) or not path:
            raise ValueError("Scratchpad path is required")
        self.path = path

    def load(self) -> ScratchpadSnapshot:
        token = file_token(self.path)
        if not token.exists:
            return ScratchpadSnapshot((), token, ())
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError as error:
            return ScratchpadSnapshot((), token, (ScratchpadDiagnostic(1, str(error)),))
        entries, diagnostics = parse_scratchpad_markdown(text)
        return ScratchpadSnapshot(entries, token, diagnostics)

    def save(
        self,
        entries: tuple[ScratchpadEntry, ...] | list[ScratchpadEntry],
        expected_token: FileToken,
        *,
        force: bool = False,
    ) -> ScratchpadSaveResult:
        current = file_token(self.path)
        if not force and current != expected_token:
            return ScratchpadSaveResult("conflict", current, "Scratchpad changed outside Calamus.")
        try:
            text = serialize_scratchpad_markdown(entries)
            return ScratchpadSaveResult("saved", atomic_write_utf8(self.path, text))
        except (OSError, TypeError, ValueError) as error:
            return ScratchpadSaveResult("error", current, str(error))
