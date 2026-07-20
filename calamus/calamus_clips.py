"""Canonical user-content persistence for Clip Collection.

Clip content is stored in UTF-8 Markdown. ``clips.json`` is read only as a
legacy migration source when no canonical Markdown file exists; it is never a
second write target or a competing authority.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

from calamus_config import load_json_file

_HEADER = "# Calamus Clip Collection v1"
_CREATED_PREFIX = "Created: "
_FENCE_RE = re.compile(r"^(`{3,})(?:text)?\s*$")


def clips_path(config_dir: str) -> str:
    return os.path.join(config_dir, "clips.md")


def legacy_clips_path(config_dir: str) -> str:
    return os.path.join(config_dir, "clips.json")


def load_clips(config_dir: str, limit: int = 200) -> list[dict[str, str]]:
    """Load canonical Markdown, importing read-only legacy JSON only if absent."""
    path = clips_path(config_dir)
    if os.path.exists(path):
        return parse_clips_markdown(_read_text(path))[:limit]

    legacy = _load_legacy_clips(config_dir, limit)
    if legacy:
        # Best-effort one-time migration. Legacy JSON is retained byte-for-byte
        # as a read-only backup and is never synchronized or rewritten.
        save_clips(config_dir, legacy, limit)
    return legacy[:limit]


def save_clips(config_dir: str, clips: list[dict[str, Any]], limit: int = 200) -> bool:
    return _write_text_atomic(
        clips_path(config_dir),
        serialize_clips_markdown(_clean_clips(clips)[:limit]),
    )


def serialize_clips_markdown(clips: list[dict[str, Any]]) -> str:
    lines = [_HEADER, ""]
    for item in _clean_clips(clips):
        title = _heading_text(item["title"])
        created = _single_line(item.get("created", ""))
        text = item["text"]
        fence = "`" * max(3, _longest_backtick_run(text) + 1)
        lines.extend(
            [
                f"## {title}",
                "",
                f"{_CREATED_PREFIX}{created}" if created else _CREATED_PREFIX,
                "",
                f"{fence}text",
                text,
                fence,
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def parse_clips_markdown(text: Any) -> list[dict[str, str]]:
    if not isinstance(text, str):
        return []
    lines = text.splitlines()
    clips: list[dict[str, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("## "):
            index += 1
            continue
        title = line[3:].strip() or "Clip"
        index += 1
        created = ""
        while index < len(lines):
            current = lines[index]
            if current.startswith("## "):
                break
            if current.startswith(_CREATED_PREFIX):
                created = current[len(_CREATED_PREFIX):].strip()
            match = _FENCE_RE.match(current)
            if match:
                fence = match.group(1)
                index += 1
                body: list[str] = []
                while index < len(lines) and lines[index] != fence:
                    body.append(lines[index])
                    index += 1
                if index < len(lines) and lines[index] == fence:
                    clips.append(
                        {
                            "title": title,
                            "text": "\n".join(body),
                            "created": created,
                        }
                    )
                    index += 1
                break
            index += 1
    return clips


def clip_title_from_text(text: str, max_len: int = 40) -> str:
    first = " ".join(text.strip().split())
    if not first:
        return "Empty clip"
    return first[:max_len] + ("…" if len(first) > max_len else "")


def new_clip(title: str, text: str) -> dict[str, str]:
    return {
        "title": title or clip_title_from_text(text),
        "text": text,
        "created": datetime.now().isoformat(timespec="seconds"),
    }


def _load_legacy_clips(config_dir: str, limit: int) -> list[dict[str, str]]:
    return _clean_clips(load_json_file(legacy_clips_path(config_dir), []))[:limit]


def _clean_clips(items: Any) -> list[dict[str, str]]:
    clips: list[dict[str, str]] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            continue
        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            title = clip_title_from_text(item["text"])
        created = item.get("created")
        clips.append(
            {
                "title": title,
                "text": item["text"],
                "created": created if isinstance(created, str) else "",
            }
        )
    return clips


def _heading_text(value: str) -> str:
    return _single_line(value).strip() or "Clip"


def _single_line(value: Any) -> str:
    return " ".join(value.splitlines()) if isinstance(value, str) else ""


def _longest_backtick_run(text: str) -> int:
    longest = current = 0
    for char in text:
        if char == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def _write_text_atomic(path: str, text: str) -> bool:
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass
        return False
