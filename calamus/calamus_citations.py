"""Pandoc citation syntax and cursor lookup for Calamus academic writing."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable

from calamus_references import is_valid_reference_key, normalize_key

_KEY_BODY = r"[A-Za-z0-9](?:[A-Za-z0-9._:-]*[A-Za-z0-9_])?"
_CITATION_KEY_RE = re.compile(rf"^(?:{_KEY_BODY})$")
_ITEM_RE = re.compile(
    rf"(?<![A-Za-z0-9_@])@(?P<key>{_KEY_BODY})(?=$|[\s\],;.!?])"
)
_BRACKET_RE = re.compile(r"\[(?P<body>[^\]\n]*@[^\]\n]*)\]")
_FENCE_RE = re.compile(r"^[ \t]*(?P<mark>`{3,}|~{3,})")


@dataclass(frozen=True)
class CitationItem:
    key: str
    start: int
    end: int

    def __post_init__(self) -> None:
        key = normalize_key(self.key)
        if not is_valid_citation_key(key):
            raise ValueError("citation key is invalid")
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            raise TypeError("citation offsets must be integers")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("citation offsets are invalid")
        object.__setattr__(self, "key", key)


@dataclass(frozen=True)
class CitationCluster:
    start: int
    end: int
    items: tuple[CitationItem, ...]
    raw: str
    bracketed: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.start, int) or not isinstance(self.end, int):
            raise TypeError("cluster offsets must be integers")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("cluster offsets are invalid")
        if not self.items:
            raise ValueError("citation cluster requires at least one item")
        if any(item.start < self.start or item.end > self.end for item in self.items):
            raise ValueError("citation item lies outside cluster")
        object.__setattr__(self, "items", tuple(self.items))
        object.__setattr__(self, "raw", self.raw if isinstance(self.raw, str) else "")
        object.__setattr__(self, "bracketed", bool(self.bracketed))

    @property
    def keys(self) -> tuple[str, ...]:
        result: list[str] = []
        for item in self.items:
            if item.key not in result:
                result.append(item.key)
        return tuple(result)


@dataclass(frozen=True)
class CitationLookup:
    status: str
    key: str | None = None
    keys: tuple[str, ...] = ()
    cluster: CitationCluster | None = None

    def __post_init__(self) -> None:
        if self.status not in {"none", "unique", "ambiguous"}:
            raise ValueError("citation lookup status is invalid")
        keys = tuple(normalize_key(value) for value in self.keys if normalize_key(value))
        object.__setattr__(self, "keys", keys)
        if self.status == "unique":
            key = normalize_key(self.key)
            if not is_valid_reference_key(key):
                raise ValueError("unique citation lookup requires a valid key")
            object.__setattr__(self, "key", key)
        elif self.key is not None:
            object.__setattr__(self, "key", None)


def is_valid_citation_key(value: Any) -> bool:
    key = normalize_key(value)
    return bool(is_valid_reference_key(key) and _CITATION_KEY_RE.fullmatch(key))


def normalize_locator(value: Any) -> str:
    """Return a safe one-line Pandoc citation suffix without a leading comma."""
    if not isinstance(value, str):
        return ""
    locator = " ".join(part.strip() for part in value.splitlines() if part.strip()).strip()
    return locator.lstrip(",").strip()


def format_pandoc_citation(key: Any, locator: Any = "") -> str:
    key_text = normalize_key(key)
    if not is_valid_citation_key(key_text):
        raise ValueError("citation key is invalid")
    locator_text = normalize_locator(locator)
    if "]" in locator_text:
        raise ValueError("citation locator cannot contain a closing bracket")
    if locator_text:
        return f"[@{key_text}, {locator_text}]"
    return f"[@{key_text}]"


def _fenced_ranges(text: str) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    active_start: int | None = None
    active_char = ""
    active_len = 0
    offset = 0

    for line in text.splitlines(keepends=True):
        logical = line.rstrip("\r\n")
        match = _FENCE_RE.match(logical)
        if active_start is None:
            if match:
                mark = match.group("mark")
                active_start = offset
                active_char = mark[0]
                active_len = len(mark)
        elif match:
            mark = match.group("mark")
            if mark[0] == active_char and len(mark) >= active_len:
                ranges.append((active_start, offset + len(line)))
                active_start = None
                active_char = ""
                active_len = 0
        offset += len(line)

    if active_start is not None:
        ranges.append((active_start, len(text)))
    return tuple(ranges)


def _inside(ranges: Iterable[tuple[int, int]], offset: int) -> bool:
    return any(start <= offset < end for start, end in ranges)


def _inline_code_ranges(text: str, fenced: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    line_start = 0
    for line in text.splitlines(keepends=True):
        line_end = line_start + len(line)
        if not _inside(fenced, line_start):
            index = 0
            while index < len(line):
                if line[index] != "`":
                    index += 1
                    continue
                run_end = index + 1
                while run_end < len(line) and line[run_end] == "`":
                    run_end += 1
                mark = line[index:run_end]
                close = line.find(mark, run_end)
                if close < 0:
                    break
                ranges.append((line_start + index, line_start + close + len(mark)))
                index = close + len(mark)
        line_start = line_end
    return tuple(ranges)


def _excluded_ranges(text: str) -> tuple[tuple[int, int], ...]:
    fenced = _fenced_ranges(text)
    return tuple(sorted((*fenced, *_inline_code_ranges(text, fenced))))


def parse_citation_clusters(text: Any) -> tuple[CitationCluster, ...]:
    """Parse bracketed and bare Pandoc citations, excluding Markdown code."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    excluded = _excluded_ranges(text)
    clusters: list[CitationCluster] = []

    for match in _BRACKET_RE.finditer(text):
        if _inside(excluded, match.start()):
            continue
        items: list[CitationItem] = []
        body_start = match.start("body")
        for item_match in _ITEM_RE.finditer(match.group("body")):
            key_start = body_start + item_match.start("key")
            key_end = body_start + item_match.end("key")
            if _inside(excluded, key_start):
                continue
            items.append(CitationItem(item_match.group("key"), key_start, key_end))
        if items:
            clusters.append(
                CitationCluster(
                    start=match.start(),
                    end=match.end(),
                    items=tuple(items),
                    raw=match.group(0),
                    bracketed=True,
                )
            )

    bracket_ranges = tuple((cluster.start, cluster.end) for cluster in clusters)
    for match in _ITEM_RE.finditer(text):
        at_start = match.start("key") - 1
        if _inside(excluded, at_start) or _inside(bracket_ranges, at_start):
            continue
        item = CitationItem(match.group("key"), match.start("key"), match.end("key"))
        clusters.append(
            CitationCluster(
                start=at_start,
                end=match.end("key"),
                items=(item,),
                raw=text[at_start:match.end("key")],
                bracketed=False,
            )
        )

    clusters.sort(key=lambda cluster: (cluster.start, cluster.end))
    return tuple(clusters)


def citation_lookup_at(text: Any, offset: Any) -> CitationLookup:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(offset, int) or isinstance(offset, bool):
        raise TypeError("offset must be an integer")
    position = max(0, min(len(text), offset))

    for cluster in parse_citation_clusters(text):
        if not (cluster.start <= position < cluster.end):
            continue
        for item in cluster.items:
            # Include the @ sign and the position immediately after the key.
            if item.start - 1 <= position < item.end:
                return CitationLookup("unique", key=item.key, keys=(item.key,), cluster=cluster)
        keys = cluster.keys
        if len(keys) == 1:
            return CitationLookup("unique", key=keys[0], keys=keys, cluster=cluster)
        return CitationLookup("ambiguous", keys=keys, cluster=cluster)

    return CitationLookup("none")


def cited_keys(text: Any) -> tuple[str, ...]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    keys: list[str] = []
    for cluster in parse_citation_clusters(text):
        for key in cluster.keys:
            if key not in keys:
                keys.append(key)
    return tuple(keys)
