"""Pure Authoring Bridge projection and heading-link planner for Calamus.

The bridge derives relationships from one immutable snapshot of the current
UTF-8 document, References, Source Notes and canonical document structure.  It
never persists a graph, count, cache or secondary index.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from calamus_citations import parse_citation_clusters
from calamus_document_structure import (
    DocumentStructure,
    is_valid_heading_identifier,
)
from calamus_references import ReferenceRecord, normalize_key
from calamus_related_references import effective_related_keys
from calamus_source_notes import SourceNote


_HEADING_LINK_RE = re.compile(
    r"(?<!!)\[(?P<label>(?:\\.|[^\\\]\n])+)\]"
    r"\(\s*#(?P<identifier>[A-Za-z_][A-Za-z0-9_.-]*)\s*\)"
)
_FENCE_RE = re.compile(r"^[ \t]{0,3}(?P<mark>`{3,}|~{3,})")
_ALLOWED_OCCURRENCE_KINDS = frozenset(
    {
        "citation",
        "source-note-reference",
        "heading-link",
        "source-note-target",
        "broken-citation",
        "broken-heading-link",
        "broken-source-note-reference",
        "broken-source-note-target",
        "heading-diagnostic",
        "related-reference",
    }
)
_ALLOWED_NAVIGATION_KINDS = frozenset({"document", "source-note", "reference"})


def _one_line(value: str) -> str:
    return " ".join(value.splitlines()).strip() if isinstance(value, str) else ""


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, min(len(text), offset))) + 1


def _line_excerpt(text: str, offset: int, *, limit: int = 150) -> str:
    start = text.rfind("\n", 0, max(0, offset)) + 1
    end = text.find("\n", max(0, offset))
    if end < 0:
        end = len(text)
    compact = _one_line(text[start:end])
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _closing_fence(line: str, marker: str, minimum: int) -> bool:
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3:
        return False
    count = 0
    for character in stripped:
        if character == marker:
            count += 1
        else:
            break
    return count >= minimum and stripped[count:].strip(" \t\r\n") == ""


def _fenced_ranges(text: str) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    marker = ""
    minimum = 0
    active_start: int | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        if active_start is None:
            match = _FENCE_RE.match(line)
            if match:
                mark = match.group("mark")
                marker = mark[0]
                minimum = len(mark)
                active_start = offset
        elif _closing_fence(line, marker, minimum):
            ranges.append((active_start, offset + len(line)))
            active_start = None
            marker = ""
            minimum = 0
        offset += len(line)
    if active_start is not None:
        ranges.append((active_start, len(text)))
    return tuple(ranges)


def _inside(ranges: Iterable[tuple[int, int]], offset: int) -> bool:
    return any(start <= offset < end for start, end in ranges)


def _inline_code_ranges(
    text: str,
    fenced: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    line_start = 0
    for line in text.splitlines(keepends=True):
        if not _inside(fenced, line_start):
            index = 0
            while index < len(line):
                if line[index] != "`":
                    index += 1
                    continue
                run_end = index + 1
                while run_end < len(line) and line[run_end] == "`":
                    run_end += 1
                marker = line[index:run_end]
                close = line.find(marker, run_end)
                if close < 0:
                    break
                ranges.append((line_start + index, line_start + close + len(marker)))
                index = close + len(marker)
        line_start += len(line)
    return tuple(ranges)


def _excluded_ranges(text: str) -> tuple[tuple[int, int], ...]:
    fenced = _fenced_ranges(text)
    return tuple(sorted((*fenced, *_inline_code_ranges(text, fenced))))


def _unescape_link_label(label: str) -> str:
    return re.sub(r"\\([\\\]])", r"\1", label)


def _escape_link_label(label: str) -> str:
    return label.replace("\\", "\\\\").replace("]", "\\]")


@dataclass(frozen=True)
class MarkdownHeadingLink:
    """One internal Markdown link to an explicit heading identifier."""

    label: str
    identifier: str
    start_offset: int
    end_offset: int
    line: int
    raw: str

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("heading-link label must be non-empty")
        if not is_valid_heading_identifier(self.identifier):
            raise ValueError("heading-link identifier is invalid")
        for name in ("start_offset", "end_offset", "line"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be int")
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise ValueError("heading-link offsets are invalid")
        if self.line < 1:
            raise ValueError("heading-link line must be one-based")


@dataclass(frozen=True)
class BridgeSubject:
    kind: str
    identifier: str
    label: str

    def __post_init__(self) -> None:
        if self.kind not in {"reference", "heading", "issues", "related"}:
            raise ValueError("bridge subject kind is invalid")
        if not isinstance(self.identifier, str) or not self.identifier:
            raise ValueError("bridge subject identifier is required")
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("bridge subject label is required")


@dataclass(frozen=True)
class BridgeOccurrence:
    """One stable, directly navigable relationship or problem."""

    id: str
    kind: str
    subject_kind: str
    subject_id: str
    label: str
    detail: str
    navigation_kind: str
    line: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    source_note_id: str = ""
    reference_key: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("bridge occurrence id is required")
        if self.kind not in _ALLOWED_OCCURRENCE_KINDS:
            raise ValueError("bridge occurrence kind is invalid")
        if self.subject_kind not in {"reference", "heading", "issues", "related"}:
            raise ValueError("bridge occurrence subject kind is invalid")
        if not isinstance(self.subject_id, str) or not self.subject_id:
            raise ValueError("bridge occurrence subject id is required")
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("bridge occurrence label is required")
        if not isinstance(self.detail, str):
            raise TypeError("bridge occurrence detail must be str")
        if self.navigation_kind not in _ALLOWED_NAVIGATION_KINDS:
            raise ValueError("bridge occurrence navigation kind is invalid")
        if self.navigation_kind == "document":
            if any(value is None for value in (self.line, self.start_offset, self.end_offset)):
                raise ValueError("document occurrence requires line and offsets")
            assert self.start_offset is not None and self.end_offset is not None
            assert self.line is not None
            if self.start_offset < 0 or self.end_offset <= self.start_offset:
                raise ValueError("document occurrence offsets are invalid")
            if self.line < 1:
                raise ValueError("document occurrence line must be one-based")
        elif self.navigation_kind == "source-note":
            if not self.source_note_id:
                raise ValueError("source-note occurrence requires source_note_id")
        elif not self.reference_key:
            raise ValueError("reference occurrence requires reference_key")


@dataclass(frozen=True)
class AuthoringBridgeProjection:
    document_text: str
    reference_subjects: tuple[BridgeSubject, ...]
    heading_subjects: tuple[BridgeSubject, ...]
    related_subjects: tuple[BridgeSubject, ...]
    occurrences: tuple[BridgeOccurrence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.document_text, str):
            raise TypeError("document_text must be str")
        object.__setattr__(self, "reference_subjects", tuple(self.reference_subjects))
        object.__setattr__(self, "heading_subjects", tuple(self.heading_subjects))
        object.__setattr__(self, "related_subjects", tuple(self.related_subjects))
        object.__setattr__(self, "occurrences", tuple(self.occurrences))
        ids = [item.id for item in self.occurrences]
        if len(ids) != len(set(ids)):
            raise ValueError("bridge occurrence identities must be unique")

    def subjects(self, mode: str) -> tuple[BridgeSubject, ...]:
        if mode == "reference":
            return self.reference_subjects
        if mode == "heading":
            return self.heading_subjects
        if mode == "related":
            return self.related_subjects
        if mode == "issues":
            return (BridgeSubject("issues", "broken-links", "Broken Research links"),)
        raise ValueError("bridge mode is invalid")

    def items(self, mode: str, subject_id: str) -> tuple[BridgeOccurrence, ...]:
        if mode not in {"reference", "heading", "related", "issues"}:
            raise ValueError("bridge mode is invalid")
        kind = "issues" if mode == "issues" else mode
        return tuple(
            item
            for item in self.occurrences
            if item.subject_kind == kind and item.subject_id == subject_id
        )

    def occurrence(self, occurrence_id: str) -> BridgeOccurrence | None:
        return next((item for item in self.occurrences if item.id == occurrence_id), None)


@dataclass(frozen=True)
class EditorSelectionSnapshot:
    """Immutable editor text and range captured before any modal dialog."""

    document_text: str
    start_offset: int
    end_offset: int

    def __post_init__(self) -> None:
        if not isinstance(self.document_text, str):
            raise TypeError("document_text must be str")
        for name in ("start_offset", "end_offset"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be int")
        if (
            self.start_offset < 0
            or self.end_offset < self.start_offset
            or self.end_offset > len(self.document_text)
        ):
            raise ValueError("editor selection range is invalid")

    @property
    def selected_text(self) -> str:
        return self.document_text[self.start_offset:self.end_offset]

    @property
    def has_selection(self) -> bool:
        return self.end_offset > self.start_offset


@dataclass(frozen=True)
class HeadingLinkPlan:
    document_before: str
    document_after: str
    replace_start: int
    replace_end: int
    replacement: str
    cursor_after: int
    identifier: str
    label: str

    @property
    def changed(self) -> bool:
        return self.document_before != self.document_after


def unique_heading_identifier_at_offset(
    structure: DocumentStructure,
    offset: int,
) -> str | None:
    """Return the unique explicit heading ID owning one document offset."""
    if not isinstance(structure, DocumentStructure):
        raise TypeError("structure must be DocumentStructure")
    heading = structure.current_heading(offset)
    if heading is None or heading.identifier is None:
        return None
    matches = structure.headings_for_identifier(heading.identifier)
    return heading.identifier if len(matches) == 1 else None


def parse_markdown_heading_links(text: str) -> tuple[MarkdownHeadingLink, ...]:
    """Return internal heading links outside fenced and inline Markdown code."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    excluded = _excluded_ranges(text)
    links: list[MarkdownHeadingLink] = []
    for match in _HEADING_LINK_RE.finditer(text):
        if _inside(excluded, match.start()):
            continue
        links.append(
            MarkdownHeadingLink(
                label=_unescape_link_label(match.group("label")),
                identifier=match.group("identifier"),
                start_offset=match.start(),
                end_offset=match.end(),
                line=_line_number(text, match.start()),
                raw=match.group(0),
            )
        )
    return tuple(links)


def _identity_owners(records: tuple[ReferenceRecord, ...]) -> dict[str, tuple[str, ...]]:
    owners: dict[str, list[str]] = {}
    for record in records:
        for identity in record.identity_keys:
            owners.setdefault(identity, []).append(record.key)
    return {key: tuple(dict.fromkeys(values)) for key, values in owners.items()}


def _resolve_reference(
    owners: dict[str, tuple[str, ...]],
    key: str,
) -> tuple[str, str | None]:
    requested = normalize_key(key)
    matches = owners.get(requested, ())
    if not matches:
        return "missing", None
    if len(matches) > 1:
        return "ambiguous", None
    return "resolved", matches[0]


def _reference_subject(record: ReferenceRecord) -> BridgeSubject:
    description = f"{record.key} — {record.author_year} — {record.title}"
    return BridgeSubject("reference", record.key, description)


def _heading_subject(identifier: str, title: str, line: int) -> BridgeSubject:
    return BridgeSubject("heading", identifier, f"{title} — #{identifier} — line {line}")


def _document_occurrence(
    *,
    occurrence_id: str,
    kind: str,
    subject_kind: str,
    subject_id: str,
    label: str,
    detail: str,
    text: str,
    start: int,
    end: int,
) -> BridgeOccurrence:
    return BridgeOccurrence(
        id=occurrence_id,
        kind=kind,
        subject_kind=subject_kind,
        subject_id=subject_id,
        label=label,
        detail=detail or _line_excerpt(text, start),
        navigation_kind="document",
        line=_line_number(text, start),
        start_offset=start,
        end_offset=end,
    )


def _source_note_occurrence(
    *,
    occurrence_id: str,
    kind: str,
    subject_kind: str,
    subject_id: str,
    label: str,
    detail: str,
    note: SourceNote,
) -> BridgeOccurrence:
    return BridgeOccurrence(
        id=occurrence_id,
        kind=kind,
        subject_kind=subject_kind,
        subject_id=subject_id,
        label=label,
        detail=detail,
        navigation_kind="source-note",
        source_note_id=note.id,
    )


def _reference_occurrence(
    *,
    occurrence_id: str,
    subject_id: str,
    record: ReferenceRecord,
) -> BridgeOccurrence:
    return BridgeOccurrence(
        id=occurrence_id,
        kind="related-reference",
        subject_kind="related",
        subject_id=subject_id,
        label=f"{record.key} — {record.author_year} — {record.title}",
        detail="Open the related Reference in the canonical library.",
        navigation_kind="reference",
        reference_key=record.key,
    )


def build_authoring_bridge_projection(
    records: Iterable[ReferenceRecord],
    document_text: str,
    source_notes: Iterable[SourceNote],
    structure: DocumentStructure,
) -> AuthoringBridgeProjection:
    """Build one deterministic, immutable projection from current authorities."""
    records_snapshot = tuple(records)
    notes_snapshot = tuple(source_notes)
    if any(not isinstance(record, ReferenceRecord) for record in records_snapshot):
        raise TypeError("records must contain ReferenceRecord values")
    if not isinstance(document_text, str):
        raise TypeError("document_text must be str")
    if any(not isinstance(note, SourceNote) for note in notes_snapshot):
        raise TypeError("source_notes must contain SourceNote values")
    if not isinstance(structure, DocumentStructure):
        raise TypeError("structure must be DocumentStructure")
    if structure.text_length != len(document_text):
        raise ValueError("document structure does not belong to the supplied text snapshot")

    owners = _identity_owners(records_snapshot)
    occurrences: list[BridgeOccurrence] = []
    reference_subjects = tuple(_reference_subject(record) for record in records_snapshot)
    related_subjects = tuple(
        BridgeSubject("related", record.key, f"{record.key} — {record.author_year} — {record.title}")
        for record in records_snapshot
    )
    records_by_key = {record.key: record for record in records_snapshot}

    unique_headings = []
    for heading in structure.headings:
        if heading.identifier is None:
            continue
        if len(structure.headings_for_identifier(heading.identifier)) != 1:
            continue
        unique_headings.append(heading)
    heading_subjects = tuple(
        _heading_subject(heading.identifier or "", heading.display_title, heading.line)
        for heading in unique_headings
    )

    for record in records_snapshot:
        for canonical in effective_related_keys(records_snapshot, record.key):
            occurrences.append(
                _reference_occurrence(
                    occurrence_id=f"related:{record.key}:{canonical}",
                    subject_id=record.key,
                    record=records_by_key[canonical],
                )
            )

    for cluster in parse_citation_clusters(document_text):
        for item in cluster.items:
            status, canonical = _resolve_reference(owners, item.key)
            if canonical is not None:
                occurrences.append(
                    _document_occurrence(
                        occurrence_id=f"citation:{canonical}:{cluster.start}:{item.start}",
                        kind="citation",
                        subject_kind="reference",
                        subject_id=canonical,
                        label=f"Citation @{item.key} — line {_line_number(document_text, cluster.start)}",
                        detail=_line_excerpt(document_text, cluster.start),
                        text=document_text,
                        start=cluster.start,
                        end=cluster.end,
                    )
                )
            else:
                occurrences.append(
                    _document_occurrence(
                        occurrence_id=f"broken-citation:{item.key}:{cluster.start}:{item.start}",
                        kind="broken-citation",
                        subject_kind="issues",
                        subject_id="broken-links",
                        label=f"{status.capitalize()} citation key @{item.key}",
                        detail=_line_excerpt(document_text, cluster.start),
                        text=document_text,
                        start=cluster.start,
                        end=cluster.end,
                    )
                )

    for link in parse_markdown_heading_links(document_text):
        matches = structure.headings_for_identifier(link.identifier)
        if len(matches) == 1:
            occurrences.append(
                _document_occurrence(
                    occurrence_id=f"heading-link:{link.identifier}:{link.start_offset}",
                    kind="heading-link",
                    subject_kind="heading",
                    subject_id=link.identifier,
                    label=f"Document link “{link.label}” — line {link.line}",
                    detail=_line_excerpt(document_text, link.start_offset),
                    text=document_text,
                    start=link.start_offset,
                    end=link.end_offset,
                )
            )
        else:
            state = "Missing" if not matches else "Ambiguous"
            occurrences.append(
                _document_occurrence(
                    occurrence_id=f"broken-heading-link:{link.identifier}:{link.start_offset}",
                    kind="broken-heading-link",
                    subject_kind="issues",
                    subject_id="broken-links",
                    label=f"{state} heading target #{link.identifier}",
                    detail=_line_excerpt(document_text, link.start_offset),
                    text=document_text,
                    start=link.start_offset,
                    end=link.end_offset,
                )
            )

    for note in notes_snapshot:
        if note.reference_key:
            status, canonical = _resolve_reference(owners, note.reference_key)
            if canonical is not None:
                occurrences.append(
                    _source_note_occurrence(
                        occurrence_id=f"source-note-reference:{canonical}:{note.id}",
                        kind="source-note-reference",
                        subject_kind="reference",
                        subject_id=canonical,
                        label=f"Source Note {note.id} — {note.kind.capitalize()}",
                        detail=note.excerpt,
                        note=note,
                    )
                )
            else:
                occurrences.append(
                    _source_note_occurrence(
                        occurrence_id=f"broken-source-note-reference:{note.id}",
                        kind="broken-source-note-reference",
                        subject_kind="issues",
                        subject_id="broken-links",
                        label=f"{status.capitalize()} Source Note reference {note.reference_key}",
                        detail=note.excerpt,
                        note=note,
                    )
                )
        if note.target:
            identifier = note.target[1:]
            matches = structure.headings_for_identifier(identifier)
            if len(matches) == 1:
                occurrences.append(
                    _source_note_occurrence(
                        occurrence_id=f"source-note-target:{identifier}:{note.id}",
                        kind="source-note-target",
                        subject_kind="heading",
                        subject_id=identifier,
                        label=f"Source Note {note.id} — {note.kind.capitalize()}",
                        detail=note.excerpt,
                        note=note,
                    )
                )
            else:
                state = "Missing" if not matches else "Ambiguous"
                occurrences.append(
                    _source_note_occurrence(
                        occurrence_id=f"broken-source-note-target:{note.id}",
                        kind="broken-source-note-target",
                        subject_kind="issues",
                        subject_id="broken-links",
                        label=f"{state} Source Note target {note.target}",
                        detail=note.excerpt,
                        note=note,
                    )
                )

    for diagnostic in structure.diagnostics:
        identifier = diagnostic.identifier or "heading-id"
        start = min(diagnostic.start_offset, max(0, len(document_text) - 1))
        end = min(len(document_text), max(start + 1, start + len(identifier)))
        if not document_text:
            # No diagnostic can validly exist for an empty structure, but keep
            # the gate explicit if a foreign provider violates that invariant.
            raise ValueError("document diagnostics require non-empty text")
        occurrences.append(
            _document_occurrence(
                occurrence_id=f"heading-diagnostic:{diagnostic.kind}:{diagnostic.line}:{diagnostic.start_offset}",
                kind="heading-diagnostic",
                subject_kind="issues",
                subject_id="broken-links",
                label=diagnostic.message,
                detail=_line_excerpt(document_text, diagnostic.start_offset),
                text=document_text,
                start=start,
                end=end,
            )
        )

    kind_order = {
        "citation": 0,
        "heading-link": 0,
        "source-note-reference": 1,
        "source-note-target": 1,
        "broken-citation": 0,
        "broken-heading-link": 1,
        "heading-diagnostic": 2,
        "broken-source-note-reference": 3,
        "broken-source-note-target": 4,
        "related-reference": 0,
    }
    occurrences.sort(
        key=lambda item: (
            item.subject_kind,
            item.subject_id.casefold(),
            kind_order[item.kind],
            item.start_offset if item.start_offset is not None else 10**18,
            item.source_note_id,
            item.id,
        )
    )
    return AuthoringBridgeProjection(
        document_text=document_text,
        reference_subjects=reference_subjects,
        heading_subjects=heading_subjects,
        related_subjects=related_subjects,
        occurrences=tuple(occurrences),
    )


def format_heading_link(label: str, identifier: str) -> str:
    if not isinstance(label, str):
        raise TypeError("link label must be str")
    compact = label.strip()
    if not compact:
        raise ValueError("Heading link label cannot be empty.")
    if "\n" in compact or "\r" in compact:
        raise ValueError("Heading link label must stay on one line.")
    target = identifier[1:] if isinstance(identifier, str) and identifier.startswith("#") else identifier
    if not isinstance(target, str) or not is_valid_heading_identifier(target):
        raise ValueError("Heading link target is invalid.")
    return f"[{_escape_link_label(compact)}](#{target})"


def plan_heading_link_insertion(
    document_text: str,
    replace_start: int,
    replace_end: int,
    identifier: str,
    label: str,
    structure: DocumentStructure,
) -> HeadingLinkPlan:
    """Plan one link insertion/replacement against the exact document snapshot."""
    if not isinstance(document_text, str):
        raise TypeError("document_text must be str")
    for name, value in (("replace_start", replace_start), ("replace_end", replace_end)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be int")
    if replace_start < 0 or replace_end < replace_start or replace_end > len(document_text):
        raise ValueError("Heading link replacement range is invalid.")
    if not isinstance(structure, DocumentStructure):
        raise TypeError("structure must be DocumentStructure")
    if structure.text_length != len(document_text):
        raise ValueError("Document changed before heading link insertion. Refresh and retry.")
    target = identifier[1:] if isinstance(identifier, str) and identifier.startswith("#") else identifier
    if not isinstance(target, str) or not is_valid_heading_identifier(target):
        raise ValueError("Heading link target is invalid.")
    matches = structure.headings_for_identifier(target)
    if len(matches) != 1:
        state = "missing" if not matches else "ambiguous"
        raise ValueError(f"Heading link target is {state}: #{target}")
    replacement = format_heading_link(label, target)
    document_after = document_text[:replace_start] + replacement + document_text[replace_end:]
    return HeadingLinkPlan(
        document_before=document_text,
        document_after=document_after,
        replace_start=replace_start,
        replace_end=replace_end,
        replacement=replacement,
        cursor_after=replace_start + len(replacement),
        identifier=target,
        label=label.strip(),
    )
