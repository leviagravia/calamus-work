"""Pure Markdown projections for the Calamus Research apparatus.

The canonical authorities remain the current document, ``references.md`` and
its document-specific Source Notes sidecar.  This module only derives export
text from immutable snapshots; it performs no file I/O and no GTK work.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from calamus_citations import cited_keys
from calamus_document_structure import DocumentStructure
from calamus_reference_integrity import resolve_reference
from calamus_references import ReferenceRecord
from calamus_source_notes import SourceNote

NOTES_DOCUMENT_ORDER = "notes-document-order"
NOTES_BY_REFERENCE = "notes-by-reference"
CITED_BIBLIOGRAPHY = "cited-bibliography"
ANNOTATED_BIBLIOGRAPHY = "annotated-bibliography"
FULL_RESEARCH_DOSSIER = "full-research-dossier"

_EXPORT_KINDS = (
    NOTES_DOCUMENT_ORDER,
    NOTES_BY_REFERENCE,
    CITED_BIBLIOGRAPHY,
    ANNOTATED_BIBLIOGRAPHY,
    FULL_RESEARCH_DOSSIER,
)
_EXPORT_TITLES = {
    NOTES_DOCUMENT_ORDER: "Source Notes in Document Order",
    NOTES_BY_REFERENCE: "Source Notes by Reference",
    CITED_BIBLIOGRAPHY: "Bibliography of Cited Sources",
    ANNOTATED_BIBLIOGRAPHY: "Annotated Bibliography",
    FULL_RESEARCH_DOSSIER: "Complete Research Dossier",
}
_EXPORT_SUFFIXES = {
    NOTES_DOCUMENT_ORDER: "source-notes-document-order",
    NOTES_BY_REFERENCE: "source-notes-by-reference",
    CITED_BIBLIOGRAPHY: "cited-bibliography",
    ANNOTATED_BIBLIOGRAPHY: "annotated-bibliography",
    FULL_RESEARCH_DOSSIER: "research-dossier",
}


@dataclass(frozen=True)
class ResearchExportArtifact:
    kind: str
    title: str
    markdown: str
    reference_count: int
    source_note_count: int
    unresolved_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in _EXPORT_KINDS:
            raise ValueError("unsupported Research export kind")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("export title is required")
        if not isinstance(self.markdown, str):
            raise TypeError("export markdown must be text")
        if not isinstance(self.reference_count, int) or self.reference_count < 0:
            raise ValueError("reference_count must be non-negative")
        if not isinstance(self.source_note_count, int) or self.source_note_count < 0:
            raise ValueError("source_note_count must be non-negative")
        object.__setattr__(self, "unresolved_keys", tuple(self.unresolved_keys))


def research_export_kinds() -> tuple[str, ...]:
    return _EXPORT_KINDS


def research_export_title(kind: str) -> str:
    if kind not in _EXPORT_TITLES:
        raise ValueError("unsupported Research export kind")
    return _EXPORT_TITLES[kind]


def research_export_suffix(kind: str) -> str:
    if kind not in _EXPORT_SUFFIXES:
        raise ValueError("unsupported Research export kind")
    return _EXPORT_SUFFIXES[kind]


def _one_line(value: str) -> str:
    return " ".join(value.split()).strip() if isinstance(value, str) else ""


def _join_people(values: Iterable[str]) -> str:
    return "; ".join(_one_line(value) for value in values if _one_line(value))


def format_reference_markdown(record: ReferenceRecord) -> str:
    """Render transparent Markdown metadata, not a CSL-formatted citation."""
    if not isinstance(record, ReferenceRecord):
        raise TypeError("record must be a ReferenceRecord")
    parts: list[str] = []
    people = _join_people(record.authors)
    if people:
        parts.append(people + ".")
    parts.append(f"*{record.title}*.")
    if record.container_title:
        parts.append(record.container_title + ".")
    publication = ""
    if record.location and record.publisher:
        publication = f"{record.location}: {record.publisher}"
    else:
        publication = record.publisher or record.location
    if record.year:
        publication = f"{publication}, {record.year}" if publication else record.year
    if publication:
        parts.append(publication.rstrip(".") + ".")
    details: list[str] = []
    if record.volume:
        details.append(f"vol. {record.volume}")
    if record.issue:
        details.append(f"no. {record.issue}")
    if record.pages:
        details.append(f"pp. {record.pages}")
    if details:
        parts.append(", ".join(details) + ".")
    if record.doi:
        parts.append(f"DOI: {record.doi}.")
    elif record.url:
        parts.append(record.url)
    return f"- **`{record.key}`** — " + " ".join(parts)


def _note_heading(note: SourceNote) -> str:
    pieces = [note.kind.title()]
    if note.reference_key:
        pieces.append(f"`{note.reference_key}`")
    if note.locator_text:
        pieces.append(note.locator_text)
    return " — ".join(pieces)


def _render_note(note: SourceNote, *, level: int = 3) -> list[str]:
    heading = "#" * max(1, min(6, level))
    lines = [f"{heading} {_note_heading(note)}", ""]
    if note.kind == "quote":
        for line in note.text.splitlines() or [""]:
            lines.append(f"> {line}" if line else ">")
    else:
        lines.extend(note.text.splitlines())
    lines.append("")
    metadata: list[str] = [f"- Source Note: `{note.id}`"]
    if note.target:
        metadata.append(f"- Target: `{note.target}`")
    if note.tags:
        metadata.append("- Tags: " + ", ".join(note.tags))
    lines.extend(metadata)
    if note.comment:
        lines.extend(["", "**Comment**", "", note.comment])
    lines.append("")
    return lines


def _resolve_key(
    records: tuple[ReferenceRecord, ...], key: str
) -> tuple[str | None, str | None]:
    if not key:
        return None, None
    resolution = resolve_reference(records, key)
    return resolution.canonical_key, None if resolution.canonical_key else key


def _record_map(records: tuple[ReferenceRecord, ...]) -> dict[str, ReferenceRecord]:
    return {record.key: record for record in records}


def _citation_reference_order(
    document_text: str,
    records: tuple[ReferenceRecord, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ordered: list[str] = []
    unresolved: list[str] = []
    for key in cited_keys(document_text):
        canonical, missing = _resolve_key(records, key)
        if canonical and canonical not in ordered:
            ordered.append(canonical)
        elif missing and missing not in unresolved:
            unresolved.append(missing)
    return tuple(ordered), tuple(unresolved)


def _used_reference_order(
    document_text: str,
    records: tuple[ReferenceRecord, ...],
    notes: tuple[SourceNote, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ordered, unresolved = _citation_reference_order(document_text, records)
    result = list(ordered)
    missing = list(unresolved)
    for note in notes:
        canonical, unresolved_key = _resolve_key(records, note.reference_key)
        if canonical and canonical not in result:
            result.append(canonical)
        elif unresolved_key and unresolved_key not in missing:
            missing.append(unresolved_key)
    return tuple(result), tuple(missing)


def render_notes_document_order(
    notes: tuple[SourceNote, ...],
    structure: DocumentStructure,
) -> str:
    if not isinstance(structure, DocumentStructure):
        raise TypeError("structure must be a DocumentStructure")
    indexed = list(enumerate(notes))
    heading_positions: dict[str, tuple[int, str]] = {}
    ambiguous: set[str] = set()
    for position, heading in enumerate(structure.headings):
        if not heading.identifier:
            continue
        if heading.identifier in heading_positions:
            ambiguous.add(heading.identifier)
        else:
            heading_positions[heading.identifier] = (position, heading.display_title)

    def key(item: tuple[int, SourceNote]) -> tuple[int, int, int]:
        index, note = item
        identifier = note.target[1:] if note.target.startswith("#") else note.target
        if identifier and identifier in heading_positions and identifier not in ambiguous:
            return (0, heading_positions[identifier][0], index)
        return (1, index, index)

    ordered = sorted(indexed, key=key)
    lines: list[str] = []
    current_target: str | None = None
    for _, note in ordered:
        identifier = note.target[1:] if note.target.startswith("#") else note.target
        valid_target = (
            identifier
            if identifier in heading_positions and identifier not in ambiguous
            else ""
        )
        target_marker = valid_target or "__unplaced__"
        if target_marker != current_target:
            if valid_target:
                title = heading_positions[valid_target][1]
                lines.extend([f"## {title} {{#{valid_target}}}", ""])
            else:
                lines.extend(["## Untargeted or Unresolved Notes", ""])
            current_target = target_marker
        lines.extend(_render_note(note))
    if not notes:
        lines.extend(["_No Source Notes are available for this document._", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_notes_by_reference(
    notes: tuple[SourceNote, ...],
    records: tuple[ReferenceRecord, ...],
) -> tuple[str, tuple[str, ...]]:
    record_by_key = _record_map(records)
    groups: dict[str, list[SourceNote]] = {}
    order: list[str] = []
    unresolved: list[str] = []
    for note in notes:
        canonical, missing = _resolve_key(records, note.reference_key)
        group = canonical or (f"?{missing}" if missing else "__unlinked__")
        if group not in groups:
            groups[group] = []
            order.append(group)
        groups[group].append(note)
        if missing and missing not in unresolved:
            unresolved.append(missing)

    lines: list[str] = []
    for group in order:
        if group == "__unlinked__":
            lines.extend(["## Notes without a Reference", ""])
        elif group.startswith("?"):
            lines.extend([f"## Unresolved Reference `{group[1:]}`", ""])
        else:
            record = record_by_key[group]
            lines.extend([f"## {record.author_year} — {record.title}", "", format_reference_markdown(record), ""])
        for note in groups[group]:
            lines.extend(_render_note(note))
    if not notes:
        lines.extend(["_No Source Notes are available for this document._", ""])
    return "\n".join(lines).rstrip() + "\n", tuple(unresolved)


def render_cited_bibliography(
    document_text: str,
    records: tuple[ReferenceRecord, ...],
) -> tuple[str, tuple[str, ...], int]:
    keys, unresolved = _citation_reference_order(document_text, records)
    record_by_key = _record_map(records)
    lines = [format_reference_markdown(record_by_key[key]) for key in keys]
    if not lines:
        lines.append("_No resolvable citations were found in the current document._")
    if unresolved:
        lines.extend(["", "## Unresolved Citation Keys", ""])
        lines.extend(f"- `{key}`" for key in unresolved)
    return "\n".join(lines).rstrip() + "\n", unresolved, len(keys)


def render_annotated_bibliography(
    document_text: str,
    records: tuple[ReferenceRecord, ...],
    notes: tuple[SourceNote, ...],
) -> tuple[str, tuple[str, ...], int]:
    keys, unresolved = _used_reference_order(document_text, records, notes)
    record_by_key = _record_map(records)
    notes_by_key: dict[str, list[SourceNote]] = {key: [] for key in keys}
    for note in notes:
        canonical, _ = _resolve_key(records, note.reference_key)
        if canonical in notes_by_key:
            notes_by_key[canonical].append(note)
    lines: list[str] = []
    for key in keys:
        record = record_by_key[key]
        lines.extend([f"## {record.author_year} — {record.title}", "", format_reference_markdown(record), ""])
        if record.annotation:
            lines.extend(["**Reference annotation**", "", record.annotation.strip(), ""])
        linked = notes_by_key[key]
        if linked:
            lines.extend(["**Linked Source Notes**", ""])
            for note in linked:
                lines.extend(_render_note(note, level=3))
        elif not record.annotation:
            lines.extend(["_No annotation or linked Source Notes._", ""])
    if not keys:
        lines.extend(["_No used References are available for an annotated bibliography._", ""])
    if unresolved:
        lines.extend(["## Unresolved Reference Keys", ""])
        lines.extend(f"- `{key}`" for key in unresolved)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", unresolved, len(keys)


def build_research_export(
    kind: str,
    *,
    document_name: str,
    document_text: str,
    records: Iterable[ReferenceRecord],
    notes: Iterable[SourceNote],
    structure: DocumentStructure,
) -> ResearchExportArtifact:
    if kind not in _EXPORT_KINDS:
        raise ValueError("unsupported Research export kind")
    if not isinstance(document_name, str) or not document_name.strip():
        raise ValueError("document_name is required")
    if not isinstance(document_text, str):
        raise TypeError("document_text must be text")
    records_tuple = tuple(records)
    notes_tuple = tuple(notes)
    if any(not isinstance(record, ReferenceRecord) for record in records_tuple):
        raise TypeError("records must contain ReferenceRecord values")
    if any(not isinstance(note, SourceNote) for note in notes_tuple):
        raise TypeError("notes must contain SourceNote values")
    if not isinstance(structure, DocumentStructure):
        raise TypeError("structure must be a DocumentStructure")

    unresolved: tuple[str, ...] = ()
    reference_count = 0
    if kind == NOTES_DOCUMENT_ORDER:
        body = render_notes_document_order(notes_tuple, structure)
    elif kind == NOTES_BY_REFERENCE:
        body, unresolved = render_notes_by_reference(notes_tuple, records_tuple)
        reference_count = len({note.reference_key for note in notes_tuple if note.reference_key})
    elif kind == CITED_BIBLIOGRAPHY:
        body, unresolved, reference_count = render_cited_bibliography(document_text, records_tuple)
    elif kind == ANNOTATED_BIBLIOGRAPHY:
        body, unresolved, reference_count = render_annotated_bibliography(
            document_text, records_tuple, notes_tuple
        )
    else:
        document_notes = render_notes_document_order(notes_tuple, structure)
        grouped_notes, unresolved_notes = render_notes_by_reference(notes_tuple, records_tuple)
        cited, unresolved_cited, cited_count = render_cited_bibliography(document_text, records_tuple)
        annotated, unresolved_annotated, annotated_count = render_annotated_bibliography(
            document_text, records_tuple, notes_tuple
        )
        unresolved = tuple(dict.fromkeys((*unresolved_notes, *unresolved_cited, *unresolved_annotated)))
        reference_count = max(cited_count, annotated_count)
        body = (
            "## Source Notes in Document Order\n\n" + document_notes + "\n"
            "## Source Notes by Reference\n\n" + grouped_notes + "\n"
            "## Bibliography of Cited Sources\n\n" + cited + "\n"
            "## Annotated Bibliography\n\n" + annotated
        )

    title = research_export_title(kind)
    header = (
        f"# {title}\n\n"
        f"Document: `{document_name.strip()}`\n\n"
        "> Derived Markdown export. The current document, `references.md`, and the "
        "document Source Notes sidecar remain the canonical authorities.\n\n"
    )
    return ResearchExportArtifact(
        kind=kind,
        title=title,
        markdown=(header + body).rstrip() + "\n",
        reference_count=reference_count,
        source_note_count=len(notes_tuple),
        unresolved_keys=unresolved,
    )
