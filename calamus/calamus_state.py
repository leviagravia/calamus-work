"""Persistent application state for Calamus.

This module centralizes settings, session data, recent files, favourites,
clips, and template paths. It intentionally remains a thin layer over the
existing JSON stores so user data stays backward compatible.
"""
from __future__ import annotations

import os
from typing import Any

from calamus_config import (
    CONFIG_DIR,
    SETTINGS_FILE,
    SESSION_FILE,
    RECENT_FILE,
    FAVOURITES_FILE,
    clamp_int,
    load_json_file,
    save_json_file,
    load_settings,
    save_settings,
    load_recent_files,
    save_recent_files,
    add_recent_file,
    load_favourite_store,
    load_favourites,
    save_favourites,
)
from calamus_clips import load_clips, save_clips


class StateManager:
    """Small compatibility layer for all persistent Calamus state."""

    def __init__(self, config_dir: str = CONFIG_DIR):
        self.config_dir = config_dir
        self.settings_file = os.path.join(config_dir, "settings.json")
        self.session_file = os.path.join(config_dir, "session.json")
        self.recent_file = os.path.join(config_dir, "recent.json")
        self.favourites_file = os.path.join(config_dir, "favourites.json")

    def ensure_dir(self) -> None:
        os.makedirs(self.config_dir, exist_ok=True)

    def load_settings(self) -> dict[str, Any]:
        if self.config_dir == CONFIG_DIR:
            return load_settings()
        data = load_json_file(self.settings_file, {})
        return data if isinstance(data, dict) else {}

    def save_settings(self, data: dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        if self.config_dir == CONFIG_DIR:
            return save_settings(data)
        return save_json_file(self.settings_file, data)

    def load_session(self) -> dict[str, Any]:
        data = load_json_file(self.session_file, {})
        return data if isinstance(data, dict) else {}

    def save_session(self, data: dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        return save_json_file(self.session_file, data)

    def load_recent_files(self, limit: int = 10) -> list[str]:
        if self.config_dir == CONFIG_DIR:
            return load_recent_files(limit)
        return _clean_existing_paths(load_json_file(self.recent_file, []), limit)

    def save_recent_files(self, items: list[str], limit: int = 10) -> bool:
        if self.config_dir == CONFIG_DIR:
            return save_recent_files(items, limit)
        return save_json_file(self.recent_file, _dedupe_paths(items)[:limit])

    def add_recent_file(self, path: str, limit: int = 10) -> list[str]:
        if self.config_dir == CONFIG_DIR:
            return add_recent_file(path, limit)
        if not path:
            return self.load_recent_files(limit)
        path = os.path.abspath(path)
        items = [x for x in self.load_recent_files(limit) if x != path]
        items.insert(0, path)
        self.save_recent_files(items, limit)
        return items[:limit]

    def load_favourite_store(self, limit: int = 50) -> list[str]:
        """Load canonical Favorite paths, including temporarily unavailable ones."""
        if self.config_dir == CONFIG_DIR:
            return load_favourite_store(limit)
        return _dedupe_paths(load_json_file(self.favourites_file, []))[:limit]

    def load_favourites(self, limit: int = 50) -> list[str]:
        if self.config_dir == CONFIG_DIR:
            return load_favourites(limit)
        return _clean_existing_paths(self.load_favourite_store(limit), limit)

    def save_favourites(self, items: list[str], limit: int = 50) -> bool:
        if self.config_dir == CONFIG_DIR:
            return save_favourites(items, limit)
        return save_json_file(self.favourites_file, _dedupe_paths(items)[:limit])

    def load_clips(self, limit: int = 200) -> list[dict[str, Any]]:
        return load_clips(self.config_dir, limit)

    def save_clips(self, clips: list[dict[str, Any]], limit: int = 200) -> bool:
        return save_clips(self.config_dir, clips, limit)

    @property
    def templates_dir(self) -> str:
        path = os.path.join(self.config_dir, "templates")
        os.makedirs(path, exist_ok=True)
        return path


def _dedupe_paths(items: Any) -> list[str]:
    clean: list[str] = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, str) and item and item not in clean:
            clean.append(item)
    return clean


def _clean_existing_paths(items: Any, limit: int) -> list[str]:
    clean: list[str] = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, str):
            path = os.path.abspath(item)
            if os.path.exists(path) and path not in clean:
                clean.append(path)
        if len(clean) >= limit:
            break
    return clean
