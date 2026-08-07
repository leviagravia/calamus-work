"""Narrow canonical path-list stores for Calamus W106."""
from __future__ import annotations

import os
from typing import Any, Callable

from calamus_config import load_json_file, save_json_file


def _dedupe(items: Any, limit: int) -> list[str]:
    result: list[str] = []
    for item in items if isinstance(items, list) else []:
        if isinstance(item, str) and item:
            path = os.path.abspath(item)
            if path not in result:
                result.append(path)
        if len(result) >= limit:
            break
    return result


class CanonicalPathStore:
    def __init__(self, path: str, *, limit: int, available: Callable[[str], bool]) -> None:
        self.path = path
        self.limit = limit
        self._available = available

    def canonical(self) -> list[str]:
        return _dedupe(load_json_file(self.path, []), self.limit)

    def visible(self) -> list[str]:
        return [p for p in self.canonical() if self._available(p)][: self.limit]

    def save(self, items: list[str]) -> bool:
        return save_json_file(self.path, _dedupe(items, self.limit))

    def add(self, path: str) -> list[str]:
        if not isinstance(path, str) or not path:
            return self.visible()
        absolute = os.path.abspath(path)
        items = [p for p in self.canonical() if p != absolute]
        items.insert(0, absolute)
        if not self.save(items):
            return self.visible()
        return [p for p in items if self._available(p)][: self.limit]


class RecentFileStore(CanonicalPathStore):
    def __init__(self, config_dir: str, limit: int = 10) -> None:
        super().__init__(os.path.join(config_dir, "recent.json"), limit=limit, available=os.path.exists)


class FavouriteStore(CanonicalPathStore):
    def __init__(self, config_dir: str, limit: int = 50) -> None:
        super().__init__(os.path.join(config_dir, "favourites.json"), limit=limit, available=os.path.exists)


class RecentWorkspaceStore(CanonicalPathStore):
    def __init__(self, config_dir: str, limit: int = 10) -> None:
        super().__init__(os.path.join(config_dir, "recent-workspaces.json"), limit=limit, available=os.path.isdir)
