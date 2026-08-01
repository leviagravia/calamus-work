"""GTK-free Document Dossier projection for Calamus W96 Core.

The dossier is a derived, immutable view of the current editor buffer and the
already-owned Research authorities.  It never persists a parallel document,
reference classification, outline, or integrity report.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from typing import Iterable

from calamus_authoring_bridge import MarkdownHeadingLink, parse_markdown_heading_links
from calamus_citations import CitationCluster, parse_citation_clusters
from calamus_document_structure import DocumentHeading, DocumentStructure, build_document_structure
from calamus_reference_integrity import ResearchCheckReport, ResearchIssue, resolve_reference, run_research_check
from calamus_reference_set_store import ReferenceSetSnapshot
from calamus_reference_sets import ReferenceSet
from calamus_reference_store import ReferenceLibrarySnapshot
from calamus_references import ReferenceRecord, normalize_key
from calamus_related_references import effective_related_keys
from calamus_research_file import FileToken
from calamus_source_note_store import SourceNoteSnapshot
from calamus_source_notes import SourceNote
from calamus_writing import document_statistics

_REFERENCE_ROLES = frozenset(
    {"cited", "source-note", "related", "reference-set", "collected-unused", "missing"}
)
_REFERENCE_STATUSES = frozenset({"resolved", "missing", "ambiguous"})
_NOTE_STATUSES = frozenset({"complete", "incomplete", "orphan"})
_LINK_STATUSES = frozenset({"resolved", "missing", "ambiguous"})


def _tuple(value: Iterable[object] | tuple[object, ...]) -> tuple[object, ...]:
    return value if isinstance(value, tuple) else tuple(value)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _line_for_offset(text: str, offset: int) -> int:
    safe = max(0, min(int(offset), len(text)))
    return text.count("\n", 0, safe) + 1


def _section_identifier(heading: DocumentHeading | None) -> str:
    if heading is None:
        return ""
    if heading.identifier:
        return heading.identifier
    return f"line-{heading.line}"


def _section_for_offset(structure: DocumentStructure, offset: int) -> DocumentHeading | None:
    heading = structure.current_heading(offset)
    if heading is None:
        return None
    if offset >= heading.section_end_offset:
        return None
    return heading


def _section_excerpt(text: str, heading: DocumentHeading, *, limit: int = 180) -> str:
    body = text[heading.start_offset:heading.section_end_offset]
    lines = body.splitlines()
    if lines:
        lines = lines[1:]
    compact = " ".join(line.strip() for line in lines if line.strip())
    if len(compact) <= limit:
        return compact
    return compact[: max(0, limit - 1)].rstrip() + "…"


@dataclass(frozen=True)
class DocumentDossierIdentity:
    name: str
    path: str = ""
    modified: bool = False
    untitled: bool = False

    def __post_init__(self) -> None:
        name = self.name.strip() if isinstance(self.name, str) else ""
        path = self.path.strip() if isinstance(self.path, str) else ""
        if not name:
            raise ValueError("document dossier identity requires a name")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "modified", bool(self.modified))
        object.__setattr__(self, "untitled", bool(self.untitled))


@dataclass(frozen=True)
class DocumentDossierAuthorityStamp:
    document_path: str
    buffer_digest: str
    modified: bool
    document_token: FileToken = field(default_factory=lambda: FileToken(False))
    source_notes_token: FileToken = field(default_factory=lambda: FileToken(False))
    references_token: FileToken = field(default_factory=lambda: FileToken(False))
    reference_sets_token: FileToken = field(default_factory=lambda: FileToken(False))

    def __post_init__(self) -> None:
        if not isinstance(self.document_path, str):
            raise TypeError("document_path must be str")
        if not isinstance(self.buffer_digest, str) or len(self.buffer_digest) != 64:
            raise ValueError("buffer_digest must be a SHA-256 hex digest")
        for character in self.buffer_digest:
            if character not in "0123456789abcdef":
                raise ValueError("buffer_digest must be lowercase hexadecimal")
        object.__setattr__(self, "modified", bool(self.modified))
        for name in (
            "document_token",
            "source_notes_token",
            "references_token",
            "reference_sets_token",
        ):
            if not isinstance(getattr(self, name), FileToken):
                raise TypeError(f"{name} must be FileToken")


@dataclass(frozen=True)
class DocumentDossierCapabilities:
    can_navigate_document: bool = True
    can_use_source_notes: bool = False
    can_open_references: bool = True
    can_open_reference_sets: bool = True
    can_run_research_check: bool = True


@dataclass(frozen=True)
class DocumentDossierSection:
    id: str
    level: int
    title: str
    line: int
    start_offset: int
    end_offset: int
    excerpt: str = ""
    word_count: int = 0
    citation_count: int = 0
    source_note_count: int = 0
    bookmark_count: int = 0
    incoming_link_count: int = 0
    outgoing_link_count: int = 0

    def __post_init__(self) -> None:
        if not self.id or not self.title:
            raise ValueError("section id and title are required")
        if not 1 <= self.level <= 6:
            raise ValueError("section level must be between 1 and 6")
        if self.line < 1 or self.start_offset < 0 or self.end_offset < self.start_offset:
            raise ValueError("section coordinates are invalid")
        for name in (
            "word_count",
            "citation_count",
            "source_note_count",
            "bookmark_count",
            "incoming_link_count",
            "outgoing_link_count",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")


@dataclass(frozen=True)
class DocumentDossierBookmark:
    id: str
    offset: int
    line: int
    section_id: str = ""
    label: str = ""

    def __post_init__(self) -> None:
        if not self.id or self.offset < 0 or self.line < 1:
            raise ValueError("bookmark identity or coordinates are invalid")


@dataclass(frozen=True)
class DocumentDossierLink:
    id: str
    label: str
    identifier: str
    line: int
    start_offset: int
    end_offset: int
    source_section_id: str
    status: str
    destination_section_id: str = ""
    destination_line: int | None = None

    def __post_init__(self) -> None:
        if not self.id or not self.label or not self.identifier:
            raise ValueError("link identity, label and identifier are required")
        if self.status not in _LINK_STATUSES:
            raise ValueError("link status is invalid")
        if self.line < 1 or self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise ValueError("link coordinates are invalid")
        if self.destination_line is not None and self.destination_line < 1:
            raise ValueError("destination line must be one-based")


@dataclass(frozen=True)
class DocumentDossierCitation:
    id: str
    raw: str
    line: int
    start_offset: int
    end_offset: int
    requested_keys: tuple[str, ...]
    canonical_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]
    ambiguous_keys: tuple[str, ...]
    section_id: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.raw:
            raise ValueError("citation identity and raw text are required")
        if self.line < 1 or self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise ValueError("citation coordinates are invalid")
        for name in ("requested_keys", "canonical_keys", "missing_keys", "ambiguous_keys"):
            object.__setattr__(self, name, tuple(getattr(self, name)))


@dataclass(frozen=True)
class DocumentDossierSourceNote:
    id: str
    kind: str
    excerpt: str
    reference_key: str
    canonical_reference_key: str
    locator: str
    target: str
    section_id: str
    status: str

    def __post_init__(self) -> None:
        if not self.id or not self.kind or not self.excerpt:
            raise ValueError("source note identity, kind and excerpt are required")
        if self.status not in _NOTE_STATUSES:
            raise ValueError("source note status is invalid")


@dataclass(frozen=True)
class DocumentDossierReference:
    key: str
    title: str
    author_year: str
    roles: tuple[str, ...]
    status: str = "resolved"
    cited_count: int = 0
    source_note_count: int = 0
    related_from: tuple[str, ...] = ()
    reference_sets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("reference key is required")
        roles = tuple(dict.fromkeys(self.roles))
        if not roles or any(role not in _REFERENCE_ROLES for role in roles):
            raise ValueError("reference roles are invalid")
        if self.status not in _REFERENCE_STATUSES:
            raise ValueError("reference status is invalid")
        if self.status == "resolved" and not self.title:
            raise ValueError("resolved references require a title")
        if self.cited_count < 0 or self.source_note_count < 0:
            raise ValueError("reference occurrence counts cannot be negative")
        object.__setattr__(self, "roles", roles)
        object.__setattr__(self, "related_from", tuple(dict.fromkeys(self.related_from)))
        object.__setattr__(self, "reference_sets", tuple(dict.fromkeys(self.reference_sets)))


@dataclass(frozen=True)
class DocumentDossierReferenceSet:
    name: str
    description: str
    members: tuple[str, ...]
    relevant_members: tuple[str, ...]
    missing_members: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("reference set name is required")
        for name in ("members", "relevant_members", "missing_members"):
            object.__setattr__(self, name, tuple(dict.fromkeys(getattr(self, name))))


@dataclass(frozen=True)
class DocumentDossierIssue:
    severity: str
    kind: str
    subject: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in {"error", "warning", "advisory"}:
            raise ValueError("issue severity is invalid")
        if not self.kind or not self.subject or not self.message:
            raise ValueError("issue kind, subject and message are required")


@dataclass(frozen=True)
class DocumentDossierStatistics:
    words: int
    characters: int
    characters_no_spaces: int
    paragraphs: int
    lines: int
    reading_minutes: int
    sections: int
    citations: int
    source_notes: int
    distinct_references: int
    relevant_reference_sets: int
    errors: int
    warnings: int
    advisories: int
    sections_without_citations: int
    sections_without_source_notes: int

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class DocumentDossierCounts:
    sections: int
    bookmarks: int
    links: int
    citations: int
    source_notes: int
    references: int
    related_references: int
    collected_unused_references: int
    relevant_reference_sets: int
    issues: int

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class DocumentDossierSnapshot:
    identity: DocumentDossierIdentity
    authority_stamp: DocumentDossierAuthorityStamp
    capabilities: DocumentDossierCapabilities
    counts: DocumentDossierCounts
    sections: tuple[DocumentDossierSection, ...]
    bookmarks: tuple[DocumentDossierBookmark, ...]
    links: tuple[DocumentDossierLink, ...]
    citations: tuple[DocumentDossierCitation, ...]
    source_notes: tuple[DocumentDossierSourceNote, ...]
    references: tuple[DocumentDossierReference, ...]
    reference_sets: tuple[DocumentDossierReferenceSet, ...]
    issues: tuple[DocumentDossierIssue, ...]
    statistics: DocumentDossierStatistics
    refreshed_at: str = ""

    def __post_init__(self) -> None:
        for name in (
            "sections",
            "bookmarks",
            "links",
            "citations",
            "source_notes",
            "references",
            "reference_sets",
            "issues",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))

    def reference(self, key: str) -> DocumentDossierReference | None:
        requested = normalize_key(key)
        return next((item for item in self.references if item.key == requested), None)

    def section(self, section_id: str) -> DocumentDossierSection | None:
        return next((item for item in self.sections if item.id == section_id), None)


@dataclass(frozen=True)
class DocumentDossierInputs:
    document_text: str
    document_path: str = ""
    modified: bool = False
    bookmarks: tuple[int, ...] = ()
    reference_snapshot: ReferenceLibrarySnapshot | None = None
    source_note_snapshot: SourceNoteSnapshot | None = None
    reference_set_snapshot: ReferenceSetSnapshot | None = None
    document_token: FileToken = field(default_factory=lambda: FileToken(False))
    refreshed_at: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.document_text, str):
            raise TypeError("document_text must be str")
        if not isinstance(self.document_path, str):
            raise TypeError("document_path must be str")
        clean_bookmarks: list[int] = []
        for value in self.bookmarks:
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError("bookmarks must contain int offsets")
            if value < 0:
                raise ValueError("bookmark offsets cannot be negative")
            clamped = min(value, len(self.document_text))
            if clamped not in clean_bookmarks:
                clean_bookmarks.append(clamped)
        object.__setattr__(self, "bookmarks", tuple(sorted(clean_bookmarks)))
        object.__setattr__(self, "modified", bool(self.modified))
        if not isinstance(self.document_token, FileToken):
            raise TypeError("document_token must be FileToken")


def document_dossier_authority_stamp(inputs: DocumentDossierInputs) -> DocumentDossierAuthorityStamp:
    if not isinstance(inputs, DocumentDossierInputs):
        raise TypeError("inputs must be DocumentDossierInputs")
    references_token = (
        inputs.reference_snapshot.token if inputs.reference_snapshot is not None else FileToken(False)
    )
    notes_token = (
        inputs.source_note_snapshot.token if inputs.source_note_snapshot is not None else FileToken(False)
    )
    sets_token = (
        inputs.reference_set_snapshot.token if inputs.reference_set_snapshot is not None else FileToken(False)
    )
    return DocumentDossierAuthorityStamp(
        document_path=inputs.document_path,
        buffer_digest=_digest(inputs.document_text),
        modified=inputs.modified,
        document_token=inputs.document_token,
        source_notes_token=notes_token,
        references_token=references_token,
        reference_sets_token=sets_token,
    )


def _resolved_identity(records: tuple[ReferenceRecord, ...], requested: str) -> tuple[str, str]:
    resolution = resolve_reference(records, requested)
    return resolution.status, resolution.canonical_key or ""


def _citation_views(
    text: str,
    structure: DocumentStructure,
    records: tuple[ReferenceRecord, ...],
    clusters: tuple[CitationCluster, ...],
) -> tuple[DocumentDossierCitation, ...]:
    views: list[DocumentDossierCitation] = []
    for index, cluster in enumerate(clusters, start=1):
        requested: list[str] = []
        canonical: list[str] = []
        missing: list[str] = []
        ambiguous: list[str] = []
        for item in cluster.items:
            # Preserve item order and multiplicity.  UI grouping may de-duplicate
            # labels, but occurrence counts must remain exact.
            requested.append(item.key)
            status, canonical_key = _resolved_identity(records, item.key)
            if status in {"primary", "alias"}:
                canonical.append(canonical_key)
            elif status == "missing":
                missing.append(item.key)
            elif status == "ambiguous":
                ambiguous.append(item.key)
        section = _section_for_offset(structure, cluster.start)
        views.append(
            DocumentDossierCitation(
                id=f"citation-{index}-{cluster.start}",
                raw=cluster.raw,
                line=_line_for_offset(text, cluster.start),
                start_offset=cluster.start,
                end_offset=cluster.end,
                requested_keys=tuple(requested),
                canonical_keys=tuple(canonical),
                missing_keys=tuple(missing),
                ambiguous_keys=tuple(ambiguous),
                section_id=_section_identifier(section),
            )
        )
    return tuple(views)


def _source_note_views(
    structure: DocumentStructure,
    records: tuple[ReferenceRecord, ...],
    notes: tuple[SourceNote, ...],
) -> tuple[DocumentDossierSourceNote, ...]:
    result: list[DocumentDossierSourceNote] = []
    for note in notes:
        ref_status, canonical = (
            _resolved_identity(records, note.reference_key)
            if note.reference_key
            else ("missing", "")
        )
        section_id = ""
        target_status = "none"
        if note.target:
            headings = structure.headings_for_identifier(note.target)
            if len(headings) == 1:
                section_id = _section_identifier(headings[0])
                target_status = "resolved"
            elif not headings:
                target_status = "missing"
            else:
                target_status = "ambiguous"
        if note.target and target_status != "resolved":
            status = "orphan"
        elif note.reference_key and ref_status not in {"primary", "alias"}:
            status = "incomplete"
        elif note.kind in {"quote", "paraphrase"} and not note.locator.display:
            status = "incomplete"
        else:
            status = "complete"
        result.append(
            DocumentDossierSourceNote(
                id=note.id,
                kind=note.kind,
                excerpt=note.excerpt,
                reference_key=note.reference_key,
                canonical_reference_key=canonical,
                locator=note.locator.display,
                target=note.target,
                section_id=section_id,
                status=status,
            )
        )
    return tuple(result)


def _link_views(
    text: str,
    structure: DocumentStructure,
    links: tuple[MarkdownHeadingLink, ...],
) -> tuple[DocumentDossierLink, ...]:
    result: list[DocumentDossierLink] = []
    for index, link in enumerate(links, start=1):
        destinations = structure.headings_for_identifier(link.identifier)
        if len(destinations) == 1:
            status = "resolved"
            destination = destinations[0]
            destination_id = _section_identifier(destination)
            destination_line = destination.line
        elif destinations:
            status = "ambiguous"
            destination_id = ""
            destination_line = None
        else:
            status = "missing"
            destination_id = ""
            destination_line = None
        source = _section_for_offset(structure, link.start_offset)
        result.append(
            DocumentDossierLink(
                id=f"link-{index}-{link.start_offset}",
                label=link.label,
                identifier=link.identifier,
                line=link.line,
                start_offset=link.start_offset,
                end_offset=link.end_offset,
                source_section_id=_section_identifier(source),
                status=status,
                destination_section_id=destination_id,
                destination_line=destination_line,
            )
        )
    return tuple(result)


def _bookmark_views(
    text: str,
    structure: DocumentStructure,
    bookmarks: tuple[int, ...],
) -> tuple[DocumentDossierBookmark, ...]:
    result: list[DocumentDossierBookmark] = []
    for index, offset in enumerate(bookmarks, start=1):
        section = _section_for_offset(structure, offset)
        line = _line_for_offset(text, offset)
        result.append(
            DocumentDossierBookmark(
                id=f"bookmark-{index}-{offset}",
                offset=offset,
                line=line,
                section_id=_section_identifier(section),
                label=f"Bookmark {index} — line {line}",
            )
        )
    return tuple(result)


def _reference_projection(
    records: tuple[ReferenceRecord, ...],
    citations: tuple[DocumentDossierCitation, ...],
    notes: tuple[DocumentDossierSourceNote, ...],
    sets: tuple[ReferenceSet, ...],
) -> tuple[tuple[DocumentDossierReference, ...], tuple[DocumentDossierReferenceSet, ...]]:
    by_key = {record.key: record for record in records}
    roles: dict[str, set[str]] = {}
    cited_count: dict[str, int] = {}
    note_count: dict[str, int] = {}
    related_from: dict[str, list[str]] = {}
    set_names: dict[str, list[str]] = {}
    unresolved_roles: dict[tuple[str, str], set[str]] = {}

    for citation in citations:
        for key in citation.canonical_keys:
            roles.setdefault(key, set()).add("cited")
            cited_count[key] = cited_count.get(key, 0) + 1
        for key in citation.missing_keys:
            unresolved_roles.setdefault((key, "missing"), set()).update({"cited", "missing"})
        for key in citation.ambiguous_keys:
            unresolved_roles.setdefault((key, "ambiguous"), set()).update({"cited", "missing"})

    for note in notes:
        if note.canonical_reference_key:
            key = note.canonical_reference_key
            roles.setdefault(key, set()).add("source-note")
            note_count[key] = note_count.get(key, 0) + 1
        elif note.reference_key:
            status, _canonical = _resolved_identity(records, note.reference_key)
            unresolved_status = "ambiguous" if status == "ambiguous" else "missing"
            unresolved_roles.setdefault((note.reference_key, unresolved_status), set()).update(
                {"source-note", "missing"}
            )

    base_keys = set(roles)
    for subject_key in sorted(base_keys):
        try:
            related = effective_related_keys(records, subject_key)
        except ValueError:
            related = ()
        for key in related:
            if key not in by_key:
                continue
            roles.setdefault(key, set()).add("related")
            related_from.setdefault(key, []).append(subject_key)

    relevant_before_sets = set(roles)
    set_views: list[DocumentDossierReferenceSet] = []
    for item in sets:
        canonical_members: list[str] = []
        missing_members: list[str] = []
        for member in item.members:
            status, canonical = _resolved_identity(records, member)
            if status in {"primary", "alias"} and canonical:
                if canonical not in canonical_members:
                    canonical_members.append(canonical)
            else:
                missing_members.append(member)
        relevant_members = [key for key in canonical_members if key in relevant_before_sets]
        if not relevant_members:
            continue
        for key in canonical_members:
            roles.setdefault(key, set()).add("reference-set")
            set_names.setdefault(key, []).append(item.name)
        set_views.append(
            DocumentDossierReferenceSet(
                name=item.name,
                description=item.description,
                members=tuple(canonical_members),
                relevant_members=tuple(relevant_members),
                missing_members=tuple(missing_members),
            )
        )

    result: list[DocumentDossierReference] = []
    role_order = ("cited", "source-note", "related", "reference-set", "collected-unused", "missing")
    for key in sorted(roles):
        record = by_key.get(key)
        if record is None:
            continue
        item_roles = roles[key]
        if not ({"cited", "source-note"} & item_roles) and ({"related", "reference-set"} & item_roles):
            item_roles.add("collected-unused")
        ordered_roles = tuple(role for role in role_order if role in item_roles)
        result.append(
            DocumentDossierReference(
                key=record.key,
                title=record.title,
                author_year=record.author_year,
                roles=ordered_roles,
                status="resolved",
                cited_count=cited_count.get(key, 0),
                source_note_count=note_count.get(key, 0),
                related_from=tuple(sorted(set(related_from.get(key, ())))),
                reference_sets=tuple(sorted(set(set_names.get(key, ())), key=str.casefold)),
            )
        )

    for (key, status), item_roles in sorted(unresolved_roles.items()):
        ordered_roles = tuple(role for role in role_order if role in item_roles)
        result.append(
            DocumentDossierReference(
                key=key,
                title="",
                author_year="",
                roles=ordered_roles,
                status=status,
            )
        )

    priority = {"cited": 0, "source-note": 1, "related": 2, "reference-set": 3, "missing": 4}
    result.sort(
        key=lambda item: (
            min(priority.get(role, 99) for role in item.roles),
            item.author_year.casefold(),
            item.title.casefold(),
            item.key.casefold(),
        )
    )
    set_views.sort(key=lambda item: item.name.casefold())
    return tuple(result), tuple(set_views)


def _issues(
    report: ResearchCheckReport,
    relevant_reference_keys: set[str],
) -> tuple[DocumentDossierIssue, ...]:
    result: list[DocumentDossierIssue] = []
    for issue in report.issues:
        # Research Check reports every globally unused library record.  A
        # current-document dossier keeps only unused records that became
        # relevant through Related References or a pertinent Reference Set.
        if issue.kind == "reference-unused" and issue.subject not in relevant_reference_keys:
            continue
        result.append(DocumentDossierIssue(issue.severity, issue.kind, issue.subject, issue.message))
    return tuple(result)


def _section_views(
    text: str,
    structure: DocumentStructure,
    citations: tuple[DocumentDossierCitation, ...],
    notes: tuple[DocumentDossierSourceNote, ...],
    bookmarks: tuple[DocumentDossierBookmark, ...],
    links: tuple[DocumentDossierLink, ...],
) -> tuple[DocumentDossierSection, ...]:
    result: list[DocumentDossierSection] = []
    for heading in structure.headings:
        section_id = _section_identifier(heading)
        section_text = text[heading.start_offset:heading.section_end_offset]
        result.append(
            DocumentDossierSection(
                id=section_id,
                level=heading.level,
                title=heading.display_title,
                line=heading.line,
                start_offset=heading.start_offset,
                end_offset=heading.section_end_offset,
                excerpt=_section_excerpt(text, heading),
                word_count=document_statistics(section_text)["words"],
                citation_count=sum(item.section_id == section_id for item in citations),
                source_note_count=sum(item.section_id == section_id for item in notes),
                bookmark_count=sum(item.section_id == section_id for item in bookmarks),
                incoming_link_count=sum(item.destination_section_id == section_id for item in links),
                outgoing_link_count=sum(item.source_section_id == section_id for item in links),
            )
        )
    return tuple(result)


def build_document_dossier(inputs: DocumentDossierInputs) -> DocumentDossierSnapshot:
    """Build one immutable W96 Core projection from explicit authorities."""
    if not isinstance(inputs, DocumentDossierInputs):
        raise TypeError("inputs must be DocumentDossierInputs")

    references_snapshot = inputs.reference_snapshot or ReferenceLibrarySnapshot((), FileToken(False), ())
    notes_snapshot = inputs.source_note_snapshot or SourceNoteSnapshot((), FileToken(False), ())
    sets_snapshot = inputs.reference_set_snapshot or ReferenceSetSnapshot((), FileToken(False), ())
    records = tuple(references_snapshot.records)
    source_notes = tuple(notes_snapshot.notes)
    reference_sets = tuple(sets_snapshot.sets)

    structure = build_document_structure(inputs.document_text)
    clusters = parse_citation_clusters(inputs.document_text)
    heading_links = parse_markdown_heading_links(inputs.document_text)

    citations = _citation_views(inputs.document_text, structure, records, clusters)
    note_views = _source_note_views(structure, records, source_notes)
    links = _link_views(inputs.document_text, structure, heading_links)
    bookmarks = _bookmark_views(inputs.document_text, structure, inputs.bookmarks)
    references, relevant_sets = _reference_projection(records, citations, note_views, reference_sets)

    report = run_research_check(
        records,
        inputs.document_text,
        source_notes,
        structure,
        reference_sets,
    )
    relevant_keys = {item.key for item in references if item.status == "resolved"}
    issues = _issues(report, relevant_keys)
    sections = _section_views(inputs.document_text, structure, citations, note_views, bookmarks, links)

    stats = document_statistics(inputs.document_text)
    errors = sum(item.severity == "error" for item in issues)
    warnings = sum(item.severity == "warning" for item in issues)
    advisories = sum(item.severity == "advisory" for item in issues)
    dossier_stats = DocumentDossierStatistics(
        words=stats["words"],
        characters=stats["characters"],
        characters_no_spaces=stats["characters_no_spaces"],
        paragraphs=stats["paragraphs"],
        lines=stats["lines"],
        reading_minutes=stats["reading_minutes"],
        sections=len(sections),
        citations=sum(len(item.requested_keys) for item in citations),
        source_notes=len(note_views),
        distinct_references=len(references),
        relevant_reference_sets=len(relevant_sets),
        errors=errors,
        warnings=warnings,
        advisories=advisories,
        sections_without_citations=sum(item.citation_count == 0 for item in sections),
        sections_without_source_notes=sum(item.source_note_count == 0 for item in sections),
    )

    path = inputs.document_path.strip()
    identity = DocumentDossierIdentity(
        name=os.path.basename(path) if path else "Untitled",
        path=path,
        modified=inputs.modified,
        untitled=not bool(path),
    )
    capabilities = DocumentDossierCapabilities(
        can_navigate_document=True,
        can_use_source_notes=bool(path),
        can_open_references=True,
        can_open_reference_sets=True,
        can_run_research_check=True,
    )
    counts = DocumentDossierCounts(
        sections=len(sections),
        bookmarks=len(bookmarks),
        links=len(links),
        citations=sum(len(item.requested_keys) for item in citations),
        source_notes=len(note_views),
        references=len(references),
        related_references=sum("related" in item.roles for item in references),
        collected_unused_references=sum("collected-unused" in item.roles for item in references),
        relevant_reference_sets=len(relevant_sets),
        issues=len(issues),
    )
    return DocumentDossierSnapshot(
        identity=identity,
        authority_stamp=document_dossier_authority_stamp(inputs),
        capabilities=capabilities,
        counts=counts,
        sections=sections,
        bookmarks=bookmarks,
        links=links,
        citations=citations,
        source_notes=note_views,
        references=references,
        reference_sets=relevant_sets,
        issues=issues,
        statistics=dossier_stats,
        refreshed_at=inputs.refreshed_at,
    )
