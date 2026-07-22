"""Typed bibliographic reference records for Calamus academic writing."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import re
import unicodedata
from typing import Any, Iterable

_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_TYPES = (
    "book",
    "book-chapter",
    "journal-article",
    "encyclopedia-entry",
    "thesis",
    "conference-paper",
    "report",
    "institutional-document",
    "website",
    "manuscript",
    "other",
)


def reference_types() -> tuple[str, ...]:
    return _TYPES


def normalize_key(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def is_valid_reference_key(value: Any) -> bool:
    key = normalize_key(value)
    return bool(key and _KEY_RE.fullmatch(key))


def _single_line(value: Any) -> str:
    return " ".join(value.splitlines()).strip() if isinstance(value, str) else ""


def _clean_many(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = values.splitlines()
    clean: list[str] = []
    for value in values if isinstance(values, Iterable) else ():
        text = _single_line(value)
        if text and text not in clean:
            clean.append(text)
    return tuple(clean)


def _clean_tags(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = values.split(",")
    clean: list[str] = []
    for value in values if isinstance(values, Iterable) else ():
        tag = _single_line(value)
        if tag and tag not in clean:
            clean.append(tag)
    return tuple(clean)


@dataclass(frozen=True)
class ReferenceRecord:
    key: str
    title: str
    type: str = "book"
    authors: tuple[str, ...] = ()
    year: str = ""
    editors: tuple[str, ...] = ()
    container_title: str = ""
    publisher: str = ""
    location: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    isbn: str = ""
    issn: str = ""
    url: str = ""
    language: str = ""
    file_path: str = ""
    tags: tuple[str, ...] = ()
    annotation: str = ""
    extra_fields: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        key = normalize_key(self.key)
        title = _single_line(self.title)
        record_type = _single_line(self.type).lower() or "other"
        if not is_valid_reference_key(key):
            raise ValueError("reference key is invalid")
        if not title:
            raise ValueError("reference title is required")
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "type", record_type)
        object.__setattr__(self, "authors", _clean_many(self.authors))
        object.__setattr__(self, "editors", _clean_many(self.editors))
        object.__setattr__(self, "tags", _clean_tags(self.tags))
        for name in (
            "year", "container_title", "publisher", "location", "volume",
            "issue", "pages", "doi", "isbn", "issn", "url", "language",
            "file_path",
        ):
            object.__setattr__(self, name, _single_line(getattr(self, name)))
        object.__setattr__(
            self,
            "extra_fields",
            tuple(
                (_single_line(name), _single_line(value))
                for name, value in self.extra_fields
                if _single_line(name)
            ),
        )
        object.__setattr__(self, "annotation", self.annotation if isinstance(self.annotation, str) else "")

    @property
    def primary_author(self) -> str:
        return self.authors[0] if self.authors else ""

    @property
    def author_year(self) -> str:
        author = self.primary_author or "Unknown author"
        return f"{author}, {self.year}" if self.year else author

    @property
    def search_text(self) -> str:
        values = (
            self.key,
            self.title,
            self.type,
            self.year,
            *self.authors,
            *self.editors,
            self.container_title,
            self.publisher,
            self.location,
            self.doi,
            self.isbn,
            self.issn,
            self.url,
            *self.tags,
            self.annotation,
        )
        return "\n".join(values).casefold()

    def with_key(self, key: str) -> "ReferenceRecord":
        return replace(self, key=key)


def suggest_reference_key(
    authors: Any,
    year: Any,
    title: Any,
    existing_keys: Iterable[str] = (),
) -> str:
    """Return a predictable readable key, disambiguated with ``-a``, ``-b``."""
    author_items = _clean_many(authors)
    surname = author_items[0].split(",", 1)[0] if author_items else "reference"
    if author_items and "," not in author_items[0]:
        surname = author_items[0].split()[-1]
    title_words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", _single_line(title))
    stop = {"a", "an", "and", "the", "of", "in", "on", "for", "to", "di", "del", "della", "e", "il", "la"}
    title_word = next((word for word in title_words if word.casefold() not in stop), "work")
    raw = f"{surname}{_single_line(year)}{title_word}"
    normalized = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^A-Za-z0-9._:-]+", "", normalized).lower() or "reference"
    existing = {normalize_key(value) for value in existing_keys}
    if base not in existing:
        return base
    for suffix in "abcdefghijklmnopqrstuvwxyz":
        candidate = f"{base}-{suffix}"
        if candidate not in existing:
            return candidate
    number = 1
    while f"{base}-{number}" in existing:
        number += 1
    return f"{base}-{number}"
