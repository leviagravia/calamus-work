"""Configuration and small persistent stores for Calamus."""
from __future__ import annotations

import json
import os
from typing import Any

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "calamus")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
RECENT_FILE = os.path.join(CONFIG_DIR, "recent.json")
FAVOURITES_FILE = os.path.join(CONFIG_DIR, "favourites.json")


def clamp_int(value: Any, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def _copy_default(default: Any) -> Any:
    if isinstance(default, dict):
        return default.copy()
    if isinstance(default, list):
        return list(default)
    return default


def load_json_file(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(default, dict) and not isinstance(data, dict):
            return default.copy()
        if isinstance(default, list) and not isinstance(data, list):
            return list(default)
        return data
    except (OSError, json.JSONDecodeError):
        return _copy_default(default)


def save_json_file(path: str, data: Any) -> bool:
    tmp = path + ".tmp"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass
        return False


def _clean_existing_paths(items: Any, limit: int) -> list[str]:
    if not isinstance(items, list):
        return []
    result: list[str] = []
    for item in items:
        if isinstance(item, str) and os.path.exists(item) and item not in result:
            result.append(item)
        if len(result) >= limit:
            break
    return result


def load_settings() -> dict[str, Any]:
    data = load_json_file(SETTINGS_FILE, {})
    return data if isinstance(data, dict) else {}


def save_settings(data: dict[str, Any]) -> bool:
    return save_json_file(SETTINGS_FILE, data)


def load_recent_files(limit: int = 10) -> list[str]:
    return _clean_existing_paths(load_json_file(RECENT_FILE, []), limit)


def save_recent_files(items: list[str], limit: int = 10) -> bool:
    clean: list[str] = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, str) and item and item not in clean:
            clean.append(item)
    return save_json_file(RECENT_FILE, clean[:limit])


def add_recent_file(path: str, limit: int = 10) -> list[str]:
    if not path:
        return load_recent_files(limit)
    path = os.path.abspath(path)
    items = [x for x in load_recent_files(limit) if x != path]
    items.insert(0, path)
    save_recent_files(items, limit)
    return items[:limit]


def load_favourite_store(limit: int = 50) -> list[str]:
    """Load the canonical Favorite path list without availability filtering."""
    clean: list[str] = []
    for item in load_json_file(FAVOURITES_FILE, []):
        if isinstance(item, str) and item and item not in clean:
            clean.append(item)
        if len(clean) >= limit:
            break
    return clean


def load_favourites(limit: int = 50) -> list[str]:
    return _clean_existing_paths(load_favourite_store(limit), limit)


def save_favourites(items: list[str], limit: int = 50) -> bool:
    clean: list[str] = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, str) and item and item not in clean:
            clean.append(item)
    return save_json_file(FAVOURITES_FILE, clean[:limit])
