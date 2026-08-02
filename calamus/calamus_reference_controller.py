"""GTK-free References controller with persist-first mutations."""
from __future__ import annotations

from typing import Any, Callable, Protocol

from calamus_reference_store import ReferenceLibrarySnapshot, ReferenceSaveResult
from calamus_research_file import FileToken
from calamus_references import ReferenceRecord
from calamus_bibliography import BibliographyContext, BibliographyFilters, project_references


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
        self._filters = BibliographyFilters()
        self._context = BibliographyContext()
        self._selected_key: str | None = None
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

    @property
    def identity_keys(self) -> tuple[str, ...]:
        return tuple(identity for record in self._records for identity in record.identity_keys)

    def resolve_key(self, key: str) -> str | None:
        matches = [record.key for record in self._records if key in record.identity_keys]
        return matches[0] if len(matches) == 1 else None

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

    @property
    def filters(self) -> BibliographyFilters:
        return self._filters

    @property
    def context(self) -> BibliographyContext:
        return self._context

    @property
    def selected_key(self) -> str | None:
        return self._selected_key

    def set_context(self, context: BibliographyContext) -> None:
        if not isinstance(context, BibliographyContext):
            raise TypeError("context must be BibliographyContext")
        self._context = context
        if self._loaded:
            self.refresh()

    def set_filters(self, **changes: str) -> tuple[ReferenceRecord, ...]:
        values = {
            "query": self._filters.query,
            "reference_type": self._filters.reference_type,
            "tag": self._filters.tag,
            "use": self._filters.use,
            "file": self._filters.file,
            "integrity": self._filters.integrity,
            "sort": self._filters.sort,
        }
        for name, value in changes.items():
            if name not in values:
                raise ValueError(f"unknown bibliography filter: {name}")
            values[name] = value if isinstance(value, str) else ""
        self._filters = BibliographyFilters(**values)
        return self.refresh()

    def refresh(self, query: str | None = None) -> tuple[ReferenceRecord, ...]:
        if query is not None:
            values = {
                "query": query if isinstance(query, str) else "",
                "reference_type": self._filters.reference_type,
                "tag": self._filters.tag,
                "use": self._filters.use,
                "file": self._filters.file,
                "integrity": self._filters.integrity,
                "sort": self._filters.sort,
            }
            self._filters = BibliographyFilters(**values)
        visible = self.filtered_records()
        visible_keys = {record.key for record in visible}
        if self._selected_key not in visible_keys:
            self._selected_key = visible[0].key if visible else None
        status = self._status_text(len(visible))
        self._view.render(visible, self._selected_key, status)
        self.refresh_detail()
        return visible

    def filtered_records(self, query: str | None = None) -> tuple[ReferenceRecord, ...]:
        filters = self._filters
        if query is not None:
            filters = BibliographyFilters(
                query=query if isinstance(query, str) else "",
                reference_type=filters.reference_type,
                tag=filters.tag,
                use=filters.use,
                file=filters.file,
                integrity=filters.integrity,
                sort=filters.sort,
            )
        return project_references(self._records, filters, self._context)

    def refresh_detail(self) -> None:
        if hasattr(self._view, "render_detail"):
            self._view.render_detail(self.selected_record(), self._context)

    def selected_record(self) -> ReferenceRecord | None:
        return next((record for record in self._records if record.key == self._selected_key), None)

    def sync_selection_from_view(self) -> None:
        selected = self._view.selected_key()
        self._selected_key = selected if selected in self.keys else None
        self.refresh_detail()

    def select_key(self, key: str) -> bool:
        self.ensure_loaded()
        canonical = self.resolve_key(key)
        if canonical is None:
            return False
        self._filters = BibliographyFilters()
        self._selected_key = canonical
        self.refresh()
        return self._view.select_key(canonical)

    def add(self, record: ReferenceRecord) -> bool:
        self.ensure_loaded()
        if self._diagnostics:
            return False
        collisions = set(record.identity_keys).intersection(self.identity_keys)
        if collisions:
            self._on_error(f"Reference identity already exists: {sorted(collisions)[0]}")
            return False
        return self._commit((*self._records, record), select_key=record.key)

    def update(self, original_key: str, record: ReferenceRecord) -> bool:
        self.ensure_loaded()
        if self._diagnostics:
            return False
        if original_key not in self.keys:
            self._on_error("Selected reference no longer exists.")
            return False
        original = next(item for item in self._records if item.key == original_key)
        if record.key != original_key:
            self._on_error("Use Rename Reference Key for citation-key changes.")
            return False
        if record.aliases != original.aliases:
            self._on_error("Reference aliases are managed only by controlled key migration.")
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

    def replace_records(
        self,
        candidate: tuple[ReferenceRecord, ...],
        *,
        select_key: str | None = None,
    ) -> bool:
        """Persist one externally planned complete library snapshot.

        The caller must provide a GTK-free immutable plan.  This gateway keeps
        conflict handling and persist-first ownership inside References.
        """
        self.ensure_loaded()
        if self._diagnostics:
            return False
        if any(not isinstance(record, ReferenceRecord) for record in candidate):
            raise TypeError("candidate must contain ReferenceRecord values")
        return self._commit(tuple(candidate), select_key=select_key)

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
        self._selected_key = select_key
        self.refresh()
        return True

    def _status_text(self, visible_count: int) -> str:
        total = len(self._records)
        if self._diagnostics:
            return f"{total} reference(s); file needs correction."
        if self._filters.query.strip() or any((self._filters.reference_type != "all", self._filters.tag != "all", self._filters.use != "all", self._filters.file != "all", self._filters.integrity != "all")):
            return f"{visible_count} of {total} reference(s)."
        return f"{total} reference(s)."
