"""Compatibility facade over the W106 narrow persistence owners.

The running application no longer receives this object as a persistence
service.  Historical tests/callers may still use ``StateManager`` while it
forwards settings and path collections to the W106 repositories.  Clip and
template compatibility remain explicitly non-authoritative and are kept only
until their already-owning subsystems finish the later host-port migration.
"""
from __future__ import annotations

import os
from typing import Any

from calamus_clips import load_clips, save_clips
from calamus_config import CONFIG_DIR
from calamus_persistent_collections import FavouriteStore, RecentFileStore, RecentWorkspaceStore
from calamus_settings_repository import SettingsCodec, SettingsRepository


class StateManager:
    """Deprecated compatibility facade; not an application composition authority."""

    def __init__(self, config_dir: str = CONFIG_DIR):
        self.config_dir = config_dir
        self.settings_file = os.path.join(config_dir, "settings.json")
        self.recent_file = os.path.join(config_dir, "recent.json")
        self.favourites_file = os.path.join(config_dir, "favourites.json")
        self.recent_workspaces_file = os.path.join(config_dir, "recent-workspaces.json")
        self._settings = SettingsRepository(config_dir)
        self._recent = RecentFileStore(config_dir)
        self._favourites = FavouriteStore(config_dir)
        self._recent_workspaces = RecentWorkspaceStore(config_dir)

    def ensure_dir(self) -> None:
        os.makedirs(self.config_dir, exist_ok=True)

    def load_settings(self) -> dict[str, Any]:
        return SettingsCodec.encode(self._settings.reload())

    def save_settings(self, data: dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        return self._settings.replace(SettingsCodec.decode(data))

    def load_recent_file_store(self, limit: int = 10) -> list[str]:
        return self._recent.canonical()[:limit]

    def load_recent_files(self, limit: int = 10) -> list[str]:
        return self._recent.visible()[:limit]

    def save_recent_files(self, items: list[str], limit: int = 10) -> bool:
        return RecentFileStore(self.config_dir, limit).save(items)

    def add_recent_file(self, path: str, limit: int = 10) -> list[str]:
        # W106 integrity rule: build from canonical, never the filtered menu list.
        return RecentFileStore(self.config_dir, limit).add(path)

    def load_favourite_store(self, limit: int = 50) -> list[str]:
        return self._favourites.canonical()[:limit]

    def load_favourites(self, limit: int = 50) -> list[str]:
        return self._favourites.visible()[:limit]

    def save_favourites(self, items: list[str], limit: int = 50) -> bool:
        return FavouriteStore(self.config_dir, limit).save(items)

    def load_recent_workspaces(self, limit: int = 10) -> list[str]:
        return RecentWorkspaceStore(self.config_dir, limit).visible()

    def save_recent_workspaces(self, items: list[str], limit: int = 10) -> bool:
        return RecentWorkspaceStore(self.config_dir, limit).save(items)

    def add_recent_workspace(self, path: str, limit: int = 10) -> list[str]:
        return RecentWorkspaceStore(self.config_dir, limit).add(path)

    # Explicit compatibility only: Clip Collection has its own Markdown store.
    def load_clips(self, limit: int = 200) -> list[dict[str, Any]]:
        return load_clips(self.config_dir, limit)

    def save_clips(self, clips: list[dict[str, Any]], limit: int = 200) -> bool:
        return save_clips(self.config_dir, clips, limit)

    @property
    def templates_dir(self) -> str:
        path = os.path.join(self.config_dir, "templates")
        os.makedirs(path, exist_ok=True)
        return path
