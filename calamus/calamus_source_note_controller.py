"""GTK-free Source Notes controller with document binding and persist-first CRUD."""
from __future__ import annotations

from typing import Any, Callable, Protocol

from calamus_document_structure import DocumentStructure
from calamus_research_file import FileToken
from calamus_source_note_store import (
    MarkdownSourceNoteStore,
    SourceNoteSaveResult,
    SourceNoteSnapshot,
    source_notes_path,
)
from calamus_source_notes import SourceNote


class SourceNoteStore(Protocol):
    path: str
    def load(self) -> SourceNoteSnapshot: ...
    def save(self, notes, expected_token: FileToken, *, force: bool = False) -> SourceNoteSaveResult: ...


class SourceNoteView(Protocol):
    @property
    def widget(self) -> Any: ...
    def set_available(self, available: bool, message: str) -> None: ...
    def set_reference_options(self, keys: tuple[str, ...], selected: str) -> None: ...
    def render(
        self,
        notes: tuple[SourceNote, ...],
        selected_id: str | None,
        status: str,
        missing_reference_ids: frozenset[str],
        missing_target_ids: frozenset[str],
        ambiguous_target_ids: frozenset[str],
    ) -> None: ...
    def selected_id(self) -> str | None: ...
    def select_id(self, note_id: str | None) -> bool: ...


class SourceNoteController:
    def __init__(
        self,
        view: SourceNoteView,
        *,
        reference_keys_provider: Callable[[], tuple[str, ...]],
        document_structure_provider: Callable[[], DocumentStructure],
        reference_key_resolver: Callable[[str], str | None] | None = None,
        resolve_conflict: Callable[[], str],
        on_error: Callable[[str], None],
        store_factory: Callable[[str], SourceNoteStore] = MarkdownSourceNoteStore,
    ) -> None:
        if any(not hasattr(view, name) for name in (
            "widget", "set_available", "set_reference_options", "render",
            "selected_id", "select_id",
        )):
            raise TypeError("view must implement SourceNoteView")
        if not all(callable(callback) for callback in (
            reference_keys_provider, document_structure_provider,
            resolve_conflict, on_error, store_factory,
        )):
            raise TypeError("callbacks must be callable")
        self._view = view
        self._reference_keys_provider = reference_keys_provider
        if reference_key_resolver is not None and not callable(reference_key_resolver):
            raise TypeError("reference_key_resolver must be callable")
        self._document_structure_provider = document_structure_provider
        self._reference_key_resolver = reference_key_resolver
        self._resolve_conflict = resolve_conflict
        self._on_error = on_error
        self._store_factory = store_factory
        self._store: SourceNoteStore | None = None
        self._document_path: str | None = None
        self._notes: tuple[SourceNote, ...] = ()
        self._token = FileToken(False)
        self._diagnostics: tuple[Any, ...] = ()
        self._query = ""
        self._kind_filter = "all"
        self._reference_filter = "all"
        self._loaded = False
        self._view.set_available(False, "Save the document to use Source Notes.")
        self._view.set_reference_options((), "all")
        self._view.render(
            (), None, "No document sidecar.",
            frozenset(), frozenset(), frozenset(),
        )

    @property
    def widget(self) -> Any:
        return self._view.widget

    @property
    def document_path(self) -> str | None:
        return self._document_path

    @property
    def sidecar_path(self) -> str | None:
        return self._store.path if self._store is not None else None

    @property
    def available(self) -> bool:
        return self._store is not None

    @property
    def notes(self) -> tuple[SourceNote, ...]:
        return self._notes

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(note.id for note in self._notes)

    @property
    def reference_keys(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(self._reference_keys_provider()))

    def resolve_reference_key(self, key: str) -> str | None:
        if self._reference_key_resolver is not None:
            return self._reference_key_resolver(key)
        return key if key in self.reference_keys else None

    @property
    def document_structure(self) -> DocumentStructure:
        structure = self._document_structure_provider()
        if not isinstance(structure, DocumentStructure):
            raise TypeError("document_structure_provider must return DocumentStructure")
        return structure

    @property
    def target_options(self) -> tuple[tuple[str, str], ...]:
        structure = self.document_structure
        options: list[tuple[str, str]] = []
        for heading in structure.headings:
            if heading.identifier is None:
                continue
            matches = structure.headings_for_identifier(heading.identifier)
            if len(matches) == 1:
                target = f"#{heading.identifier}"
                options.append((target, f"{heading.display_title} — {target}"))
        return tuple(options)

    def bind_document(self, document_path: str | None, *, force: bool = False) -> bool:
        target = source_notes_path(document_path)
        if target is None:
            self._document_path = None
            self._store = None
            self._notes = ()
            self._token = FileToken(False)
            self._diagnostics = ()
            self._loaded = False
            self._view.set_available(False, "Save the document to use Source Notes.")
            self._view.set_reference_options(self.reference_keys, "all")
            self._view.render(
                (), None, "No document sidecar.",
                frozenset(), frozenset(), frozenset(),
            )
            return False
        if not force and self._store is not None and self._store.path == target and self._loaded:
            self.refresh()
            return True
        self._document_path = document_path
        self._store = self._store_factory(target)
        self._loaded = False
        self.load()
        return True

    def load(self) -> None:
        if self._store is None:
            return
        snapshot = self._store.load()
        self._notes = snapshot.notes
        self._token = snapshot.token
        self._diagnostics = snapshot.diagnostics
        self._loaded = True
        self._view.set_available(True, f"Sidecar: {self._store.path}")
        self.refresh()
        if snapshot.diagnostics:
            detail = "\n".join(
                f"Line {item.line}: {item.message}"
                for item in snapshot.diagnostics[:8]
            )
            self._on_error(
                "Source Notes file contains blocking problems and is read-only "
                "until corrected.\n\n" + detail
            )

    def refresh(
        self,
        query: str | None = None,
        kind: str | None = None,
        reference_key: str | None = None,
    ) -> tuple[SourceNote, ...]:
        if query is not None:
            self._query = query if isinstance(query, str) else ""
        if kind is not None:
            self._kind_filter = kind if kind in {"all", "quote", "paraphrase", "comment"} else "all"
        if reference_key is not None:
            self._reference_filter = reference_key or "all"
        keys = self.reference_keys
        if self._reference_filter != "all" and self._reference_filter not in keys:
            self._reference_filter = "all"
        self._view.set_reference_options(keys, self._reference_filter)
        visible = self.filtered_notes(
            self._query,
            self._kind_filter,
            self._reference_filter,
        )
        selected = self._view.selected_id()
        visible_ids = {note.id for note in visible}
        if selected not in visible_ids:
            selected = visible[0].id if visible else None
        missing_references = frozenset(
            note.id
            for note in self._notes
            if note.reference_key and self.resolve_reference_key(note.reference_key) is None
        )
        missing_targets, ambiguous_targets = self._target_issue_ids()
        self._view.render(
            visible,
            selected,
            self._status_text(
                len(visible),
                len(missing_references),
                len(missing_targets),
                len(ambiguous_targets),
            ),
            missing_references,
            missing_targets,
            ambiguous_targets,
        )
        return visible

    def filtered_notes(
        self,
        query: str = "",
        kind: str = "all",
        reference_key: str = "all",
    ) -> tuple[SourceNote, ...]:
        needle = (query or "").strip().casefold()
        result = self._notes
        if kind and kind != "all":
            result = tuple(note for note in result if note.kind == kind)
        if reference_key and reference_key != "all":
            result = tuple(note for note in result if note.reference_key == reference_key)
        if needle:
            result = tuple(note for note in result if needle in note.search_text)
        return result

    def selected_note(self) -> SourceNote | None:
        note_id = self._view.selected_id()
        return next((note for note in self._notes if note.id == note_id), None)

    def add(self, note: SourceNote) -> bool:
        if not self._can_mutate() or not self._links_are_valid(note):
            return False
        if note.id in self.ids:
            self._on_error(f"Source Note id already exists: {note.id}")
            return False
        return self._commit((*self._notes, note), select_id=note.id)

    def update(self, original_id: str, note: SourceNote) -> bool:
        if not self._can_mutate() or not self._links_are_valid(note):
            return False
        if original_id not in self.ids:
            self._on_error("Selected Source Note no longer exists.")
            return False
        if note.id != original_id and note.id in self.ids:
            self._on_error(f"Source Note id already exists: {note.id}")
            return False
        candidate = tuple(note if item.id == original_id else item for item in self._notes)
        return self._commit(candidate, select_id=note.id)

    def delete(self, note_id: str) -> bool:
        if not self._can_mutate() or note_id not in self.ids:
            return False
        index = self.ids.index(note_id)
        candidate = tuple(note for note in self._notes if note.id != note_id)
        next_id = None
        if candidate:
            next_id = candidate[min(index, len(candidate) - 1)].id
        return self._commit(candidate, select_id=next_id)

    def reload(self) -> None:
        if self._store is not None:
            self.load()

    def target_state(self, note: SourceNote) -> str:
        if not note.target:
            return "none"
        matches = self.document_structure.headings_for_identifier(note.target)
        if not matches:
            return "missing"
        if len(matches) > 1:
            return "ambiguous"
        return "valid"

    def _target_issue_ids(self) -> tuple[frozenset[str], frozenset[str]]:
        missing: set[str] = set()
        ambiguous: set[str] = set()
        for note in self._notes:
            state = self.target_state(note)
            if state == "missing":
                missing.add(note.id)
            elif state == "ambiguous":
                ambiguous.add(note.id)
        return frozenset(missing), frozenset(ambiguous)

    def _links_are_valid(self, note: SourceNote) -> bool:
        if note.reference_key and self.resolve_reference_key(note.reference_key) is None:
            self._on_error(f"Reference key is missing: {note.reference_key}")
            return False
        target_state = self.target_state(note)
        if target_state == "missing":
            self._on_error(f"Heading target is missing: {note.target}")
            return False
        if target_state == "ambiguous":
            self._on_error(f"Heading target is ambiguous: {note.target}")
            return False
        return True

    def _can_mutate(self) -> bool:
        if self._store is None:
            self._on_error("Save the document before creating Source Notes.")
            return False
        if self._diagnostics:
            return False
        return True

    def _commit(self, candidate: tuple[SourceNote, ...], *, select_id: str | None) -> bool:
        assert self._store is not None
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
            self._on_error(result.message or "Could not save Source Notes.")
            return False
        self._notes = candidate
        self._token = result.token
        self._diagnostics = ()
        self.refresh()
        self._view.select_id(select_id)
        return True

    def _status_text(
        self,
        visible_count: int,
        missing_reference_count: int,
        missing_target_count: int,
        ambiguous_target_count: int,
    ) -> str:
        total = len(self._notes)
        if self._diagnostics:
            return f"{total} note(s); sidecar needs correction."
        issues: list[str] = []
        if missing_reference_count:
            issues.append(f"{missing_reference_count} missing reference link(s)")
        if missing_target_count:
            issues.append(f"{missing_target_count} missing target(s)")
        if ambiguous_target_count:
            issues.append(f"{ambiguous_target_count} ambiguous target(s)")
        base = f"{total} note(s)"
        if issues:
            base += "; " + "; ".join(issues)
        base += "."
        if self._query.strip() or self._kind_filter != "all" or self._reference_filter != "all":
            return f"{visible_count} of {base}"
        return base
