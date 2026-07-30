"""GTK-free search and display helpers for Clip Collection."""
from __future__ import annotations

from typing import Any, Iterable


def normalized_query(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.casefold().split())


def clip_preview(text: Any, max_len: int = 100) -> str:
    if not isinstance(text, str):
        return ""
    first = next((" ".join(line.split()) for line in text.splitlines() if line.strip()), "")
    return first[:max_len] + ("…" if len(first) > max_len else "")


def search_clips(clips: Iterable[dict[str, Any]], query: Any) -> list[dict[str, Any]]:
    records = [dict(item) for item in clips if isinstance(item, dict)]
    needle = normalized_query(query)
    if not needle:
        return sorted(
            records,
            key=lambda item: (
                0 if normalized_query(item.get("shortcut", "")) else 1,
                normalized_query(item.get("shortcut", "")) or normalized_query(item.get("title", "")),
                normalized_query(item.get("title", "")),
                item.get("id", ""),
            ),
        )

    ranked: list[tuple[tuple[int, str, str, str], dict[str, Any]]] = []
    for item in records:
        shortcut = normalized_query(item.get("shortcut", ""))
        title = normalized_query(item.get("title", ""))
        body = normalized_query(item.get("text", ""))
        rank: int | None = None
        if shortcut == needle:
            rank = 0
        elif shortcut.startswith(needle):
            rank = 1
        elif title.startswith(needle):
            rank = 2
        elif needle in shortcut:
            rank = 3
        elif needle in title:
            rank = 4
        elif needle in body:
            rank = 5
        if rank is not None:
            ranked.append(((rank, shortcut, title, item.get("id", "")), item))
    ranked.sort(key=lambda pair: pair[0])
    return [item for _rank, item in ranked]


def duplicate_body_ids(clips: Iterable[dict[str, Any]], text: str, *, exclude_id: str = "") -> tuple[str, ...]:
    if not isinstance(text, str):
        return ()
    return tuple(
        item.get("id", "")
        for item in clips
        if isinstance(item, dict)
        and item.get("id") != exclude_id
        and item.get("text") == text
        and isinstance(item.get("id"), str)
    )
