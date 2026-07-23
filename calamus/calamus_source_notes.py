"""Typed document-specific Source Notes for Calamus academic writing."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
import re
import uuid
from typing import Any, Iterable

from calamus_document_structure import is_valid_heading_identifier
from calamus_references import is_valid_reference_key, normalize_key

_NOTE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_KINDS = ("quote", "paraphrase", "comment")


def source_note_kinds() -> tuple[str, ...]:
    return _KINDS


def _single_line(value: Any) -> str:
    return " ".join(value.splitlines()).strip() if isinstance(value, str) else ""


def _clean_tags(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = values.split(",")
    clean: list[str] = []
    for value in values if isinstance(values, Iterable) else ():
        tag = _single_line(value)
        if tag and tag not in clean:
            clean.append(tag)
    return tuple(clean)


def normalize_source_note_id(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def normalize_heading_target(value: Any) -> str:
    target = _single_line(value)
    if not target:
        return ""
    identifier = target[1:] if target.startswith("#") else target
    if not is_valid_heading_identifier(identifier):
        raise ValueError("source note target is invalid")
    return f"#{identifier}"


def is_valid_source_note_id(value: Any) -> bool:
    note_id = normalize_source_note_id(value)
    return bool(note_id and _NOTE_ID_RE.fullmatch(note_id))


def new_source_note_id(
    existing_ids: Iterable[str] = (),
    *,
    now: datetime | None = None,
    token: str | None = None,
) -> str:
    moment = now or datetime.now().astimezone()
    stamp = moment.strftime("%Y%m%d-%H%M%S")
    suffix = re.sub(r"[^A-Za-z0-9]+", "", token or uuid.uuid4().hex[:6]).lower()[:8] or "note"
    base = f"sn-{stamp}-{suffix}"
    existing = {normalize_source_note_id(value) for value in existing_ids}
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
class SourceLocator:
    page: str = ""
    page_end: str = ""
    chapter: str = ""
    section: str = ""
    paragraph: str = ""

    def __post_init__(self) -> None:
        for name in ("page", "page_end", "chapter", "section", "paragraph"):
            object.__setattr__(self, name, _single_line(getattr(self, name)))

    @property
    def display(self) -> str:
        values: list[str] = []
        if self.page:
            page = self.page
            if self.page_end and self.page_end != self.page:
                page = f"{page}–{self.page_end}"
            values.append(f"p. {page}")
        elif self.page_end:
            values.append(f"p. {self.page_end}")
        if self.chapter:
            values.append(f"ch. {self.chapter}")
        if self.section:
            values.append(f"sec. {self.section}")
        if self.paragraph:
            values.append(f"para. {self.paragraph}")
        return ", ".join(values)

    @property
    def search_text(self) -> str:
        return "\n".join(
            (self.page, self.page_end, self.chapter, self.section, self.paragraph)
        ).casefold()


@dataclass(frozen=True)
class SourceNote:
    id: str
    kind: str
    text: str
    reference_key: str = ""
    locator: SourceLocator = field(default_factory=SourceLocator)
    comment: str = ""
    tags: tuple[str, ...] = ()
    created: str = ""
    modified: str = ""
    extra_fields: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    target: str = ""

    def __post_init__(self) -> None:
        note_id = normalize_source_note_id(self.id)
        kind = _single_line(self.kind).lower()
        text = self.text.strip() if isinstance(self.text, str) else ""
        reference_key = normalize_key(self.reference_key)
        target = normalize_heading_target(self.target)
        if not is_valid_source_note_id(note_id):
            raise ValueError("source note id is invalid")
        if kind not in _KINDS:
            raise ValueError("source note kind is invalid")
        if not text:
            raise ValueError("source note text is required")
        if reference_key and not is_valid_reference_key(reference_key):
            raise ValueError("source note reference key is invalid")
        if kind in {"quote", "paraphrase"} and not reference_key:
            raise ValueError(f"{kind} source notes require a reference key")
        locator = self.locator if isinstance(self.locator, SourceLocator) else SourceLocator()
        object.__setattr__(self, "id", note_id)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "text", text)
        object.__setattr__(self, "reference_key", reference_key)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "locator", locator)
        object.__setattr__(self, "comment", self.comment.strip() if isinstance(self.comment, str) else "")
        object.__setattr__(self, "tags", _clean_tags(self.tags))
        object.__setattr__(self, "created", _single_line(self.created))
        object.__setattr__(self, "modified", _single_line(self.modified))
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
        compact = " ".join(self.text.split())
        return compact if len(compact) <= 100 else compact[:97].rstrip() + "…"

    @property
    def locator_text(self) -> str:
        return self.locator.display

    @property
    def search_text(self) -> str:
        return "\n".join(
            (
                self.id,
                self.kind,
                self.reference_key,
                self.target,
                self.text,
                self.comment,
                *self.tags,
                self.locator.search_text,
            )
        ).casefold()

    def revised(self, *, modified: str, **changes: Any) -> "SourceNote":
        return replace(self, modified=modified, **changes)
