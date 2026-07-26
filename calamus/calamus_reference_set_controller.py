"""GTK-free controller for transparent static Calamus Reference Sets."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Protocol

from calamus_reference_set_store import (
    ReferenceSetSaveResult,
    ReferenceSetSnapshot,
)
from calamus_reference_sets import ReferenceSet, canonicalize_reference_set
from calamus_references import ReferenceRecord
from calamus_research_file import FileToken


class ReferenceSetStore(Protocol):
    def load(self) -> ReferenceSetSnapshot: ...
    def save(self, sets, expected_token: FileToken, *, force: bool = False) -> ReferenceSetSaveResult: ...


class ReferenceSetView(Protocol):
    @property
    def widget(self) -> Any: ...
    def render(
        self,
        sets: tuple[ReferenceSet, ...],
        selected_set: str | None,
        records: tuple[ReferenceRecord, ...],
        selected_member: str | None,
        status: str,
    ) -> None: ...
    def selected_set_name(self) -> str | None: ...
    def selected_member_key(self) -> str | None: ...
    def select_set_name(self, name: str | None) -> bool: ...
    def select_member_key(self, key: str | None) -> bool: ...


class ReferenceSetController:
    def __init__(
        self,
        store: ReferenceSetStore,
        view: ReferenceSetView,
        *,
        records_provider: Callable[[], Iterable[ReferenceRecord]],
        resolve_conflict: Callable[[], str],
        on_error: Callable[[str], None],
    ) -> None:
        if not hasattr(store, "load") or not hasattr(store, "save"):
            raise TypeError("store must implement ReferenceSetStore")
        required = (
            "widget", "render", "selected_set_name", "selected_member_key",
            "select_set_name", "select_member_key",
        )
        if any(not hasattr(view, name) for name in required):
            raise TypeError("view must implement ReferenceSetView")
        if any(not callable(callback) for callback in (records_provider, resolve_conflict, on_error)):
            raise TypeError("Reference Set callbacks must be callable")
        self._store = store
        self._view = view
        self._records_provider = records_provider
        self._resolve_conflict = resolve_conflict
        self._on_error = on_error
        self._sets: tuple[ReferenceSet, ...] = ()
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
    def sets(self) -> tuple[ReferenceSet, ...]:
        return self._sets

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self._sets)

    @property
    def records(self) -> tuple[ReferenceRecord, ...]:
        records = tuple(self._records_provider())
        if any(not isinstance(record, ReferenceRecord) for record in records):
            raise TypeError("records_provider must return ReferenceRecord values")
        return records

    def load(self) -> None:
        snapshot = self._store.load()
        self._sets = snapshot.sets
        self._token = snapshot.token
        self._diagnostics = snapshot.diagnostics
        self._loaded = True
        self.refresh()
        blocking = [item for item in snapshot.diagnostics if item.blocking]
        if blocking:
            detail = "\n".join(f"Line {item.line}: {item.message}" for item in blocking[:8])
            self._on_error("Reference Sets contains blocking problems and is read-only until corrected.\n\n" + detail)

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def selected_set(self) -> ReferenceSet | None:
        name = self._view.selected_set_name()
        return next((item for item in self._sets if item.name == name), None)

    def selected_member_key(self) -> str | None:
        return self._view.selected_member_key()

    def filtered_sets(self, query: str = "") -> tuple[ReferenceSet, ...]:
        needle = (query or "").strip().casefold()
        if not needle:
            return self._sets
        return tuple(item for item in self._sets if needle in item.search_text)

    def refresh(self, query: str | None = None) -> tuple[ReferenceSet, ...]:
        if query is not None:
            self._query = query if isinstance(query, str) else ""
        visible = self.filtered_sets(self._query)
        selected = self._view.selected_set_name()
        if selected not in {item.name for item in visible}:
            selected = visible[0].name if visible else None
        selected_item = next((item for item in visible if item.name == selected), None)
        member = self._view.selected_member_key()
        if selected_item is None or member not in selected_item.members:
            member = selected_item.members[0] if selected_item and selected_item.members else None
        status = self._status_text(len(visible), selected_item)
        self._view.render(visible, selected, self.records, member, status)
        return visible

    def select_set(self, name: str) -> bool:
        self.ensure_loaded()
        match = next((item.name for item in self._sets if item.name.casefold() == (name or "").casefold()), None)
        if match is None:
            return False
        self._query = ""
        self.refresh()
        return self._view.select_set_name(match)

    def add(self, item: ReferenceSet) -> bool:
        self.ensure_loaded()
        if self._blocking():
            return False
        candidate = canonicalize_reference_set(item, self.records)
        if candidate.identity in {current.identity for current in self._sets}:
            self._on_error(f"Reference Set name already exists: {candidate.name}")
            return False
        return self._commit((*self._sets, candidate), select_set=candidate.name)

    def update(self, original_name: str, item: ReferenceSet) -> bool:
        self.ensure_loaded()
        if self._blocking():
            return False
        original = next((current for current in self._sets if current.name == original_name), None)
        if original is None:
            self._on_error("Selected Reference Set no longer exists.")
            return False
        candidate_item = canonicalize_reference_set(item, self.records)
        collisions = {
            current.identity for current in self._sets if current.name != original_name
        }
        if candidate_item.identity in collisions:
            self._on_error(f"Reference Set name already exists: {candidate_item.name}")
            return False
        candidate = tuple(
            candidate_item if current.name == original_name else current
            for current in self._sets
        )
        return self._commit(candidate, select_set=candidate_item.name)

    def delete(self, name: str) -> bool:
        self.ensure_loaded()
        if self._blocking() or name not in self.names:
            return False
        candidate = tuple(item for item in self._sets if item.name != name)
        next_name = candidate[0].name if candidate else None
        return self._commit(candidate, select_set=next_name)

    def reload(self) -> None:
        self.load()

    def replace_sets(self, candidate: Iterable[ReferenceSet], *, select_set: str | None = None) -> bool:
        self.ensure_loaded()
        if self._blocking():
            return False
        snapshot = tuple(candidate)
        if any(not isinstance(item, ReferenceSet) for item in snapshot):
            raise TypeError("candidate must contain ReferenceSet values")
        return self._commit(snapshot, select_set=select_set)

    def _blocking(self) -> bool:
        return any(getattr(item, "blocking", True) for item in self._diagnostics)

    def _commit(self, candidate: tuple[ReferenceSet, ...], *, select_set: str | None) -> bool:
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
            self._on_error(result.message or "Could not save Reference Sets.")
            return False
        self._sets = candidate
        self._token = result.token
        self._diagnostics = ()
        self.refresh()
        self._view.select_set_name(select_set)
        return True

    def _status_text(self, visible_count: int, selected: ReferenceSet | None) -> str:
        total = len(self._sets)
        if self._blocking():
            return f"{total} set(s); file needs correction."
        base = f"{visible_count} of {total} set(s)." if self._query.strip() else f"{total} set(s)."
        if selected is not None:
            base += f" {len(selected.members)} member(s)."
        return base
