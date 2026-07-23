"""Pure reference-key migration and on-demand Research integrity checks.

This module never owns persistent state.  It derives one migration plan or one
report from the current References snapshot, active document text, current
Source Notes sidecar and canonical document structure.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Iterable

from calamus_citations import CitationCluster, CitationItem, parse_citation_clusters
from calamus_document_structure import DocumentStructure
from calamus_references import ReferenceRecord, is_valid_reference_key, normalize_key
from calamus_source_notes import SourceNote


@dataclass(frozen=True)
class ReferenceResolution:
    requested_key: str
    canonical_key: str | None
    status: str

    def __post_init__(self) -> None:
        if self.status not in {"missing", "primary", "alias", "ambiguous"}:
            raise ValueError("reference resolution status is invalid")


@dataclass(frozen=True)
class ReferenceMigrationImpact:
    old_key: str
    new_key: str
    citation_occurrences: int
    source_note_occurrences: int
    related_key_occurrences: int = 0
    preserved_alias: bool = True

    @property
    def total_rewrites(self) -> int:
        return self.citation_occurrences + self.source_note_occurrences + self.related_key_occurrences


@dataclass(frozen=True)
class ReferenceMigrationPlan:
    original_records: tuple[ReferenceRecord, ...]
    candidate_records: tuple[ReferenceRecord, ...]
    document_before: str
    document_after: str
    source_notes_before: tuple[SourceNote, ...]
    source_notes_after: tuple[SourceNote, ...]
    impact: ReferenceMigrationImpact

    @property
    def document_changed(self) -> bool:
        return self.document_before != self.document_after

    @property
    def source_notes_changed(self) -> bool:
        return self.source_notes_before != self.source_notes_after


@dataclass(frozen=True, order=True)
class ResearchIssue:
    severity: str
    kind: str
    subject: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in {"error", "warning", "advisory"}:
            raise ValueError("research issue severity is invalid")
        if not all(isinstance(value, str) and value for value in (self.kind, self.subject, self.message)):
            raise ValueError("research issue fields must be non-empty strings")


@dataclass(frozen=True)
class ResearchCheckReport:
    issues: tuple[ResearchIssue, ...]
    reference_count: int
    citation_count: int
    source_note_count: int

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

    @property
    def advisory_count(self) -> int:
        return sum(issue.severity == "advisory" for issue in self.issues)

    @property
    def clean(self) -> bool:
        return not self.issues


def build_identity_index(records: Iterable[ReferenceRecord]) -> dict[str, str]:
    """Map primary keys and aliases to one canonical key, rejecting collisions."""
    index: dict[str, str] = {}
    for record in records:
        if not isinstance(record, ReferenceRecord):
            raise TypeError("records must contain ReferenceRecord values")
        for identity in record.identity_keys:
            owner = index.get(identity)
            if owner is not None and owner != record.key:
                raise ValueError(
                    f"Reference identity {identity} belongs to both {owner} and {record.key}."
                )
            index[identity] = record.key
    return index


def resolve_reference(records: Iterable[ReferenceRecord], key: str) -> ReferenceResolution:
    requested = normalize_key(key)
    matches = [record for record in records if requested in record.identity_keys]
    if not requested or not matches:
        return ReferenceResolution(requested, None, "missing")
    if len(matches) > 1:
        return ReferenceResolution(requested, None, "ambiguous")
    record = matches[0]
    return ReferenceResolution(
        requested,
        record.key,
        "primary" if requested == record.key else "alias",
    )


def _replace_citation_items(text: str, old_key: str, new_key: str) -> tuple[str, int]:
    items = [
        item
        for cluster in parse_citation_clusters(text)
        for item in cluster.items
        if item.key == old_key
    ]
    updated = text
    for item in reversed(items):
        updated = updated[: item.start] + new_key + updated[item.end :]
    return updated, len(items)


def _related_keys(record: ReferenceRecord) -> tuple[str, ...]:
    values: list[str] = []
    for label, value in record.extra_fields:
        if label.casefold() not in {"related", "related key", "related keys"}:
            continue
        for key in re.split(r"[,;\s]+", value):
            key = normalize_key(key)
            if key and key not in values:
                values.append(key)
    return tuple(values)


def _replace_related_key(record: ReferenceRecord, old_key: str, new_key: str) -> tuple[ReferenceRecord, int]:
    count = 0
    extras: list[tuple[str, str]] = []
    for label, value in record.extra_fields:
        if label.casefold() not in {"related", "related key", "related keys"}:
            extras.append((label, value))
            continue
        tokens = re.split(r"([,;\s]+)", value)
        for index, token in enumerate(tokens):
            if normalize_key(token) == old_key:
                tokens[index] = new_key
                count += 1
        extras.append((label, "".join(tokens)))
    return replace(record, extra_fields=tuple(extras)), count


def plan_reference_key_migration(
    records: Iterable[ReferenceRecord],
    document_text: str,
    source_notes: Iterable[SourceNote],
    old_key: str,
    new_key: str,
    *,
    preserve_old_alias: bool = True,
) -> ReferenceMigrationPlan:
    records_before = tuple(records)
    notes_before = tuple(source_notes)
    if not isinstance(document_text, str):
        raise TypeError("document_text must be a string")
    old = normalize_key(old_key)
    new = normalize_key(new_key)
    if not is_valid_reference_key(old):
        raise ValueError("existing reference key is invalid")
    if not is_valid_reference_key(new):
        raise ValueError("new reference key is invalid")
    if old == new:
        raise ValueError("new reference key must differ from the existing key")

    build_identity_index(records_before)
    matching = [record for record in records_before if record.key == old]
    if len(matching) != 1:
        raise ValueError(f"Primary reference key is not uniquely available: {old}")
    target = matching[0]
    for record in records_before:
        if record.key != old and new in record.identity_keys:
            raise ValueError(f"Reference identity already exists: {new}")

    renamed = target.with_key(new, preserve_old_alias=preserve_old_alias)
    candidate_records: list[ReferenceRecord] = []
    related_count = 0
    for record in records_before:
        current = renamed if record.key == old else record
        current, changed = _replace_related_key(current, old, new)
        related_count += changed
        candidate_records.append(current)
    build_identity_index(candidate_records)

    document_after, citation_count = _replace_citation_items(document_text, old, new)
    notes_after: list[SourceNote] = []
    note_count = 0
    for note in notes_before:
        if not isinstance(note, SourceNote):
            raise TypeError("source_notes must contain SourceNote values")
        if note.reference_key == old:
            notes_after.append(replace(note, reference_key=new))
            note_count += 1
        else:
            notes_after.append(note)

    return ReferenceMigrationPlan(
        original_records=records_before,
        candidate_records=tuple(candidate_records),
        document_before=document_text,
        document_after=document_after,
        source_notes_before=notes_before,
        source_notes_after=tuple(notes_after),
        impact=ReferenceMigrationImpact(
            old_key=old,
            new_key=new,
            citation_occurrences=citation_count,
            source_note_occurrences=note_count,
            related_key_occurrences=related_count,
            preserved_alias=preserve_old_alias,
        ),
    )


def _normalize_identifier(value: str, kind: str) -> str:
    compact = value.strip().casefold()
    if kind == "doi":
        compact = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", compact)
    elif kind in {"isbn", "issn"}:
        compact = re.sub(r"[^0-9x]", "", compact)
    return compact


def _citation_segment_has_locator(text: str, cluster: CitationCluster, item: CitationItem) -> bool:
    end = cluster.end - (1 if cluster.bracketed else 0)
    following_item_starts = [other.start - 1 for other in cluster.items if other.start > item.start]
    if following_item_starts:
        end = min(end, min(following_item_starts))
    suffix = text[item.end:end].strip()
    suffix = suffix.lstrip(",").strip().rstrip(";").strip()
    return bool(suffix)


def run_research_check(
    records: Iterable[ReferenceRecord],
    document_text: str,
    source_notes: Iterable[SourceNote],
    document_structure: DocumentStructure,
) -> ResearchCheckReport:
    records_tuple = tuple(records)
    notes_tuple = tuple(source_notes)
    if not isinstance(document_text, str):
        raise TypeError("document_text must be a string")
    if not isinstance(document_structure, DocumentStructure):
        raise TypeError("document_structure must be DocumentStructure")
    issues: list[ResearchIssue] = []

    try:
        identity_index = build_identity_index(records_tuple)
    except ValueError as error:
        identity_index = {}
        issues.append(ResearchIssue("error", "identity-collision", "References", str(error)))

    clusters = parse_citation_clusters(document_text)
    cited_canonical: set[str] = set()
    for cluster in clusters:
        for item in cluster.items:
            resolution = resolve_reference(records_tuple, item.key)
            if resolution.status in {"missing", "ambiguous"}:
                issues.append(
                    ResearchIssue(
                        "error",
                        "cited-key-missing",
                        item.key,
                        f"Citation key is not uniquely available in References: {item.key}.",
                    )
                )
                continue
            assert resolution.canonical_key is not None
            cited_canonical.add(resolution.canonical_key)
            if resolution.status == "alias":
                issues.append(
                    ResearchIssue(
                        "warning",
                        "citation-uses-alias",
                        item.key,
                        f"Citation should migrate from alias {item.key} to {resolution.canonical_key}.",
                    )
                )
            if not _citation_segment_has_locator(document_text, cluster, item):
                issues.append(
                    ResearchIssue(
                        "advisory",
                        "citation-without-locator",
                        item.key,
                        "Citation has no locator; verify whether a page or section is needed.",
                    )
                )

    identifier_owners: dict[tuple[str, str], list[str]] = {}
    for record in records_tuple:
        missing = []
        if not record.authors:
            missing.append("author")
        if not record.year:
            missing.append("year/date")
        if missing:
            issues.append(
                ResearchIssue(
                    "advisory",
                    "incomplete-reference",
                    record.key,
                    "Reference is missing " + " and ".join(missing) + ".",
                )
            )
        for kind in ("doi", "isbn", "issn"):
            raw = getattr(record, kind)
            normalized = _normalize_identifier(raw, kind)
            if normalized:
                identifier_owners.setdefault((kind, normalized), []).append(record.key)
        for related in _related_keys(record):
            resolution = resolve_reference(records_tuple, related)
            if resolution.status in {"missing", "ambiguous"}:
                issues.append(
                    ResearchIssue(
                        "warning",
                        "related-key-missing",
                        record.key,
                        f"Related reference key is unavailable: {related}.",
                    )
                )
            elif resolution.status == "alias":
                issues.append(
                    ResearchIssue(
                        "warning",
                        "related-key-uses-alias",
                        record.key,
                        f"Related key should migrate from {related} to {resolution.canonical_key}.",
                    )
                )

    for (kind, value), owners in sorted(identifier_owners.items()):
        unique = tuple(dict.fromkeys(owners))
        if len(unique) > 1:
            issues.append(
                ResearchIssue(
                    "warning",
                    f"duplicate-{kind}",
                    value,
                    f"{kind.upper()} is shared by: {', '.join(unique)}.",
                )
            )

    used_by_notes: set[str] = set()
    for note in notes_tuple:
        if not isinstance(note, SourceNote):
            raise TypeError("source_notes must contain SourceNote values")
        if note.reference_key:
            resolution = resolve_reference(records_tuple, note.reference_key)
            if resolution.status in {"missing", "ambiguous"}:
                issues.append(
                    ResearchIssue(
                        "error",
                        "source-note-reference-missing",
                        note.id,
                        f"Source Note points to unavailable reference key: {note.reference_key}.",
                    )
                )
            else:
                assert resolution.canonical_key is not None
                used_by_notes.add(resolution.canonical_key)
                if resolution.status == "alias":
                    issues.append(
                        ResearchIssue(
                            "warning",
                            "source-note-uses-alias",
                            note.id,
                            f"Source Note should migrate from {note.reference_key} to {resolution.canonical_key}.",
                        )
                    )
        if note.target:
            try:
                matches = document_structure.headings_for_identifier(note.target)
            except ValueError:
                matches = ()
            if not matches:
                issues.append(
                    ResearchIssue(
                        "warning",
                        "source-note-target-missing",
                        note.id,
                        f"Source Note heading target is missing: {note.target}.",
                    )
                )
            elif len(matches) > 1:
                issues.append(
                    ResearchIssue(
                        "warning",
                        "source-note-target-ambiguous",
                        note.id,
                        f"Source Note heading target is ambiguous: {note.target}.",
                    )
                )
        if note.kind in {"quote", "paraphrase"} and not note.locator.display:
            issues.append(
                ResearchIssue(
                    "advisory",
                    "source-note-without-locator",
                    note.id,
                    f"{note.kind.title()} Source Note has no locator.",
                )
            )

    used = cited_canonical | used_by_notes
    for record in records_tuple:
        if record.key not in used:
            issues.append(
                ResearchIssue(
                    "advisory",
                    "reference-unused",
                    record.key,
                    "Reference is not cited and is not linked by the current Source Notes sidecar.",
                )
            )

    for diagnostic in document_structure.diagnostics:
        issues.append(
            ResearchIssue(
                "warning",
                "document-structure-diagnostic",
                f"line {diagnostic.line}",
                diagnostic.message,
            )
        )

    # Deterministic order and de-duplication make reports stable and testable.
    unique = tuple(sorted(set(issues), key=lambda issue: (
        {"error": 0, "warning": 1, "advisory": 2}[issue.severity],
        issue.kind,
        issue.subject,
        issue.message,
    )))
    return ResearchCheckReport(
        unique,
        reference_count=len(records_tuple),
        citation_count=sum(len(cluster.items) for cluster in clusters),
        source_note_count=len(notes_tuple),
    )
