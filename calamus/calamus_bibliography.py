"""GTK-free Bibliography Manager projections and guarded operations.

The canonical authority remains ``references.md``.  This module owns only
rebuildable search/filter/sort/detail projections and immutable operation plans.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import os
from typing import Iterable, Mapping

from calamus_citations import parse_citation_clusters
from calamus_related_references import related_keys
from calamus_references import ReferenceRecord, suggest_reference_key


_SORTS = ("author-year-title", "title", "year", "key", "type")


@dataclass(frozen=True)
class BibliographyFilters:
    query: str = ""
    reference_type: str = "all"
    tag: str = "all"
    use: str = "all"
    file: str = "all"
    integrity: str = "all"
    sort: str = "author-year-title"

    def __post_init__(self) -> None:
        if self.use not in {"all", "cited", "source-notes", "unused"}:
            raise ValueError("bibliography use filter is invalid")
        if self.file not in {"all", "present", "missing", "unset"}:
            raise ValueError("bibliography file filter is invalid")
        if self.integrity not in {"all", "error", "warning", "advisory", "clean"}:
            raise ValueError("bibliography integrity filter is invalid")
        if self.sort not in _SORTS:
            raise ValueError("bibliography sort is invalid")


@dataclass(frozen=True)
class BibliographyContext:
    cited_keys: frozenset[str] = frozenset()
    source_note_keys: frozenset[str] = frozenset()
    set_names_by_key: tuple[tuple[str, tuple[str, ...]], ...] = ()
    issue_severities_by_key: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @property
    def used_keys(self) -> frozenset[str]:
        return self.cited_keys | self.source_note_keys

    def set_names(self, key: str) -> tuple[str, ...]:
        return dict(self.set_names_by_key).get(key, ())

    def severities(self, key: str) -> tuple[str, ...]:
        return dict(self.issue_severities_by_key).get(key, ())


@dataclass(frozen=True)
class ReferenceDeleteImpact:
    key: str
    citation_occurrences: int = 0
    source_note_occurrences: int = 0
    related_reference_owners: tuple[str, ...] = ()
    reference_set_names: tuple[str, ...] = ()

    @property
    def used(self) -> bool:
        return bool(
            self.citation_occurrences
            or self.source_note_occurrences
            or self.related_reference_owners
            or self.reference_set_names
        )

    @property
    def summary_lines(self) -> tuple[str, ...]:
        lines: list[str] = []
        if self.citation_occurrences:
            lines.append(f"Document citations: {self.citation_occurrences}")
        if self.source_note_occurrences:
            lines.append(f"Source Notes: {self.source_note_occurrences}")
        if self.related_reference_owners:
            lines.append("Related from: " + ", ".join(self.related_reference_owners))
        if self.reference_set_names:
            lines.append("Reference Sets: " + ", ".join(self.reference_set_names))
        return tuple(lines)


def complete_search_text(record: ReferenceRecord) -> str:
    if not isinstance(record, ReferenceRecord):
        raise TypeError("record must be ReferenceRecord")
    values = (
        "key", record.key, "aliases", *record.aliases, "title", record.title,
        "type", record.type, "year", record.year, "author", *record.authors,
        "editor", *record.editors, "container", record.container_title,
        "publisher", record.publisher, "location", record.location,
        "volume", record.volume, "issue", record.issue, "pages", record.pages,
        "doi", record.doi, "isbn", record.isbn, "issn", record.issn,
        "url", record.url, "language", record.language, "file", record.file_path,
        "tags", *record.tags, "annotation", record.annotation,
        *(item for pair in record.extra_fields for item in pair),
    )
    return "\n".join(values).casefold()


def available_types(records: Iterable[ReferenceRecord]) -> tuple[str, ...]:
    return tuple(sorted({record.type for record in records}, key=str.casefold))


def available_tags(records: Iterable[ReferenceRecord]) -> tuple[str, ...]:
    display: dict[str, str] = {}
    for record in records:
        for tag in record.tags:
            display.setdefault(tag.casefold(), tag)
    return tuple(display[key] for key in sorted(display))


def _file_state(record: ReferenceRecord) -> str:
    if not record.file_path:
        return "unset"
    return "present" if os.path.exists(os.path.expanduser(record.file_path)) else "missing"


def project_references(
    records: Iterable[ReferenceRecord],
    filters: BibliographyFilters = BibliographyFilters(),
    context: BibliographyContext = BibliographyContext(),
) -> tuple[ReferenceRecord, ...]:
    snapshot = tuple(records)
    if any(not isinstance(record, ReferenceRecord) for record in snapshot):
        raise TypeError("records must contain ReferenceRecord values")
    needle = filters.query.strip().casefold()
    visible: list[ReferenceRecord] = []
    for record in snapshot:
        if needle and needle not in complete_search_text(record):
            continue
        if filters.reference_type != "all" and record.type != filters.reference_type:
            continue
        if filters.tag != "all" and filters.tag.casefold() not in {tag.casefold() for tag in record.tags}:
            continue
        if filters.use == "cited" and record.key not in context.cited_keys:
            continue
        if filters.use == "source-notes" and record.key not in context.source_note_keys:
            continue
        if filters.use == "unused" and record.key in context.used_keys:
            continue
        if filters.file != "all" and _file_state(record) != filters.file:
            continue
        severities = set(context.severities(record.key))
        if filters.integrity == "clean" and severities:
            continue
        if filters.integrity not in {"all", "clean"} and filters.integrity not in severities:
            continue
        visible.append(record)

    def sortable(value: str) -> tuple[int, str]:
        folded = value.strip().casefold()
        return (0, folded) if folded else (1, "")

    def key(record: ReferenceRecord):
        if filters.sort == "title":
            return (sortable(record.title), sortable(record.key))
        if filters.sort == "year":
            return (sortable(record.year), sortable(record.primary_author), sortable(record.title), sortable(record.key))
        if filters.sort == "key":
            return (sortable(record.key),)
        if filters.sort == "type":
            return (sortable(record.type), sortable(record.primary_author), sortable(record.title), sortable(record.key))
        return (sortable(record.primary_author), sortable(record.year), sortable(record.title), sortable(record.key))

    return tuple(sorted(visible, key=key))


def duplicate_reference(record: ReferenceRecord, existing_identity_keys: Iterable[str]) -> ReferenceRecord:
    if not isinstance(record, ReferenceRecord):
        raise TypeError("record must be ReferenceRecord")
    key = suggest_reference_key(record.authors, record.year, record.title, existing_identity_keys)
    return replace(record, key=key, aliases=())


def build_delete_impact(
    records: Iterable[ReferenceRecord],
    key: str,
    *,
    document_text: str = "",
    source_notes: Iterable[object] = (),
    reference_sets: Iterable[object] = (),
) -> ReferenceDeleteImpact:
    snapshot = tuple(records)
    target = next((record for record in snapshot if record.key == key), None)
    if target is None:
        raise ValueError("reference is not available")
    identities = set(target.identity_keys)
    citation_count = sum(
        1
        for cluster in parse_citation_clusters(document_text if isinstance(document_text, str) else "")
        for item in cluster.items
        if item.key in identities
    )
    note_count = sum(
        1 for note in source_notes
        if getattr(note, "reference_key", "") in identities
    )
    related_owners = tuple(
        record.key for record in snapshot
        if record.key != key and identities.intersection(related_keys(record))
    )
    set_names = tuple(
        getattr(item, "name", "") for item in reference_sets
        if identities.intersection(getattr(item, "members", ()))
    )
    return ReferenceDeleteImpact(
        key=key,
        citation_occurrences=citation_count,
        source_note_occurrences=note_count,
        related_reference_owners=related_owners,
        reference_set_names=tuple(name for name in set_names if name),
    )


def format_reference_detail(record: ReferenceRecord, context: BibliographyContext) -> str:
    fields: list[tuple[str, str]] = [
        ("Key", record.key),
        ("Aliases", ", ".join(record.aliases)),
        ("Type", record.type),
        ("Author", "; ".join(record.authors)),
        ("Editor", "; ".join(record.editors)),
        ("Title", record.title),
        ("Year / Date", record.year),
        ("Container", record.container_title),
        ("Publisher", record.publisher),
        ("Location", record.location),
        ("Volume", record.volume),
        ("Issue", record.issue),
        ("Pages", record.pages),
        ("DOI", record.doi),
        ("ISBN", record.isbn),
        ("ISSN", record.issn),
        ("URL", record.url),
        ("Language", record.language),
        ("Tags", ", ".join(record.tags)),
        ("Local File", record.file_path),
        ("File Status", _file_state(record)),
        ("Related", ", ".join(related_keys(record))),
        ("Reference Sets", ", ".join(context.set_names(record.key))),
        ("Current Document", "cited" if record.key in context.cited_keys else "not cited"),
        ("Source Notes", "used" if record.key in context.source_note_keys else "not used"),
        ("Integrity", ", ".join(context.severities(record.key)) or "clean"),
    ]
    fields.extend(record.extra_fields)
    body = "\n".join(f"{label}: {value}" for label, value in fields if value)
    if record.annotation:
        body += "\n\nAnnotation\n" + record.annotation
    return body


def render_plain_bibliography(records: Iterable[ReferenceRecord]) -> str:
    lines: list[str] = []
    for record in records:
        author = "; ".join(record.authors) or "Unknown author"
        year = f" ({record.year})" if record.year else ""
        publication = ". ".join(value for value in (record.location, record.publisher) if value)
        line = f"{author}{year}. {record.title}."
        if publication:
            line += f" {publication}."
        lines.append(line)
    return "\n".join(lines) + ("\n" if lines else "")


def render_markdown_bibliography(records: Iterable[ReferenceRecord]) -> str:
    plain = render_plain_bibliography(records).splitlines()
    return "# Bibliography\n\n" + "\n".join(f"- {line}" for line in plain) + ("\n" if plain else "")


def build_bibliography_context(
    records: Iterable[ReferenceRecord],
    *,
    document_text: str = "",
    source_notes: Iterable[object] = (),
    reference_sets: Iterable[object] = (),
) -> BibliographyContext:
    snapshot = tuple(records)
    owners: dict[str, str] = {}
    for record in snapshot:
        for identity in record.identity_keys:
            if identity not in owners:
                owners[identity] = record.key
    cited = {
        owners[item.key]
        for cluster in parse_citation_clusters(document_text if isinstance(document_text, str) else "")
        for item in cluster.items
        if item.key in owners
    }
    note_keys = {
        owners[getattr(note, "reference_key", "")]
        for note in source_notes
        if getattr(note, "reference_key", "") in owners
    }
    sets_by_key: dict[str, list[str]] = {record.key: [] for record in snapshot}
    for item in reference_sets:
        name = getattr(item, "name", "")
        for identity in getattr(item, "members", ()):
            canonical = owners.get(identity)
            if canonical and name and name not in sets_by_key[canonical]:
                sets_by_key[canonical].append(name)

    identifiers: dict[tuple[str, str], list[str]] = {}
    for record in snapshot:
        for kind, value in (("doi", record.doi), ("isbn", record.isbn), ("issn", record.issn)):
            normalized = "".join(char for char in value.casefold() if char.isalnum())
            if normalized:
                identifiers.setdefault((kind, normalized), []).append(record.key)

    severities: dict[str, set[str]] = {record.key: set() for record in snapshot}
    used = cited | note_keys
    for record in snapshot:
        if not record.authors or not record.year:
            severities[record.key].add("warning")
        if record.file_path and not os.path.exists(os.path.expanduser(record.file_path)):
            severities[record.key].add("warning")
        if record.key not in used:
            severities[record.key].add("advisory")
        if not record.tags or not any((record.doi, record.isbn, record.issn, record.url)):
            severities[record.key].add("advisory")
        for kind, value in (("doi", record.doi), ("isbn", record.isbn), ("issn", record.issn)):
            normalized = "".join(char for char in value.casefold() if char.isalnum())
            if normalized and len(identifiers.get((kind, normalized), ())) > 1:
                severities[record.key].add("error")
    return BibliographyContext(
        cited_keys=frozenset(cited),
        source_note_keys=frozenset(note_keys),
        set_names_by_key=tuple((key, tuple(values)) for key, values in sets_by_key.items()),
        issue_severities_by_key=tuple((key, tuple(sorted(values))) for key, values in severities.items()),
    )
