"""Typed, document-local Scratchpad entries for Calamus."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
import re
import uuid
from typing import Any, Iterable

from calamus_document_structure import is_valid_heading_identifier

_ENTRY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_TYPES = ("note", "idea", "draft", "task")
_STATES = ("inbox", "active", "resolved", "archived")


def scratchpad_types() -> tuple[str, ...]:
    return _TYPES


def scratchpad_states() -> tuple[str, ...]:
    return _STATES


def _single_line(value: Any) -> str:
    return " ".join(value.splitlines()).strip() if isinstance(value, str) else ""


def _clean_tags(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = values.split(",")
    clean: list[str] = []
    identities: set[str] = set()
    for value in values if isinstance(values, Iterable) else ():
        tag = _single_line(value)
        identity = tag.casefold()
        if tag and identity not in identities:
            clean.append(tag)
            identities.add(identity)
    return tuple(clean)


def normalize_entry_id(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def is_valid_entry_id(value: Any) -> bool:
    entry_id = normalize_entry_id(value)
    return bool(entry_id and _ENTRY_ID_RE.fullmatch(entry_id))


def normalize_heading_target(value: Any) -> str:
    target = _single_line(value)
    if not target:
        return ""
    identifier = target[1:] if target.startswith("#") else target
    if not is_valid_heading_identifier(identifier):
        raise ValueError("scratchpad section target is invalid")
    return f"#{identifier}"


def _clean_targets(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = values.split(",")
    clean: list[str] = []
    for value in values if isinstance(values, Iterable) else ():
        target = normalize_heading_target(value)
        if target and target not in clean:
            clean.append(target)
    return tuple(clean)


def new_scratchpad_id(
    existing_ids: Iterable[str] = (),
    *,
    now: datetime | None = None,
    token: str | None = None,
) -> str:
    moment = now or datetime.now().astimezone()
    stamp = moment.strftime("%Y%m%d-%H%M%S")
    suffix = re.sub(r"[^A-Za-z0-9]+", "", token or uuid.uuid4().hex[:6]).lower()[:8] or "item"
    base = f"sp-{stamp}-{suffix}"
    existing = {normalize_entry_id(value) for value in existing_ids}
    if base not in existing:
        return base
    number = 2
    while f"{base}-{number}" in existing:
        number += 1
    return f"{base}-{number}"


def now_iso(moment: datetime | None = None) -> str:
    value = moment or datetime.now().astimezone()
    return value.isoformat(timespec="seconds")


@dataclass(frozen=True)
class ScratchpadEntry:
    id: str
    type: str
    title: str
    body: str
    status: str = "inbox"
    tags: tuple[str, ...] = ()
    sections: tuple[str, ...] = ()
    created: str = ""
    updated: str = ""
    extra_fields: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        entry_id = normalize_entry_id(self.id)
        entry_type = _single_line(self.type).lower()
        title = _single_line(self.title)
        status = _single_line(self.status).lower()
        body = self.body.strip() if isinstance(self.body, str) else ""
        if not is_valid_entry_id(entry_id):
            raise ValueError("scratchpad entry id is invalid")
        if entry_type not in _TYPES:
            raise ValueError("scratchpad entry type is invalid")
        if not title:
            raise ValueError("scratchpad entry title is required")
        if status not in _STATES:
            raise ValueError("scratchpad entry status is invalid")
        object.__setattr__(self, "id", entry_id)
        object.__setattr__(self, "type", entry_type)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "tags", _clean_tags(self.tags))
        object.__setattr__(self, "sections", _clean_targets(self.sections))
        object.__setattr__(self, "created", _single_line(self.created))
        object.__setattr__(self, "updated", _single_line(self.updated))
        object.__setattr__(
            self,
            "extra_fields",
            tuple(
                (_single_line(name), _single_line(value))
                for name, value in self.extra_fields
                if _single_line(name)
            ),
        )

    @property
    def excerpt(self) -> str:
        compact = " ".join(self.body.split())
        if not compact:
            return "(No body text)"
        return compact if len(compact) <= 110 else compact[:107].rstrip() + "…"

    @property
    def search_text(self) -> str:
        return "\n".join(
            (self.id, self.type, self.title, self.status, self.body, *self.tags, *self.sections)
        ).casefold()

    def revised(self, *, updated: str, **changes: Any) -> "ScratchpadEntry":
        return replace(self, updated=updated, **changes)
