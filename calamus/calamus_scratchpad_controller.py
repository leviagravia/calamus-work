"""GTK-free Scratchpad controller with document binding and persist-first CRUD."""
from __future__ import annotations

from typing import Any, Callable, Protocol

from calamus_document_structure import DocumentStructure
from calamus_research_file import FileToken
from calamus_scratchpad import ScratchpadEntry
from calamus_scratchpad_store import (
    MarkdownScratchpadStore,
    ScratchpadSaveResult,
    ScratchpadSnapshot,
    scratchpad_path,
)


class ScratchpadStore(Protocol):
    path: str
    def load(self) -> ScratchpadSnapshot: ...
    def save(self, entries, expected_token: FileToken, *, force: bool = False) -> ScratchpadSaveResult: ...


class ScratchpadView(Protocol):
    @property
    def widget(self) -> Any: ...
    def set_available(self, available: bool, message: str) -> None: ...
    def set_tag_options(self, tags: tuple[str, ...], selected: str) -> None: ...
    def render(
        self,
        entries: tuple[ScratchpadEntry, ...],
        selected_id: str | None,
        status: str,
        missing_section_ids: frozenset[str],
        ambiguous_section_ids: frozenset[str],
    ) -> None: ...
    def selected_id(self) -> str | None: ...
    def select_id(self, entry_id: str | None) -> bool: ...


class ScratchpadController:
    def __init__(
        self,
        view: ScratchpadView,
        *,
        document_structure_provider: Callable[[], DocumentStructure],
        resolve_conflict: Callable[[], str],
        on_error: Callable[[str], None],
        store_factory: Callable[[str], ScratchpadStore] = MarkdownScratchpadStore,
    ) -> None:
        required = ("widget", "set_available", "set_tag_options", "render", "selected_id", "select_id")
        if any(not hasattr(view, name) for name in required):
            raise TypeError("view must implement ScratchpadView")
        if not all(callable(callback) for callback in (
            document_structure_provider, resolve_conflict, on_error, store_factory,
        )):
            raise TypeError("Scratchpad callbacks must be callable")
        self._view = view
        self._document_structure_provider = document_structure_provider
        self._resolve_conflict = resolve_conflict
        self._on_error = on_error
        self._store_factory = store_factory
        self._store: ScratchpadStore | None = None
        self._document_path: str | None = None
        self._entries: tuple[ScratchpadEntry, ...] = ()
        self._token = FileToken(False)
        self._diagnostics: tuple[Any, ...] = ()
        self._query = ""
        self._type_filter = "all"
        self._status_filter = "active-work"
        self._tag_filter = "all"
        self._section_filter = "all"
        self._loaded = False
        self._view.set_available(False, "Save the document to use Scratchpad.")
        self._view.set_tag_options((), "all")
        self._view.render((), None, "No document sidecar.", frozenset(), frozenset())

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
    def entries(self) -> tuple[ScratchpadEntry, ...]:
        return self._entries

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(entry.id for entry in self._entries)

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

    @property
    def tags(self) -> tuple[str, ...]:
        values: list[str] = []
        identities: set[str] = set()
        for entry in self._entries:
            for tag in entry.tags:
                identity = tag.casefold()
                if identity not in identities:
                    values.append(tag)
                    identities.add(identity)
        return tuple(sorted(values, key=str.casefold))

    def bind_document(self, document_path: str | None, *, force: bool = False) -> bool:
        target = scratchpad_path(document_path)
        if target is None:
            self._document_path = None
            self._store = None
            self._entries = ()
            self._token = FileToken(False)
            self._diagnostics = ()
            self._loaded = False
            self._view.set_available(False, "Save the document to use Scratchpad.")
            self._view.set_tag_options((), "all")
            self._view.render((), None, "No document sidecar.", frozenset(), frozenset())
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
        self._entries = snapshot.entries
        self._token = snapshot.token
        self._diagnostics = snapshot.diagnostics
        self._loaded = True
        self._view.set_available(True, f"Sidecar: {self._store.path}")
        self.refresh()
        if snapshot.diagnostics:
            detail = "\n".join(f"Line {item.line}: {item.message}" for item in snapshot.diagnostics[:8])
            self._on_error(
                "Scratchpad contains blocking problems and is read-only until corrected.\n\n" + detail
            )

    def refresh(
        self,
        query: str | None = None,
        entry_type: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        section: str | None = None,
    ) -> tuple[ScratchpadEntry, ...]:
        if query is not None:
            self._query = query if isinstance(query, str) else ""
        if entry_type is not None:
            self._type_filter = entry_type if entry_type in {"all", "note", "idea", "draft", "task"} else "all"
        if status is not None:
            self._status_filter = status if status in {"all", "active-work", "inbox", "active", "resolved", "archived"} else "active-work"
        if tag is not None:
            self._tag_filter = tag or "all"
        if section is not None:
            self._section_filter = section or "all"
        tags = self.tags
        if self._tag_filter != "all" and not any(tag.casefold() == self._tag_filter.casefold() for tag in tags):
            self._tag_filter = "all"
        self._view.set_tag_options(tags, self._tag_filter)
        visible = self.filtered_entries(
            self._query,
            self._type_filter,
            self._status_filter,
            self._tag_filter,
            self._section_filter,
        )
        selected = self._view.selected_id()
        visible_ids = {entry.id for entry in visible}
        if selected not in visible_ids:
            selected = visible[0].id if visible else None
        missing, ambiguous = self._section_issue_ids()
        self._view.render(
            visible,
            selected,
            self._status_text(len(visible), len(missing), len(ambiguous)),
            missing,
            ambiguous,
        )
        return visible

    def filtered_entries(
        self,
        query: str = "",
        entry_type: str = "all",
        status: str = "active-work",
        tag: str = "all",
        section: str = "all",
    ) -> tuple[ScratchpadEntry, ...]:
        needle = (query or "").strip().casefold()
        result = self._entries
        if entry_type and entry_type != "all":
            result = tuple(entry for entry in result if entry.type == entry_type)
        if status == "active-work":
            result = tuple(entry for entry in result if entry.status != "archived")
        elif status and status != "all":
            result = tuple(entry for entry in result if entry.status == status)
        if tag and tag != "all":
            identity = tag.casefold()
            result = tuple(entry for entry in result if any(value.casefold() == identity for value in entry.tags))
        if section and section != "all":
            result = tuple(entry for entry in result if section in entry.sections)
        if needle:
            result = tuple(entry for entry in result if needle in entry.search_text)
        return result

    def selected_entry(self) -> ScratchpadEntry | None:
        entry_id = self._view.selected_id()
        return next((entry for entry in self._entries if entry.id == entry_id), None)

    def select_id(self, entry_id: str) -> bool:
        if not isinstance(entry_id, str) or entry_id not in self.ids:
            return False
        reset = getattr(self._view, "reset_filters", None)
        if callable(reset):
            reset()
        self._query = ""
        self._type_filter = "all"
        self._status_filter = "all"
        self._tag_filter = "all"
        self._section_filter = "all"
        self.refresh()
        return self._view.select_id(entry_id)

    def show_for_section(self, target: str | None) -> tuple[ScratchpadEntry, ...]:
        section = target or "__none__"
        set_section = getattr(self._view, "set_section_filter_label", None)
        if callable(set_section):
            set_section(target or "No current section")
        return self.refresh(section=section)

    def clear_section_filter(self) -> tuple[ScratchpadEntry, ...]:
        set_section = getattr(self._view, "set_section_filter_label", None)
        if callable(set_section):
            set_section("All sections")
        return self.refresh(section="all")

    def add(self, entry: ScratchpadEntry) -> bool:
        if not self._can_mutate() or not self._sections_are_valid(entry):
            return False
        if entry.id in self.ids:
            self._on_error(f"Scratchpad entry id already exists: {entry.id}")
            return False
        return self._commit((*self._entries, entry), select_id=entry.id)

    def update(self, original_id: str, entry: ScratchpadEntry) -> bool:
        if not self._can_mutate() or not self._sections_are_valid(entry):
            return False
        if original_id not in self.ids:
            self._on_error("Selected Scratchpad entry no longer exists.")
            return False
        if entry.id != original_id and entry.id in self.ids:
            self._on_error(f"Scratchpad entry id already exists: {entry.id}")
            return False
        candidate = tuple(entry if item.id == original_id else item for item in self._entries)
        return self._commit(candidate, select_id=entry.id)

    def archive(self, entry_id: str, *, archived: bool = True) -> bool:
        selected = next((entry for entry in self._entries if entry.id == entry_id), None)
        if selected is None or not self._can_mutate():
            return False
        status = "archived" if archived else "active"
        revised = selected.revised(updated=selected.updated, status=status)
        candidate = tuple(revised if item.id == entry_id else item for item in self._entries)
        return self._commit(candidate, select_id=entry_id)

    def delete(self, entry_id: str) -> bool:
        if not self._can_mutate() or entry_id not in self.ids:
            return False
        index = self.ids.index(entry_id)
        candidate = tuple(entry for entry in self._entries if entry.id != entry_id)
        next_id = candidate[min(index, len(candidate) - 1)].id if candidate else None
        return self._commit(candidate, select_id=next_id)

    def reload(self) -> None:
        if self._store is not None:
            self.load()

    def target_state(self, target: str) -> str:
        if not target:
            return "none"
        matches = self.document_structure.headings_for_identifier(target)
        if not matches:
            return "missing"
        if len(matches) > 1:
            return "ambiguous"
        return "valid"

    def entry_target_state(self, entry: ScratchpadEntry) -> str:
        states = {self.target_state(target) for target in entry.sections}
        if "ambiguous" in states:
            return "ambiguous"
        if "missing" in states:
            return "missing"
        return "valid" if entry.sections else "none"

    def _section_issue_ids(self) -> tuple[frozenset[str], frozenset[str]]:
        missing: set[str] = set()
        ambiguous: set[str] = set()
        for entry in self._entries:
            state = self.entry_target_state(entry)
            if state == "missing":
                missing.add(entry.id)
            elif state == "ambiguous":
                ambiguous.add(entry.id)
        return frozenset(missing), frozenset(ambiguous)

    def _sections_are_valid(self, entry: ScratchpadEntry) -> bool:
        for target in entry.sections:
            state = self.target_state(target)
            if state == "missing":
                self._on_error(f"Heading target is missing: {target}")
                return False
            if state == "ambiguous":
                self._on_error(f"Heading target is ambiguous: {target}")
                return False
        return True

    def _can_mutate(self) -> bool:
        if self._store is None:
            self._on_error("Save the document before using Scratchpad.")
            return False
        if self._diagnostics:
            return False
        return True

    def _commit(self, candidate: tuple[ScratchpadEntry, ...], *, select_id: str | None) -> bool:
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
            self._on_error(result.message or "Could not save Scratchpad.")
            return False
        self._entries = candidate
        self._token = result.token
        self._diagnostics = ()
        self.refresh()
        self._view.select_id(select_id)
        return True

    def _status_text(self, visible_count: int, missing_count: int, ambiguous_count: int) -> str:
        total = len(self._entries)
        if self._diagnostics:
            return f"{total} item(s); sidecar needs correction."
        issues: list[str] = []
        if missing_count:
            issues.append(f"{missing_count} missing section link(s)")
        if ambiguous_count:
            issues.append(f"{ambiguous_count} ambiguous section link(s)")
        base = f"{total} item(s)"
        if issues:
            base += "; " + "; ".join(issues)
        base += "."
        filtered = any((
            self._query.strip(), self._type_filter != "all", self._status_filter not in {"all", "active-work"},
            self._tag_filter != "all", self._section_filter != "all",
        ))
        return f"{visible_count} of {base}" if filtered else base
