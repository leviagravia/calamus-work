"""Canonical UTF-8 Markdown authority for the global Clip Collection.

W95 upgrades the legacy positional v1 format to a stable-ID v2 authority.
The module is GTK-free: parsing, validation, migration, stale detection and
atomic persistence are available to headless tests and non-GUI callers.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
import re
import tempfile
import uuid
from typing import Any, Iterable

_HEADER_V1 = "# Calamus Clip Collection v1"
_HEADER_V2 = "# Calamus Clip Collection v2"
_HEADER_RE = re.compile(r"^# Calamus Clip Collection v([12])\s*$")
_FENCE_RE = re.compile(r"^(`{3,})(?:text)?\s*$")
_ID_RE = re.compile(r"^clip-[0-9a-f]{32}$")
_SHORTCUT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
_METADATA_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 _-]*):\s*(.*)$")
_KNOWN_METADATA = {"id", "shortcut", "created", "updated"}
_MISSING_REVISION = "missing"


class ClipError(RuntimeError):
    """Base class for controlled Clip Collection failures."""


class ClipFormatError(ClipError):
    """The Markdown authority cannot be parsed without guessing."""


class ClipValidationError(ClipError):
    """One requested clip or collection violates the frozen contract."""


class ClipConflictError(ClipError):
    """The authority changed after the caller loaded it."""


class ClipLimitError(ClipValidationError):
    """The collection exceeds its explicit maximum."""


@dataclass(frozen=True)
class ClipSnapshot:
    clips: tuple[dict[str, Any], ...]
    revision: str
    path: str
    migrated: bool = False

    def mutable_clips(self) -> list[dict[str, Any]]:
        return [_copy_clip(item) for item in self.clips]


def clips_path(config_dir: str) -> str:
    return os.path.join(config_dir, "clips.md")


def legacy_clips_path(config_dir: str) -> str:
    return os.path.join(config_dir, "clips.json")


def clip_revision(path: str) -> str:
    """Return a byte-authoritative token, including the missing-file state."""
    try:
        with open(path, "rb") as handle:
            payload = handle.read()
    except FileNotFoundError:
        return _MISSING_REVISION
    except OSError as error:
        raise ClipError(f"Could not read Clip Collection revision: {error}") from error
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def validate_shortcut(value: Any) -> str:
    shortcut = value.strip().casefold() if isinstance(value, str) else ""
    if not shortcut:
        return ""
    if not _SHORTCUT_RE.fullmatch(shortcut):
        raise ClipValidationError(
            "Shortcut must contain 1–32 lowercase letters, numbers, '-' or '_', "
            "and must begin with a letter or number."
        )
    return shortcut


def validate_clip_id(value: Any) -> str:
    clip_id = value.strip() if isinstance(value, str) else ""
    if not _ID_RE.fullmatch(clip_id):
        raise ClipValidationError(f"Invalid Clip ID: {clip_id or '<missing>'}")
    return clip_id


def clip_title_from_text(text: str, max_len: int = 40) -> str:
    first = " ".join(text.strip().split())
    if not first:
        return "Empty clip"
    return first[:max_len] + ("…" if len(first) > max_len else "")


def new_clip(title: str, text: str, shortcut: str = "") -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ClipValidationError("Clip body cannot be empty.")
    now = _now_iso()
    return {
        "id": "clip-" + uuid.uuid4().hex,
        "title": _heading_text(title) if isinstance(title, str) and title.strip() else clip_title_from_text(text),
        "shortcut": validate_shortcut(shortcut),
        "text": text,
        "created": now,
        "updated": now,
        "extra_fields": (),
    }


def clone_clip(item: dict[str, Any], *, title: str | None = None) -> dict[str, Any]:
    text = item.get("text", "") if isinstance(item, dict) else ""
    cloned = new_clip(title or f"Copy of {item.get('title', 'Clip')}", text, "")
    cloned["extra_fields"] = tuple(item.get("extra_fields", ()))
    return cloned


def update_clip(
    item: dict[str, Any],
    *,
    title: str,
    text: str,
    shortcut: str,
) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise ClipValidationError("Clip body cannot be empty.")
    updated = _copy_clip(item)
    updated.update(
        {
            "id": validate_clip_id(item.get("id")),
            "title": _heading_text(title) if isinstance(title, str) and title.strip() else clip_title_from_text(text),
            "shortcut": validate_shortcut(shortcut),
            "text": text,
            "updated": _now_iso(),
        }
    )
    return updated


def validate_clips(items: Any, *, limit: int = 200) -> list[dict[str, Any]]:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    if not isinstance(items, (list, tuple)):
        raise ClipValidationError("Clip Collection must be a list of records.")
    if len(items) > limit:
        raise ClipLimitError(f"Clip Collection contains {len(items)} records; the limit is {limit}.")

    clean: list[dict[str, Any]] = []
    ids: set[str] = set()
    shortcuts: dict[str, str] = {}
    for position, raw in enumerate(items, start=1):
        if not isinstance(raw, dict):
            raise ClipValidationError(f"Clip {position} is not a record.")
        text = raw.get("text")
        if not isinstance(text, str):
            raise ClipValidationError(f"Clip {position} has no text body.")
        clip_id = validate_clip_id(raw.get("id"))
        if clip_id in ids:
            raise ClipValidationError(f"Duplicate Clip ID: {clip_id}")
        ids.add(clip_id)
        shortcut = validate_shortcut(raw.get("shortcut", ""))
        if shortcut:
            if shortcut in shortcuts:
                raise ClipValidationError(
                    f"Shortcut '{shortcut}' is already used by {shortcuts[shortcut]}."
                )
            shortcuts[shortcut] = clip_id
        title = raw.get("title")
        if not isinstance(title, str) or not title.strip():
            title = clip_title_from_text(text)
        created = raw.get("created") if isinstance(raw.get("created"), str) else ""
        updated = raw.get("updated") if isinstance(raw.get("updated"), str) else created
        extra_fields = _clean_extra_fields(raw.get("extra_fields", ()))
        clean.append(
            {
                "id": clip_id,
                "title": _heading_text(title),
                "shortcut": shortcut,
                "text": text,
                "created": created,
                "updated": updated,
                "extra_fields": extra_fields,
            }
        )
    return clean


def serialize_clips_markdown(clips: list[dict[str, Any]]) -> str:
    records = _coerce_input_records(clips, limit=max(1, len(clips) or 1))
    lines = [_HEADER_V2, ""]
    for item in records:
        fence = "`" * max(3, _longest_backtick_run(item["text"]) + 1)
        lines.extend(
            [
                f"## {_heading_text(item['title'])}",
                "",
                f"ID: {item['id']}",
                f"Shortcut: {item['shortcut']}",
                f"Created: {_single_line(item.get('created', ''))}",
                f"Updated: {_single_line(item.get('updated', ''))}",
            ]
        )
        for key, value in item.get("extra_fields", ()):
            lines.append(f"{key}: {_single_line(value)}")
        lines.extend(["", f"{fence}text", item["text"], fence, ""])
    return "\n".join(lines).rstrip() + "\n"


def parse_clips_markdown(text: Any, *, strict: bool = False) -> list[dict[str, Any]]:
    try:
        _version, records = parse_clips_document(text)
        return records
    except ClipError:
        if strict:
            raise
        return []


def parse_clips_document(text: Any) -> tuple[int, list[dict[str, Any]]]:
    if not isinstance(text, str):
        raise ClipFormatError("Clip Collection is not UTF-8 text.")
    lines = text.splitlines()
    first = next((line.strip() for line in lines if line.strip()), "")
    match = _HEADER_RE.fullmatch(first)
    if not match:
        raise ClipFormatError("Clip Collection header is missing or unsupported.")
    version = int(match.group(1))
    records: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("## "):
            index += 1
            continue
        title = line[3:].strip() or "Clip"
        index += 1
        metadata: list[tuple[str, str]] = []
        fence = ""
        while index < len(lines):
            current = lines[index]
            if current.startswith("## "):
                raise ClipFormatError(f"Clip '{title}' has no fenced body.")
            fence_match = _FENCE_RE.fullmatch(current)
            if fence_match:
                fence = fence_match.group(1)
                index += 1
                break
            metadata_match = _METADATA_RE.fullmatch(current)
            if metadata_match:
                metadata.append((metadata_match.group(1).strip(), metadata_match.group(2).strip()))
            index += 1
        if not fence:
            raise ClipFormatError(f"Clip '{title}' has no fenced body.")
        body: list[str] = []
        while index < len(lines) and lines[index] != fence:
            body.append(lines[index])
            index += 1
        if index >= len(lines):
            raise ClipFormatError(f"Clip '{title}' has an unterminated fenced body.")
        index += 1
        fields: dict[str, str] = {}
        extras: list[tuple[str, str]] = []
        for key, value in metadata:
            normalized = key.casefold()
            if normalized in _KNOWN_METADATA:
                if normalized in fields:
                    raise ClipFormatError(f"Clip '{title}' repeats metadata field {key}.")
                fields[normalized] = value
            else:
                extras.append((key, value))
        records.append(
            {
                "id": fields.get("id", ""),
                "title": title,
                "shortcut": fields.get("shortcut", ""),
                "text": "\n".join(body),
                "created": fields.get("created", ""),
                "updated": fields.get("updated", fields.get("created", "")),
                "extra_fields": tuple(extras),
            }
        )
    if version == 2:
        return version, validate_clips(records, limit=max(1, len(records) or 1))
    return version, _migrate_records(records)


def load_clips(config_dir: str, limit: int = 200) -> list[dict[str, Any]]:
    return MarkdownClipStore(config_dir).load_snapshot(limit=limit).mutable_clips()


def save_clips(config_dir: str, clips: list[dict[str, Any]], limit: int = 200) -> bool:
    store = MarkdownClipStore(config_dir)
    try:
        candidate = _coerce_input_records(clips, limit=limit)
        store.save_snapshot(candidate, expected_revision=store.current_revision(), limit=limit)
        return True
    except ClipError:
        return False


class MarkdownClipStore:
    """Versioned, stale-safe owner of ``clips.md``."""

    def __init__(self, config_dir: str) -> None:
        if not isinstance(config_dir, str) or not config_dir:
            raise ValueError("config_dir is required")
        self.config_dir = config_dir
        self.path = clips_path(config_dir)
        self.legacy_path = legacy_clips_path(config_dir)

    def current_revision(self) -> str:
        return clip_revision(self.path)

    def load_snapshot(self, limit: int = 200) -> ClipSnapshot:
        revision = self.current_revision()
        if revision != _MISSING_REVISION:
            raw = _read_utf8(self.path)
            version, records = parse_clips_document(raw)
            if len(records) > limit:
                raise ClipLimitError(
                    f"Clip Collection contains {len(records)} records; the limit is {limit}."
                )
            if version == 1:
                return self.save_snapshot(records, expected_revision=revision, limit=limit, migrated=True)
            clean = validate_clips(records, limit=limit)
            return ClipSnapshot(tuple(_copy_clip(item) for item in clean), revision, self.path, False)

        legacy = self._load_legacy(limit)
        if legacy:
            return self.save_snapshot(legacy, expected_revision=_MISSING_REVISION, limit=limit, migrated=True)
        return ClipSnapshot((), _MISSING_REVISION, self.path, False)

    def ensure_file(self, limit: int = 200) -> ClipSnapshot:
        snapshot = self.load_snapshot(limit)
        if snapshot.revision != _MISSING_REVISION:
            return snapshot
        return self.save_snapshot([], expected_revision=_MISSING_REVISION, limit=limit)

    def save_snapshot(
        self,
        clips: Iterable[dict[str, Any]],
        *,
        expected_revision: str,
        limit: int = 200,
        migrated: bool = False,
    ) -> ClipSnapshot:
        candidate = validate_clips(list(clips), limit=limit)
        current = self.current_revision()
        if current != expected_revision:
            raise ClipConflictError("Clip Collection changed outside Calamus. Refresh and repeat the operation.")
        payload = serialize_clips_markdown(candidate)
        _write_text_atomic_checked(self.path, payload, expected_revision)
        revision = self.current_revision()
        return ClipSnapshot(tuple(_copy_clip(item) for item in candidate), revision, self.path, migrated)

    def _load_legacy(self, limit: int) -> list[dict[str, Any]]:
        if not os.path.exists(self.legacy_path):
            return []
        try:
            with open(self.legacy_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ClipFormatError(f"Could not read legacy clips.json: {error}") from error
        if not isinstance(raw, list):
            raise ClipFormatError("Legacy clips.json is not a list.")
        if len(raw) > limit:
            raise ClipLimitError(f"Legacy Clip Collection contains {len(raw)} records; the limit is {limit}.")
        records: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                raise ClipFormatError("Legacy clips.json contains an invalid record.")
            records.append(
                {
                    "id": "",
                    "title": item.get("title", ""),
                    "shortcut": "",
                    "text": item["text"],
                    "created": item.get("created", "") if isinstance(item.get("created"), str) else "",
                    "updated": item.get("created", "") if isinstance(item.get("created"), str) else "",
                    "extra_fields": (),
                }
            )
        return _migrate_records(records)



def _coerce_input_records(items: Any, *, limit: int) -> list[dict[str, Any]]:
    """Upgrade legacy in-memory dictionaries used by compatibility callers."""
    if not isinstance(items, (list, tuple)):
        raise ClipValidationError("Clip Collection must be a list of records.")
    if len(items) > limit:
        raise ClipLimitError(f"Clip Collection contains {len(items)} records; the limit is {limit}.")
    upgraded: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
            raise ClipValidationError("Clip Collection contains an invalid record.")
        text = raw["text"]
        created = raw.get("created") if isinstance(raw.get("created"), str) else ""
        if not created:
            created = _now_iso()
        clip_id = raw.get("id") if isinstance(raw.get("id"), str) else ""
        if not _ID_RE.fullmatch(clip_id):
            clip_id = "clip-" + uuid.uuid4().hex
        upgraded.append({
            "id": clip_id,
            "title": raw.get("title") if isinstance(raw.get("title"), str) and raw.get("title", "").strip() else clip_title_from_text(text),
            "shortcut": raw.get("shortcut", "") if isinstance(raw.get("shortcut", ""), str) else "",
            "text": text,
            "created": created,
            "updated": raw.get("updated") if isinstance(raw.get("updated"), str) and raw.get("updated") else created,
            "extra_fields": _clean_extra_fields(raw.get("extra_fields", ())),
        })
    return validate_clips(upgraded, limit=limit)

def _migrate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    migrated: list[dict[str, Any]] = []
    for item in records:
        created = item.get("created") if isinstance(item.get("created"), str) else ""
        if not created:
            created = _now_iso()
        text = item.get("text") if isinstance(item.get("text"), str) else ""
        migrated.append(
            {
                "id": "clip-" + uuid.uuid4().hex,
                "title": _heading_text(item.get("title", "")) or clip_title_from_text(text),
                "shortcut": "",
                "text": text,
                "created": created,
                "updated": item.get("updated") if isinstance(item.get("updated"), str) and item.get("updated") else created,
                "extra_fields": _clean_extra_fields(item.get("extra_fields", ())),
            }
        )
    return validate_clips(migrated, limit=max(1, len(migrated) or 1))


def _copy_clip(item: dict[str, Any]) -> dict[str, Any]:
    copied = dict(item)
    copied["extra_fields"] = tuple(item.get("extra_fields", ()))
    return copied


def _clean_extra_fields(value: Any) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for pair in value if isinstance(value, (list, tuple)) else ():
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            continue
        key, item_value = pair
        if not isinstance(key, str) or not key.strip() or key.casefold() in _KNOWN_METADATA:
            continue
        result.append((_single_line(key).strip(), _single_line(item_value)))
    return tuple(result)


def _heading_text(value: Any) -> str:
    return _single_line(value).strip().replace("#", "＃") or "Clip"


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


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_utf8(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeError) as error:
        raise ClipFormatError(f"Could not read clips.md: {error}") from error


def _write_text_atomic_checked(path: str, text: str, expected_revision: str) -> None:
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=directory,
            prefix=".clips-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if clip_revision(path) != expected_revision:
            raise ClipConflictError("Clip Collection changed while Calamus was preparing the save.")
        os.replace(temp_path, path)
        temp_path = ""
        try:
            directory_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
    except ClipError:
        raise
    except OSError as error:
        raise ClipError(f"Could not save Clip Collection: {error}") from error
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
