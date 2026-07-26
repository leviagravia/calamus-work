"""Transparent static named Reference Sets for Calamus.

A set owns only a name, optional description, deterministic order and canonical
Reference keys.  Bibliographic metadata remains exclusively in ``references.md``.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable

from calamus_references import ReferenceRecord, normalize_key

_HEADER = "# Calamus Reference Sets v1"
_DESCRIPTION = "Description:"


def _one_line(value: Any) -> str:
    return " ".join(value.splitlines()).strip() if isinstance(value, str) else ""


@dataclass(frozen=True)
class ReferenceSet:
    name: str
    description: str = ""
    members: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        name = _one_line(self.name)
        description = _one_line(self.description)
        if not name:
            raise ValueError("Reference Set name is required")
        if name.startswith("#"):
            raise ValueError("Reference Set name cannot begin with #")
        clean: list[str] = []
        for value in self.members:
            key = normalize_key(value)
            if not key:
                raise ValueError("Reference Set member key cannot be empty")
            if key not in clean:
                clean.append(key)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "members", tuple(clean))

    @property
    def identity(self) -> str:
        return self.name.casefold()

    @property
    def search_text(self) -> str:
        return "\n".join((self.name, self.description, *self.members)).casefold()

    def with_member_replacement(self, old_key: str, new_key: str) -> tuple["ReferenceSet", int]:
        old = normalize_key(old_key)
        new = normalize_key(new_key)
        count = sum(member == old for member in self.members)
        if not count:
            return self, 0
        return replace(
            self,
            members=tuple(new if member == old else member for member in self.members),
        ), count


@dataclass(frozen=True)
class ReferenceSetDiagnostic:
    line: int
    message: str
    blocking: bool = True


@dataclass(frozen=True, order=True)
class ReferenceSetIssue:
    severity: str
    kind: str
    set_name: str
    member_key: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in {"error", "warning"}:
            raise ValueError("Reference Set issue severity is invalid")
        if not all(isinstance(value, str) and value for value in (
            self.kind, self.set_name, self.member_key, self.message
        )):
            raise ValueError("Reference Set issue fields must be non-empty strings")


def identity_collision_messages(sets: Iterable[ReferenceSet]) -> tuple[str, ...]:
    owners: dict[str, str] = {}
    messages: list[str] = []
    for item in sets:
        if not isinstance(item, ReferenceSet):
            raise TypeError("sets must contain ReferenceSet values")
        previous = owners.get(item.identity)
        if previous is not None:
            messages.append(f"Reference Set name is duplicated: {previous} / {item.name}.")
        else:
            owners[item.identity] = item.name
    return tuple(messages)


def serialize_reference_sets_markdown(sets: Iterable[ReferenceSet]) -> str:
    snapshot = tuple(sets)
    collisions = identity_collision_messages(snapshot)
    if collisions:
        raise ValueError(collisions[0])
    lines = [_HEADER, ""]
    for item in snapshot:
        lines.extend([f"## {item.name}", "", f"{_DESCRIPTION} {item.description}".rstrip(), ""])
        lines.extend(f"- {member}" for member in item.members)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_reference_sets_markdown(
    text: Any,
) -> tuple[tuple[ReferenceSet, ...], tuple[ReferenceSetDiagnostic, ...]]:
    if not isinstance(text, str):
        return (), (ReferenceSetDiagnostic(1, "Reference Sets file is not text."),)
    lines = text.splitlines()
    diagnostics: list[ReferenceSetDiagnostic] = []
    first = next(((i + 1, line.strip()) for i, line in enumerate(lines) if line.strip()), None)
    if first is not None and first[1] != _HEADER:
        diagnostics.append(ReferenceSetDiagnostic(first[0], f"Expected file header: {_HEADER}."))
    sets: list[ReferenceSet] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("## "):
            index += 1
            continue
        start_line = index + 1
        name = line[3:].strip()
        index += 1
        description = ""
        members: list[str] = []
        while index < len(lines) and not lines[index].startswith("## "):
            current = lines[index].strip()
            if current.casefold().startswith(_DESCRIPTION.casefold()):
                if description:
                    diagnostics.append(ReferenceSetDiagnostic(
                        index + 1,
                        f"Reference Set {name or '<unnamed>'} has more than one Description field.",
                    ))
                description = current[len(_DESCRIPTION):].strip()
            elif current.startswith("-"):
                member = normalize_key(current[1:].strip())
                if not member:
                    diagnostics.append(ReferenceSetDiagnostic(index + 1, "Reference Set member is empty."))
                elif member in members:
                    diagnostics.append(ReferenceSetDiagnostic(
                        index + 1,
                        f"Reference Set {name or '<unnamed>'} repeats member {member}.",
                    ))
                else:
                    members.append(member)
            elif current and not current.startswith("#"):
                diagnostics.append(ReferenceSetDiagnostic(
                    index + 1,
                    f"Unrecognized Reference Set line: {current}",
                ))
            index += 1
        try:
            sets.append(ReferenceSet(name, description, tuple(members)))
        except ValueError as error:
            diagnostics.append(ReferenceSetDiagnostic(start_line, str(error) + "."))
    for message in identity_collision_messages(sets):
        diagnostics.append(ReferenceSetDiagnostic(1, message))
    return tuple(sets), tuple(diagnostics)


def _identity_owners(records: tuple[ReferenceRecord, ...]) -> dict[str, tuple[str, ...]]:
    owners: dict[str, list[str]] = {}
    for record in records:
        if not isinstance(record, ReferenceRecord):
            raise TypeError("records must contain ReferenceRecord values")
        for identity in record.identity_keys:
            owners.setdefault(identity, []).append(record.key)
    return {key: tuple(dict.fromkeys(values)) for key, values in owners.items()}


def canonicalize_reference_set(
    item: ReferenceSet,
    records: Iterable[ReferenceRecord],
) -> ReferenceSet:
    if not isinstance(item, ReferenceSet):
        raise TypeError("item must be ReferenceSet")
    snapshot = tuple(records)
    owners = _identity_owners(snapshot)
    canonical: list[str] = []
    for member in item.members:
        matches = owners.get(member, ())
        if not matches:
            raise ValueError(f"Reference Set member is missing: {member}")
        if len(matches) > 1:
            raise ValueError(f"Reference Set member is ambiguous: {member}")
        key = matches[0]
        if key not in canonical:
            canonical.append(key)
    return replace(item, members=tuple(canonical))


def reference_set_issues(
    sets: Iterable[ReferenceSet],
    records: Iterable[ReferenceRecord],
) -> tuple[ReferenceSetIssue, ...]:
    set_snapshot = tuple(sets)
    record_snapshot = tuple(records)
    owners = _identity_owners(record_snapshot)
    issues: list[ReferenceSetIssue] = []
    for item in set_snapshot:
        for member in item.members:
            matches = owners.get(member, ())
            if not matches:
                issues.append(ReferenceSetIssue(
                    "error", "reference-set-member-missing", item.name, member,
                    f"Reference Set member is unavailable: {member}.",
                ))
            elif len(matches) > 1:
                issues.append(ReferenceSetIssue(
                    "error", "reference-set-member-ambiguous", item.name, member,
                    f"Reference Set member is ambiguous: {member}.",
                ))
            elif matches[0] != member:
                issues.append(ReferenceSetIssue(
                    "warning", "reference-set-member-uses-alias", item.name, member,
                    f"Reference Set member should migrate from {member} to {matches[0]}.",
                ))
    return tuple(sorted(issues))


def replace_reference_set_member(
    sets: Iterable[ReferenceSet],
    old_key: str,
    new_key: str,
) -> tuple[tuple[ReferenceSet, ...], int]:
    changed: list[ReferenceSet] = []
    count = 0
    for item in sets:
        updated, occurrences = item.with_member_replacement(old_key, new_key)
        changed.append(updated)
        count += occurrences
    return tuple(changed), count
