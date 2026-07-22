"""GTK-free References controller with persist-first mutations."""
from __future__ import annotations

from typing import Any, Callable, Protocol

from calamus_reference_store import ReferenceLibrarySnapshot, ReferenceSaveResult
from calamus_research_file import FileToken
from calamus_references import ReferenceRecord


class ReferenceStore(Protocol):
    def load(self) -> ReferenceLibrarySnapshot: ...
    def save(self, records, expected_token: FileToken, *, force: bool = False) -> ReferenceSaveResult: ...


class ReferenceView(Protocol):
    @property
    def widget(self) -> Any: ...
    def render(self, records: tuple[ReferenceRecord, ...], selected_key: str | None, status: str) -> None: ...
    def selected_key(self) -> str | None: ...
    def select_key(self, key: str | None) -> bool: ...


class ReferenceController:
    def __init__(
        self,
        store: ReferenceStore,
        view: ReferenceView,
        *,
        resolve_conflict: Callable[[], str],
        on_error: Callable[[str], None],
    ) -> None:
        if not hasattr(store, "load") or not hasattr(store, "save"):
            raise TypeError("store must implement ReferenceStore")
        if any(not hasattr(view, name) for name in ("widget", "render", "selected_key", "select_key")):
            raise TypeError("view must implement ReferenceView")
        if not callable(resolve_conflict) or not callable(on_error):
            raise TypeError("callbacks must be callable")
        self._store = store
        self._view = view
        self._resolve_conflict = resolve_conflict
        self._on_error = on_error
        self._records: tuple[ReferenceRecord, ...] = ()
        self._token = FileToken(False)
        self._diagnostics: tuple[Any, ...] = ()
        self._query = ""
        self._loaded = False

    @property
    def widget(self) -> Any:
        return self._view.widget

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def records(self) -> tuple[ReferenceRecord, ...]:
        return self._records

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(record.key for record in self._records)

    def load(self) -> None:
        snapshot = self._store.load()
        self._records = snapshot.records
        self._token = snapshot.token
        self._diagnostics = snapshot.diagnostics
        self._loaded = True
        self.refresh()
        if snapshot.diagnostics:
            detail = "\n".join(f"Line {item.line}: {item.message}" for item in snapshot.diagnostics[:8])
            self._on_error("References file contains blocking problems and is read-only until corrected.\n\n" + detail)

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def refresh(self, query: str | None = None) -> tuple[ReferenceRecord, ...]:
        if query is not None:
            self._query = query if isinstance(query, str) else ""
        visible = self.filtered_records(self._query)
        selected = self._view.selected_key()
        if selected not in {record.key for record in visible}:
            selected = visible[0].key if visible else None
        status = self._status_text(len(visible))
        self._view.render(visible, selected, status)
        return visible

    def filtered_records(self, query: str = "") -> tuple[ReferenceRecord, ...]:
        needle = (query or "").strip().casefold()
        if not needle:
            return self._records
        return tuple(record for record in self._records if needle in record.search_text)

    def selected_record(self) -> ReferenceRecord | None:
        key = self._view.selected_key()
        return next((record for record in self._records if record.key == key), None)

    def select_key(self, key: str) -> bool:
        self.ensure_loaded()
        if key not in self.keys:
            return False
        self._query = ""
        self.refresh()
        return self._view.select_key(key)

    def add(self, record: ReferenceRecord) -> bool:
        self.ensure_loaded()
        if self._diagnostics:
            return False
        if record.key in self.keys:
            self._on_error(f"Reference key already exists: {record.key}")
            return False
        return self._commit((*self._records, record), select_key=record.key)

    def update(self, original_key: str, record: ReferenceRecord) -> bool:
        self.ensure_loaded()
        if self._diagnostics:
            return False
        if original_key not in self.keys:
            self._on_error("Selected reference no longer exists.")
            return False
        if record.key != original_key and record.key in self.keys:
            self._on_error(f"Reference key already exists: {record.key}")
            return False
        candidate = tuple(record if item.key == original_key else item for item in self._records)
        return self._commit(candidate, select_key=record.key)

    def delete(self, key: str) -> bool:
        self.ensure_loaded()
        if self._diagnostics or key not in self.keys:
            return False
        candidate = tuple(item for item in self._records if item.key != key)
        next_key = candidate[0].key if candidate else None
        return self._commit(candidate, select_key=next_key)

    def reload(self) -> None:
        self.load()

    def _commit(self, candidate: tuple[ReferenceRecord, ...], *, select_key: str | None) -> bool:
        result = self._store.save(candidate, self._token)
        if result.status == "conflict":
            choice = self._resolve_conflict()
            if choice == "reload":
                self.load()
                return False
            if choice == "overwrite":
                result = self._store.save(candidate, result.token, force=True)
            else:
                return False
        if not result.saved:
            self._on_error(result.message or "Could not save References.")
            return False
        self._records = candidate
        self._token = result.token
        self._diagnostics = ()
        self.refresh()
        self._view.select_key(select_key)
        return True

    def _status_text(self, visible_count: int) -> str:
        total = len(self._records)
        if self._diagnostics:
            return f"{total} reference(s); file needs correction."
        if self._query.strip():
            return f"{visible_count} of {total} reference(s)."
        return f"{total} reference(s)."
