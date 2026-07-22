"""Canonical UTF-8 Markdown persistence for the global Calamus reference library."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from calamus_references import ReferenceRecord
from calamus_research_file import FileToken, atomic_write_utf8, file_token

_HEADER = "# Calamus References v1"
_ANNOTATION = "### Annotation"
_KNOWN_FIELDS = {
    "type": "type",
    "author": "authors",
    "title": "title",
    "year": "year",
    "editor": "editors",
    "container title": "container_title",
    "publisher": "publisher",
    "location": "location",
    "volume": "volume",
    "issue": "issue",
    "pages": "pages",
    "doi": "doi",
    "isbn": "isbn",
    "issn": "issn",
    "url": "url",
    "language": "language",
    "file": "file_path",
    "tags": "tags",
}
_FIELD_LABELS = (
    ("Type", "type"),
    ("Author", "authors"),
    ("Title", "title"),
    ("Year", "year"),
    ("Editor", "editors"),
    ("Container Title", "container_title"),
    ("Publisher", "publisher"),
    ("Location", "location"),
    ("Volume", "volume"),
    ("Issue", "issue"),
    ("Pages", "pages"),
    ("DOI", "doi"),
    ("ISBN", "isbn"),
    ("ISSN", "issn"),
    ("URL", "url"),
    ("Language", "language"),
    ("File", "file_path"),
    ("Tags", "tags"),
)


@dataclass(frozen=True)
class ReferenceDiagnostic:
    line: int
    message: str
    blocking: bool = True


@dataclass(frozen=True)
class ReferenceLibrarySnapshot:
    records: tuple[ReferenceRecord, ...]
    token: FileToken
    diagnostics: tuple[ReferenceDiagnostic, ...] = ()

    @property
    def writable(self) -> bool:
        return not any(item.blocking for item in self.diagnostics)


@dataclass(frozen=True)
class ReferenceSaveResult:
    status: str
    token: FileToken
    message: str = ""

    @property
    def saved(self) -> bool:
        return self.status == "saved"


def default_references_path(home: str | None = None, data_home: str | None = None) -> str:
    base_home = os.path.expanduser(home or "~")
    root = data_home or os.environ.get("XDG_DATA_HOME") or os.path.join(base_home, ".local", "share")
    return os.path.join(root, "calamus", "research", "references.md")


def serialize_references_markdown(records: tuple[ReferenceRecord, ...] | list[ReferenceRecord]) -> str:
    lines = [_HEADER, ""]
    for record in records:
        if not isinstance(record, ReferenceRecord):
            raise TypeError("records must contain ReferenceRecord values")
        lines.extend([f"## {record.key}", ""])
        for label, attribute in _FIELD_LABELS:
            value = getattr(record, attribute)
            if attribute in {"authors", "editors"}:
                for item in value:
                    lines.append(f"{label}: {item}")
                if not value and label == "Author":
                    lines.append("Author:")
            elif attribute == "tags":
                lines.append(f"Tags: {', '.join(value)}")
            else:
                lines.append(f"{label}: {value}")
        for label, value in record.extra_fields:
            lines.append(f"{label}: {value}")
        lines.extend(["", _ANNOTATION, "", record.annotation.rstrip(), ""])
    return "\n".join(lines).rstrip() + "\n"


def parse_references_markdown(text: Any) -> tuple[tuple[ReferenceRecord, ...], tuple[ReferenceDiagnostic, ...]]:
    if not isinstance(text, str):
        return (), (ReferenceDiagnostic(1, "Reference library is not text."),)
    lines = text.splitlines()
    records: list[ReferenceRecord] = []
    diagnostics: list[ReferenceDiagnostic] = []
    first_content = next(((position + 1, line.strip()) for position, line in enumerate(lines) if line.strip()), None)
    if first_content is not None and first_content[1] != _HEADER:
        diagnostics.append(
            ReferenceDiagnostic(first_content[0], f"Expected library header: {{_HEADER}}.")
        )
    seen: set[str] = set()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("## "):
            index += 1
            continue
        start_line = index + 1
        key = line[3:].strip()
        index += 1
        fields: dict[str, Any] = {"authors": [], "editors": [], "tags": []}
        extras: list[tuple[str, str]] = []
        annotation: list[str] = []
        in_annotation = False
        while index < len(lines) and not lines[index].startswith("## "):
            current = lines[index]
            if current.strip() == _ANNOTATION:
                in_annotation = True
                index += 1
                if index < len(lines) and not lines[index].strip():
                    index += 1
                continue
            if in_annotation:
                annotation.append(current)
                index += 1
                continue
            if ":" in current and current.strip():
                label, value = current.split(":", 1)
                label_clean = " ".join(label.split()).strip()
                value_clean = value.strip()
                attribute = _KNOWN_FIELDS.get(label_clean.casefold())
                if attribute in {"authors", "editors"}:
                    if value_clean:
                        fields[attribute].append(value_clean)
                elif attribute == "tags":
                    fields[attribute].extend(item.strip() for item in value_clean.split(",") if item.strip())
                elif attribute:
                    fields[attribute] = value_clean
                else:
                    extras.append((label_clean, value_clean))
            index += 1
        if not key:
            diagnostics.append(ReferenceDiagnostic(start_line, "Reference heading has no key."))
            continue
        if key in seen:
            diagnostics.append(ReferenceDiagnostic(start_line, f"Duplicate reference key: {key}."))
            continue
        try:
            record = ReferenceRecord(
                key=key,
                title=fields.get("title", ""),
                type=fields.get("type", "book"),
                authors=tuple(fields["authors"]),
                year=fields.get("year", ""),
                editors=tuple(fields["editors"]),
                container_title=fields.get("container_title", ""),
                publisher=fields.get("publisher", ""),
                location=fields.get("location", ""),
                volume=fields.get("volume", ""),
                issue=fields.get("issue", ""),
                pages=fields.get("pages", ""),
                doi=fields.get("doi", ""),
                isbn=fields.get("isbn", ""),
                issn=fields.get("issn", ""),
                url=fields.get("url", ""),
                language=fields.get("language", ""),
                file_path=fields.get("file_path", ""),
                tags=tuple(fields["tags"]),
                annotation="\n".join(annotation).strip("\n"),
                extra_fields=tuple(extras),
            )
        except ValueError as error:
            diagnostics.append(ReferenceDiagnostic(start_line, f"{key or 'Reference'}: {error}."))
            continue
        seen.add(record.key)
        records.append(record)
    return tuple(records), tuple(diagnostics)


class MarkdownReferenceStore:
    """Load/save the one canonical Markdown library with conflict detection."""

    def __init__(self, path: str | None = None) -> None:
        self.path = path or default_references_path()

    def load(self) -> ReferenceLibrarySnapshot:
        token = file_token(self.path)
        if not token.exists:
            return ReferenceLibrarySnapshot((), token, ())
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError as error:
            return ReferenceLibrarySnapshot((), token, (ReferenceDiagnostic(1, str(error)),))
        records, diagnostics = parse_references_markdown(text)
        return ReferenceLibrarySnapshot(records, token, diagnostics)

    def save(
        self,
        records: tuple[ReferenceRecord, ...] | list[ReferenceRecord],
        expected_token: FileToken,
        *,
        force: bool = False,
    ) -> ReferenceSaveResult:
        current = file_token(self.path)
        if not force and current != expected_token:
            return ReferenceSaveResult("conflict", current, "References file changed outside Calamus.")
        try:
            text = serialize_references_markdown(records)
        except (TypeError, ValueError) as error:
            return ReferenceSaveResult("error", current, str(error))
        try:
            return ReferenceSaveResult("saved", atomic_write_utf8(self.path, text))
        except OSError as error:
            return ReferenceSaveResult("error", current, str(error))
