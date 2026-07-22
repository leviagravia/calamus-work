"""Canonical UTF-8 Markdown sidecar persistence for document Source Notes."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from calamus_research_file import FileToken, atomic_write_utf8, file_token
from calamus_source_notes import SourceLocator, SourceNote

_HEADER = "# Calamus Source Notes v1"
_RECORD_PREFIX = "## Source Note: "
_TEXT_HEADING = "### Text"
_COMMENT_HEADING = "### Comment"
_KNOWN_FIELDS = {
    "reference": "reference_key",
    "kind": "kind",
    "page": "page",
    "page end": "page_end",
    "chapter": "chapter",
    "section": "section",
    "paragraph": "paragraph",
    "tags": "tags",
    "created": "created",
    "modified": "modified",
}
_FIELD_LABELS = (
    ("Reference", "reference_key"),
    ("Kind", "kind"),
    ("Page", "page"),
    ("Page End", "page_end"),
    ("Chapter", "chapter"),
    ("Section", "section"),
    ("Paragraph", "paragraph"),
    ("Tags", "tags"),
    ("Created", "created"),
    ("Modified", "modified"),
)


@dataclass(frozen=True)
class SourceNoteDiagnostic:
    line: int
    message: str
    blocking: bool = True


@dataclass(frozen=True)
class SourceNoteSnapshot:
    notes: tuple[SourceNote, ...]
    token: FileToken
    diagnostics: tuple[SourceNoteDiagnostic, ...] = ()

    @property
    def writable(self) -> bool:
        return not any(item.blocking for item in self.diagnostics)


@dataclass(frozen=True)
class SourceNoteSaveResult:
    status: str
    token: FileToken
    message: str = ""

    @property
    def saved(self) -> bool:
        return self.status == "saved"


def source_notes_path(document_path: Any) -> str | None:
    if not isinstance(document_path, str) or not document_path.strip():
        return None
    return os.path.abspath(os.path.expanduser(document_path.strip())) + ".source-notes.md"


def _fence_for(text: str) -> str:
    longest = 0
    current = 0
    for character in text:
        if character == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return "`" * max(3, longest + 1)


def _append_fenced(lines: list[str], heading: str, text: str) -> None:
    fence = _fence_for(text)
    lines.extend([heading, "", fence + "text", text.rstrip(), fence, ""])


def serialize_source_notes_markdown(notes: tuple[SourceNote, ...] | list[SourceNote]) -> str:
    lines = [_HEADER, ""]
    for note in notes:
        if not isinstance(note, SourceNote):
            raise TypeError("notes must contain SourceNote values")
        lines.extend([f"{_RECORD_PREFIX}{note.id}", ""])
        for label, attribute in _FIELD_LABELS:
            if attribute in {"page", "page_end", "chapter", "section", "paragraph"}:
                value = getattr(note.locator, attribute)
            else:
                value = getattr(note, attribute)
            if attribute == "tags":
                value = ", ".join(value)
            lines.append(f"{label}: {value}")
        for label, value in note.extra_fields:
            lines.append(f"{label}: {value}")
        lines.append("")
        _append_fenced(lines, _TEXT_HEADING, note.text)
        _append_fenced(lines, _COMMENT_HEADING, note.comment)
    return "\n".join(lines).rstrip() + "\n"


def _parse_fenced_block(
    lines: list[str],
    index: int,
    heading: str,
    diagnostics: list[SourceNoteDiagnostic],
) -> tuple[list[str], int]:
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        diagnostics.append(SourceNoteDiagnostic(index + 1, f"{heading} has no fenced block."))
        return [], index
    opener = lines[index].strip()
    ticks = len(opener) - len(opener.lstrip("`"))
    if ticks < 3 or opener[ticks:].strip().casefold() not in {"", "text"}:
        diagnostics.append(SourceNoteDiagnostic(index + 1, f"{heading} must use a Markdown text fence."))
        return [], index
    fence = "`" * ticks
    index += 1
    content: list[str] = []
    while index < len(lines) and lines[index].strip() != fence:
        content.append(lines[index])
        index += 1
    if index >= len(lines):
        diagnostics.append(SourceNoteDiagnostic(index + 1, f"{heading} fence is not closed."))
        return content, index
    return content, index + 1

def parse_source_notes_markdown(
    text: Any,
) -> tuple[tuple[SourceNote, ...], tuple[SourceNoteDiagnostic, ...]]:
    if not isinstance(text, str):
        return (), (SourceNoteDiagnostic(1, "Source Notes file is not text."),)
    lines = text.splitlines()
    diagnostics: list[SourceNoteDiagnostic] = []
    notes: list[SourceNote] = []
    first_content = next(
        ((position + 1, line.strip()) for position, line in enumerate(lines) if line.strip()),
        None,
    )
    if first_content is not None and first_content[1] != _HEADER:
        diagnostics.append(
            SourceNoteDiagnostic(first_content[0], f"Expected Source Notes header: {_HEADER}.")
        )
    seen: set[str] = set()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith(_RECORD_PREFIX):
            index += 1
            continue
        start_line = index + 1
        note_id = line[len(_RECORD_PREFIX):].strip()
        index += 1
        fields: dict[str, Any] = {"tags": []}
        extras: list[tuple[str, str]] = []
        while index < len(lines) and lines[index].strip() != _TEXT_HEADING:
            current = lines[index]
            if current.startswith(_RECORD_PREFIX):
                diagnostics.append(SourceNoteDiagnostic(start_line, f"{note_id}: missing {_TEXT_HEADING}."))
                break
            if ":" in current and current.strip():
                label, value = current.split(":", 1)
                clean_label = " ".join(label.split()).strip()
                clean_value = value.strip()
                attribute = _KNOWN_FIELDS.get(clean_label.casefold())
                if attribute == "tags":
                    fields[attribute].extend(
                        item.strip() for item in clean_value.split(",") if item.strip()
                    )
                elif attribute:
                    fields[attribute] = clean_value
                else:
                    extras.append((clean_label, clean_value))
            index += 1
        if index >= len(lines) or lines[index].strip() != _TEXT_HEADING:
            while index < len(lines) and not lines[index].startswith(_RECORD_PREFIX):
                index += 1
            continue
        index += 1
        text_lines, index = _parse_fenced_block(lines, index, _TEXT_HEADING, diagnostics)
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines) or lines[index].strip() != _COMMENT_HEADING:
            diagnostics.append(SourceNoteDiagnostic(start_line, f"{note_id}: missing {_COMMENT_HEADING}."))
            while index < len(lines) and not lines[index].startswith(_RECORD_PREFIX):
                index += 1
            continue
        index += 1
        comment_lines, index = _parse_fenced_block(lines, index, _COMMENT_HEADING, diagnostics)
        if not note_id:
            diagnostics.append(SourceNoteDiagnostic(start_line, "Source Note heading has no id."))
            continue
        if note_id in seen:
            diagnostics.append(SourceNoteDiagnostic(start_line, f"Duplicate Source Note id: {note_id}."))
            continue
        try:
            note = SourceNote(
                id=note_id,
                reference_key=fields.get("reference_key", ""),
                kind=fields.get("kind", "comment"),
                locator=SourceLocator(
                    page=fields.get("page", ""),
                    page_end=fields.get("page_end", ""),
                    chapter=fields.get("chapter", ""),
                    section=fields.get("section", ""),
                    paragraph=fields.get("paragraph", ""),
                ),
                tags=tuple(fields.get("tags", ())),
                created=fields.get("created", ""),
                modified=fields.get("modified", ""),
                text="\n".join(text_lines).strip("\n"),
                comment="\n".join(comment_lines).strip("\n"),
                extra_fields=tuple(extras),
            )
        except ValueError as error:
            diagnostics.append(SourceNoteDiagnostic(start_line, f"{note_id}: {error}."))
            continue
        seen.add(note.id)
        notes.append(note)
    return tuple(notes), tuple(diagnostics)


class MarkdownSourceNoteStore:
    def __init__(self, path: str) -> None:
        if not isinstance(path, str) or not path:
            raise ValueError("Source Notes path is required")
        self.path = path

    def load(self) -> SourceNoteSnapshot:
        token = file_token(self.path)
        if not token.exists:
            return SourceNoteSnapshot((), token, ())
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError as error:
            return SourceNoteSnapshot(
                (), token, (SourceNoteDiagnostic(1, str(error)),)
            )
        notes, diagnostics = parse_source_notes_markdown(text)
        return SourceNoteSnapshot(notes, token, diagnostics)

    def save(
        self,
        notes: tuple[SourceNote, ...] | list[SourceNote],
        expected_token: FileToken,
        *,
        force: bool = False,
    ) -> SourceNoteSaveResult:
        current = file_token(self.path)
        if not force and current != expected_token:
            return SourceNoteSaveResult(
                "conflict",
                current,
                "Source Notes file changed outside Calamus.",
            )
        try:
            text = serialize_source_notes_markdown(notes)
            return SourceNoteSaveResult("saved", atomic_write_utf8(self.path, text))
        except (OSError, TypeError, ValueError) as error:
            return SourceNoteSaveResult("error", current, str(error))
