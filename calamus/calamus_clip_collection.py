"""Typed Clip Collection controller independent from GTK and App."""
from __future__ import annotations

from typing import Any, Protocol

from calamus_clips import clip_title_from_text, new_clip


class ClipStore(Protocol):
    def load_clips(self, limit: int = 200) -> list[dict[str, Any]]: ...
    def save_clips(self, clips: list[dict[str, Any]], limit: int = 200) -> bool: ...


class ClipView(Protocol):
    @property
    def widget(self) -> Any: ...
    def render(self, clips: list[dict[str, Any]]) -> None: ...
    def selected_index(self) -> int | None: ...
    def select_index(self, index: int) -> bool: ...


class ClipCollectionController:
    """Own Clip Collection state, persistence and list-view synchronization."""

    def __init__(self, store: ClipStore, view: ClipView, *, limit: int = 200) -> None:
        if not hasattr(store, "load_clips") or not hasattr(store, "save_clips"):
            raise TypeError("store must implement the ClipStore protocol")
        required = ("render", "selected_index", "select_index", "widget")
        if any(not hasattr(view, name) for name in required):
            raise TypeError("view must implement the ClipView protocol")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        self._store = store
        self._view = view
        self._limit = limit
        self._clips: list[dict[str, Any]] = []

    @property
    def widget(self) -> Any:
        return self._view.widget

    @property
    def clips(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(item) for item in self._clips)

    def load(self) -> None:
        self._clips = self._clean(self._store.load_clips(self._limit))
        self.refresh()

    def refresh(self) -> None:
        self._view.render(self._clips)

    def selected_index(self) -> int | None:
        index = self._view.selected_index()
        if index is None or not isinstance(index, int):
            return None
        if index < 0 or index >= len(self._clips):
            return None
        return index

    def selected_text(self) -> str | None:
        index = self.selected_index()
        if index is None:
            return None
        return self._clips[index].get("text", "")

    def select_number(self, number: Any) -> bool:
        try:
            index = int(number) - 1
        except (TypeError, ValueError):
            return False
        if index < 0 or index >= len(self._clips):
            return False
        return bool(self._view.select_index(index))

    def add_text(self, text: Any) -> bool:
        value = text if isinstance(text, str) else ""
        candidate = [new_clip(clip_title_from_text(value), value), *self._clips]
        candidate = candidate[: self._limit]
        if not self._store.save_clips(candidate, self._limit):
            return False
        self._clips = candidate
        self.refresh()
        self._view.select_index(0)
        return True

    def delete_selected(self) -> bool | None:
        index = self.selected_index()
        if index is None:
            return None
        candidate = [item for position, item in enumerate(self._clips) if position != index]
        if not self._store.save_clips(candidate, self._limit):
            return False
        self._clips = candidate
        self.refresh()
        if self._clips:
            self._view.select_index(min(index, len(self._clips) - 1))
        return True

    @staticmethod
    def _clean(items: Any) -> list[dict[str, Any]]:
        clean: list[dict[str, Any]] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                continue
            title = item.get("title")
            if not isinstance(title, str) or not title.strip():
                title = clip_title_from_text(item["text"])
            created = item.get("created")
            clean.append(
                {
                    "title": title,
                    "text": item["text"],
                    "created": created if isinstance(created, str) else "",
                }
            )
        return clean
