"""GTK-free Clip Collection application controller."""
from __future__ import annotations

from typing import Any, Protocol

from calamus_clip_search import duplicate_body_ids, search_clips
from calamus_clips import (
    ClipError,
    ClipSnapshot,
    clone_clip,
    clip_title_from_text,
    new_clip,
    update_clip,
    validate_clips,
)


class ClipStore(Protocol):
    def load_snapshot(self, limit: int = 200) -> ClipSnapshot: ...
    def save_snapshot(
        self,
        clips: list[dict[str, Any]],
        *,
        expected_revision: str,
        limit: int = 200,
    ) -> ClipSnapshot: ...
    def ensure_file(self, limit: int = 200) -> ClipSnapshot: ...


class ClipView(Protocol):
    @property
    def widget(self) -> Any: ...
    def render(self, clips: list[dict[str, Any]], *, total: int, query: str) -> None: ...
    def selected_id(self) -> str | None: ...
    def select_id(self, clip_id: str) -> bool: ...
    def focus_search(self) -> None: ...


class ClipCollectionController:
    """Own canonical state, search, selection and persist-first mutations."""

    def __init__(self, store: ClipStore, view: ClipView, *, limit: int = 200) -> None:
        advanced_store = all(hasattr(store, name) for name in ("load_snapshot", "save_snapshot", "ensure_file"))
        legacy_store = all(hasattr(store, name) for name in ("load_clips", "save_clips"))
        if not advanced_store and not legacy_store:
            raise TypeError("store must implement the ClipStore protocol")
        if not hasattr(view, "render") or not hasattr(view, "widget"):
            raise TypeError("view must implement the ClipView protocol")
        self._advanced_store = advanced_store
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        self._store = store
        self._view = view
        self._limit = limit
        self._clips: list[dict[str, Any]] = []
        self._visible: list[dict[str, Any]] = []
        self._revision = "missing"
        self._query = ""
        self.last_error = ""

    @property
    def widget(self) -> Any:
        return self._view.widget

    @property
    def clips(self) -> tuple[dict[str, Any], ...]:
        return tuple(_copy(item) for item in self._clips)

    @property
    def visible_clips(self) -> tuple[dict[str, Any], ...]:
        return tuple(_copy(item) for item in self._visible)

    @property
    def revision(self) -> str:
        return self._revision

    @property
    def query(self) -> str:
        return self._query

    @property
    def authority_path(self) -> str:
        return getattr(self._store, "path", "")

    def load(self) -> bool:
        return self.reload_from_disk(preserve_selection=False)

    def reload_from_disk(self, *, preserve_selection: bool = True) -> bool:
        selected = self.selected_id() if preserve_selection else None
        try:
            if self._advanced_store:
                snapshot = self._store.load_snapshot(self._limit)
                loaded = snapshot.mutable_clips()
                revision = snapshot.revision
            else:
                from calamus_clips import _coerce_input_records
                raw_items = self._store.load_clips(self._limit)
                loaded = []
                for raw in raw_items if isinstance(raw_items, list) else []:
                    try:
                        loaded.extend(_coerce_input_records([raw], limit=self._limit))
                    except ClipError:
                        continue
                revision = "legacy-runtime"
        except (ClipError, OSError, TypeError, ValueError) as error:
            self.last_error = str(error)
            return False
        self._clips = loaded
        self._revision = revision
        self.last_error = ""
        self._render(select_id=selected)
        return True

    def refresh(self) -> bool:
        """Refresh means a real disk reload, never a view-only redraw."""
        return self.reload_from_disk(preserve_selection=True)

    def activate(self) -> None:
        self._query = ""
        self._render(select_id=self.selected_id())
        if hasattr(self._view, "focus_search"):
            self._view.focus_search()

    def set_query(self, query: Any) -> None:
        selected = self.selected_id()
        self._query = query if isinstance(query, str) else ""
        self._render(select_id=selected)

    def selected_id(self) -> str | None:
        if hasattr(self._view, "selected_id"):
            clip_id = self._view.selected_id()
            return clip_id if isinstance(clip_id, str) and self.clip_by_id(clip_id) is not None else None
        if hasattr(self._view, "selected_index"):
            index = self._view.selected_index()
            if isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(self._visible):
                return self._visible[index].get("id")
        return None

    def selected_clip(self) -> dict[str, Any] | None:
        clip_id = self.selected_id()
        return self.clip_by_id(clip_id) if clip_id else None

    def selected_text(self) -> str | None:
        selected = self.selected_clip()
        return selected.get("text", "") if selected is not None else None

    def clip_by_id(self, clip_id: Any) -> dict[str, Any] | None:
        if not isinstance(clip_id, str):
            return None
        for item in self._clips:
            if item.get("id") == clip_id:
                return _copy(item)
        return None

    def select_id(self, clip_id: str, *, clear_query: bool = False) -> bool:
        if self.clip_by_id(clip_id) is None:
            return False
        if clear_query:
            self._query = ""
            self._render(select_id=clip_id)
            return True
        if not any(item.get("id") == clip_id for item in self._visible):
            self._query = ""
            self._render(select_id=clip_id)
            return True
        if hasattr(self._view, "select_id"):
            return bool(self._view.select_id(clip_id))
        if hasattr(self._view, "select_index"):
            for index, item in enumerate(self._visible):
                if item.get("id") == clip_id:
                    return bool(self._view.select_index(index))
        return False

    def select_number(self, number: Any) -> bool:
        try:
            index = int(number) - 1
        except (TypeError, ValueError):
            return False
        if index < 0 or index >= len(self._clips):
            return False
        return self.select_id(self._clips[index]["id"], clear_query=True)

    def create(self, title: str, text: str, shortcut: str = "") -> bool:
        try:
            item = new_clip(title, text, shortcut)
        except ClipError as error:
            self.last_error = str(error)
            return False
        return self._commit([item, *self._clips], select_id=item["id"])

    def add_text(self, text: Any) -> bool:
        value = text if isinstance(text, str) else ""
        return self.create(clip_title_from_text(value), value, "")

    def update_selected(self, title: str, text: str, shortcut: str = "") -> bool | None:
        selected = self.selected_clip()
        if selected is None:
            return None
        try:
            replacement = update_clip(selected, title=title, text=text, shortcut=shortcut)
        except ClipError as error:
            self.last_error = str(error)
            return False
        candidate = [replacement if item["id"] == selected["id"] else item for item in self._clips]
        return self._commit(candidate, select_id=selected["id"])

    def duplicate_selected(self, *, title: str | None = None) -> bool | None:
        selected = self.selected_clip()
        if selected is None:
            return None
        try:
            duplicate = clone_clip(selected, title=title)
        except ClipError as error:
            self.last_error = str(error)
            return False
        index = next(i for i, item in enumerate(self._clips) if item["id"] == selected["id"])
        candidate = list(self._clips)
        candidate.insert(index + 1, duplicate)
        return self._commit(candidate, select_id=duplicate["id"])

    def delete_selected(self) -> bool | None:
        selected = self.selected_clip()
        if selected is None:
            return None
        index = next(i for i, item in enumerate(self._clips) if item["id"] == selected["id"])
        candidate = [item for item in self._clips if item["id"] != selected["id"]]
        next_id = ""
        if candidate:
            next_id = candidate[min(index, len(candidate) - 1)]["id"]
        return self._commit(candidate, select_id=next_id or None)

    def duplicate_body_ids(self, text: str, *, exclude_id: str = "") -> tuple[str, ...]:
        return duplicate_body_ids(self._clips, text, exclude_id=exclude_id)

    def ensure_authority(self) -> bool:
        try:
            if self._advanced_store:
                snapshot = self._store.ensure_file(self._limit)
                self._clips = snapshot.mutable_clips()
                self._revision = snapshot.revision
            else:
                if not self._store.save_clips(self._clips, self._limit):
                    self.last_error = "Could not create Clip Collection authority."
                    return False
        except ClipError as error:
            self.last_error = str(error)
            return False
        self.last_error = ""
        self._render(select_id=self.selected_id())
        return True

    def _commit(self, candidate: list[dict[str, Any]], *, select_id: str | None) -> bool:
        try:
            clean = validate_clips(candidate, limit=self._limit)
            if self._advanced_store:
                snapshot = self._store.save_snapshot(
                    clean,
                    expected_revision=self._revision,
                    limit=self._limit,
                )
                committed = snapshot.mutable_clips()
                revision = snapshot.revision
            else:
                if not self._store.save_clips(clean, self._limit):
                    self.last_error = "Could not save Clip Collection."
                    return False
                committed = [_copy(item) for item in clean]
                revision = self._revision
        except ClipError as error:
            self.last_error = str(error)
            return False
        self._clips = committed
        self._revision = revision
        self.last_error = ""
        self._render(select_id=select_id)
        return True

    def _render(self, *, select_id: str | None = None) -> None:
        self._visible = search_clips(self._clips, self._query)
        try:
            self._view.render(self._visible, total=len(self._clips), query=self._query)
        except TypeError:
            self._view.render(self._visible)
        target = select_id
        if target and any(item.get("id") == target for item in self._visible):
            self.select_id(target)
        elif self._visible:
            self.select_id(self._visible[0]["id"])


def _copy(item: dict[str, Any]) -> dict[str, Any]:
    copied = dict(item)
    copied["extra_fields"] = tuple(item.get("extra_fields", ()))
    return copied
