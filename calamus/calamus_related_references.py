"""Pure symmetric Related References model and planner for Calamus.

Related References remain transparent fields inside ``references.md``.  This
module never performs I/O and never infers relationships.  It resolves aliases,
rejects missing or ambiguous identities, and plans one symmetric update across
all affected records.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Iterable

from calamus_references import ReferenceRecord, normalize_key

_RELATED_LABELS = frozenset({"related", "related key", "related keys"})
_CANONICAL_LABEL = "Related Keys"


def is_related_label(label: str) -> bool:
    return isinstance(label, str) and label.casefold() in _RELATED_LABELS


def _related_key_tokens(record: ReferenceRecord) -> tuple[str, ...]:
    if not isinstance(record, ReferenceRecord):
        raise TypeError("record must be ReferenceRecord")
    values: list[str] = []
    for label, value in record.extra_fields:
        if not is_related_label(label):
            continue
        values.extend(
            clean for clean in (normalize_key(key) for key in re.split(r"[,;\s]+", value)) if clean
        )
    return tuple(values)


def related_keys(record: ReferenceRecord) -> tuple[str, ...]:
    """Return de-duplicated related identities in source order."""
    return tuple(dict.fromkeys(_related_key_tokens(record)))


def related_key_occurrence_count(record: ReferenceRecord, key: str) -> int:
    target = normalize_key(key)
    if not target:
        return 0
    count = 0
    for label, value in record.extra_fields:
        if not is_related_label(label):
            continue
        count += sum(normalize_key(token) == target for token in re.split(r"[,;\s]+", value))
    return count


def with_related_keys(record: ReferenceRecord, keys: Iterable[str]) -> ReferenceRecord:
    """Return ``record`` with exactly one canonical Related Keys field."""
    if not isinstance(record, ReferenceRecord):
        raise TypeError("record must be ReferenceRecord")
    clean: list[str] = []
    for value in keys:
        key = normalize_key(value)
        if key and key not in clean:
            clean.append(key)
    extras: list[tuple[str, str]] = []
    insert_at: int | None = None
    for label, value in record.extra_fields:
        if is_related_label(label):
            if insert_at is None:
                insert_at = len(extras)
            continue
        extras.append((label, value))
    if clean:
        field = (_CANONICAL_LABEL, ", ".join(clean))
        if insert_at is None:
            extras.append(field)
        else:
            extras.insert(insert_at, field)
    return replace(record, extra_fields=tuple(extras))


def replace_related_identity(
    record: ReferenceRecord,
    old_key: str,
    new_key: str,
) -> tuple[ReferenceRecord, int]:
    """Replace one identity in related fields while preserving unrelated fields."""
    old = normalize_key(old_key)
    new = normalize_key(new_key)
    if not old or not new:
        raise ValueError("related identity replacement requires non-empty keys")
    count = related_key_occurrence_count(record, old)
    if not count:
        return record, 0
    values = tuple(new if value == old else value for value in related_keys(record))
    return with_related_keys(record, values), count


def _identity_owners(records: tuple[ReferenceRecord, ...]) -> dict[str, tuple[str, ...]]:
    owners: dict[str, list[str]] = {}
    for record in records:
        if not isinstance(record, ReferenceRecord):
            raise TypeError("records must contain ReferenceRecord values")
        for identity in record.identity_keys:
            owners.setdefault(identity, []).append(record.key)
    return {identity: tuple(dict.fromkeys(keys)) for identity, keys in owners.items()}


def effective_related_keys(
    records: Iterable[ReferenceRecord],
    subject_key: str,
) -> tuple[str, ...]:
    """Return the symmetric closure visible to an editor for one subject.

    Incoming one-sided legacy relations are included so opening the editor never
    removes an asymmetry merely because the subject record omitted its half.
    """
    snapshot = tuple(records)
    owners = _identity_owners(snapshot)
    subject = normalize_key(subject_key)
    if owners.get(subject, ()) != (subject,):
        raise ValueError(f"Primary Reference key is not uniquely available: {subject}")
    values: list[str] = []
    target = next(record for record in snapshot if record.key == subject)
    for raw in related_keys(target):
        matches = owners.get(raw, ())
        if len(matches) == 1 and matches[0] != subject and matches[0] not in values:
            values.append(matches[0])
    for record in snapshot:
        if record.key == subject:
            continue
        outgoing = []
        for raw in related_keys(record):
            matches = owners.get(raw, ())
            if len(matches) == 1:
                outgoing.append(matches[0])
        if subject in outgoing and record.key not in values:
            values.append(record.key)
    return tuple(values)


def resolve_related_identity(
    records: Iterable[ReferenceRecord],
    identity: str,
) -> tuple[str, str | None]:
    snapshot = tuple(records)
    owners = _identity_owners(snapshot)
    requested = normalize_key(identity)
    matches = owners.get(requested, ())
    if not requested or not matches:
        return "missing", None
    if len(matches) > 1:
        return "ambiguous", None
    canonical = matches[0]
    return ("primary" if canonical == requested else "alias"), canonical


@dataclass(frozen=True, order=True)
class RelatedReferenceIssue:
    severity: str
    kind: str
    subject_key: str
    related_key: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in {"error", "warning"}:
            raise ValueError("related issue severity is invalid")
        if not all(isinstance(value, str) and value for value in (
            self.kind, self.subject_key, self.related_key, self.message
        )):
            raise ValueError("related issue fields must be non-empty strings")


def related_reference_issues(
    records: Iterable[ReferenceRecord],
) -> tuple[RelatedReferenceIssue, ...]:
    snapshot = tuple(records)
    owners = _identity_owners(snapshot)
    canonical_map = {record.key: record for record in snapshot}
    issues: list[RelatedReferenceIssue] = []
    for record in snapshot:
        seen_raw: set[str] = set()
        for raw in _related_key_tokens(record):
            if raw in seen_raw:
                issues.append(RelatedReferenceIssue(
                    "warning", "duplicate-related-key", record.key, raw,
                    f"Related reference {raw} is listed more than once.",
                ))
                continue
            seen_raw.add(raw)
            matches = owners.get(raw, ())
            if not matches:
                issues.append(RelatedReferenceIssue(
                    "error", "related-key-missing", record.key, raw,
                    f"Related reference key is unavailable: {raw}.",
                ))
                continue
            if len(matches) > 1:
                issues.append(RelatedReferenceIssue(
                    "error", "related-key-ambiguous", record.key, raw,
                    f"Related reference identity is ambiguous: {raw}.",
                ))
                continue
            canonical = matches[0]
            if canonical == record.key:
                issues.append(RelatedReferenceIssue(
                    "error", "related-key-self", record.key, raw,
                    "A Reference cannot be related to itself.",
                ))
                continue
            if raw != canonical:
                issues.append(RelatedReferenceIssue(
                    "warning", "related-key-uses-alias", record.key, raw,
                    f"Related key should migrate from {raw} to {canonical}.",
                ))
            counterpart = canonical_map[canonical]
            counterpart_canonicals = {
                owners[value][0]
                for value in related_keys(counterpart)
                if len(owners.get(value, ())) == 1
            }
            if record.key not in counterpart_canonicals:
                issues.append(RelatedReferenceIssue(
                    "warning", "related-key-asymmetric", record.key, canonical,
                    f"Relation {record.key} ↔ {canonical} is present only on one side.",
                ))
    return tuple(sorted(set(issues)))


@dataclass(frozen=True)
class RelatedReferencePlan:
    subject_key: str
    records_before: tuple[ReferenceRecord, ...]
    records_after: tuple[ReferenceRecord, ...]
    related_before: tuple[str, ...]
    related_after: tuple[str, ...]
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed_record_keys: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return self.records_before != self.records_after


def plan_related_references_update(
    records: Iterable[ReferenceRecord],
    subject_key: str,
    requested_keys: Iterable[str],
) -> RelatedReferencePlan:
    """Plan a symmetric replacement of one Reference's related set.

    The user selects canonical library objects.  Alias input is accepted but
    canonicalized; missing, ambiguous and self identities fail closed.
    """
    before = tuple(records)
    if any(not isinstance(record, ReferenceRecord) for record in before):
        raise TypeError("records must contain ReferenceRecord values")
    owners = _identity_owners(before)
    subject = normalize_key(subject_key)
    subject_matches = owners.get(subject, ())
    if len(subject_matches) != 1 or subject_matches[0] != subject:
        raise ValueError(f"Primary Reference key is not uniquely available: {subject}")

    requested: list[str] = []
    for identity in requested_keys:
        raw = normalize_key(identity)
        matches = owners.get(raw, ())
        if not matches:
            raise ValueError(f"Related Reference is missing: {raw or '<empty>'}")
        if len(matches) > 1:
            raise ValueError(f"Related Reference is ambiguous: {raw}")
        canonical = matches[0]
        if canonical == subject:
            raise ValueError("A Reference cannot be related to itself.")
        if canonical not in requested:
            requested.append(canonical)

    records_by_key = {record.key: record for record in before}
    current_canonical = list(effective_related_keys(before, subject))

    requested_tuple = tuple(requested)
    after_records: list[ReferenceRecord] = []
    changed: list[str] = []
    for record in before:
        if record.key == subject:
            updated = with_related_keys(record, requested_tuple)
        else:
            related = []
            for raw in related_keys(record):
                matches = owners.get(raw, ())
                canonical = matches[0] if len(matches) == 1 else raw
                if canonical == subject:
                    continue
                if canonical not in related:
                    related.append(canonical)
            if record.key in requested_tuple:
                related.append(subject)
            updated = with_related_keys(record, related)
        after_records.append(updated)
        if updated != record:
            changed.append(record.key)

    added = tuple(key for key in requested_tuple if key not in current_canonical)
    removed = tuple(key for key in current_canonical if key not in requested_tuple)
    return RelatedReferencePlan(
        subject_key=subject,
        records_before=before,
        records_after=tuple(after_records),
        related_before=tuple(current_canonical),
        related_after=requested_tuple,
        added=added,
        removed=removed,
        changed_record_keys=tuple(changed),
    )
