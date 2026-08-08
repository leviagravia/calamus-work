"""GTK-free App boundary for building W96 Document Dossier inputs.

The App supplies only live editor state and existing authority stores.  This
module performs bounded, read-only loading and returns the immutable input
value consumed by :mod:`calamus_document_dossier`.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from calamus_document_dossier import DocumentDossierInputs
from calamus_reference_set_store import ReferenceSetSnapshot
from calamus_reference_store import ReferenceLibrarySnapshot
from calamus_research_file import FileToken, file_token
from calamus_source_note_store import (
    MarkdownSourceNoteStore,
    SourceNoteSnapshot,
    source_notes_path,
)


class SnapshotStore(Protocol):
    def load(self): ...


def _timestamp(now_provider: Callable[[], datetime] | None) -> str:
    provider = now_provider or (lambda: datetime.now().astimezone())
    value = provider()
    if not isinstance(value, datetime):
        raise TypeError("now_provider must return datetime")
    if value.tzinfo is None:
        value = value.astimezone()
    return value.isoformat(timespec="seconds")


def build_document_dossier_inputs(
    *,
    document_text: str,
    document_path: str | None,
    modified: bool,
    bookmarks: Iterable[int],
    reference_store: SnapshotStore,
    reference_set_store: SnapshotStore,
    source_note_store_factory: Callable[[str], SnapshotStore] = MarkdownSourceNoteStore,
    now_provider: Callable[[], datetime] | None = None,
) -> DocumentDossierInputs:
    """Load current authorities once and return a read-only dossier input.

    No controller or GTK widget is mutated.  An untitled document receives an
    explicit empty Source Notes snapshot because no sidecar identity exists.
    """
    if not isinstance(document_text, str):
        raise TypeError("document_text must be str")
    if document_path is not None and not isinstance(document_path, str):
        raise TypeError("document_path must be str or None")
    if not hasattr(reference_store, "load") or not hasattr(reference_set_store, "load"):
        raise TypeError("authority stores must implement load()")
    if not callable(source_note_store_factory):
        raise TypeError("source_note_store_factory must be callable")

    references = reference_store.load()
    sets = reference_set_store.load()
    if not isinstance(references, ReferenceLibrarySnapshot):
        raise TypeError("reference_store.load() must return ReferenceLibrarySnapshot")
    if not isinstance(sets, ReferenceSetSnapshot):
        raise TypeError("reference_set_store.load() must return ReferenceSetSnapshot")

    path = (document_path or "").strip()
    sidecar = source_notes_path(path)
    if sidecar is None:
        notes = SourceNoteSnapshot((), FileToken(False), ())
    else:
        notes = source_note_store_factory(sidecar).load()
        if not isinstance(notes, SourceNoteSnapshot):
            raise TypeError("Source Notes store must return SourceNoteSnapshot")

    return DocumentDossierInputs(
        document_text=document_text,
        document_path=path,
        modified=bool(modified),
        bookmarks=tuple(bookmarks),
        reference_snapshot=references,
        source_note_snapshot=notes,
        reference_set_snapshot=sets,
        document_token=file_token(path) if path else FileToken(False),
        refreshed_at=_timestamp(now_provider),
    )


def _default_document_overview_view_factory():
    """Return the concrete GTK view factory at the application boundary.

    The import is deliberately local: importing dossier inputs and the runtime
    remains possible in non-GTK test processes, while the running application
    owns the concrete view selection.
    """
    from calamus_document_overview_view import build_document_overview_view

    return build_document_overview_view



@dataclass(frozen=True)
class DocumentOverviewCompositionInput:
    dialog_parent: Any
    text_view: Any
    document_text: Callable[[], str]
    document_path: Callable[[], str | None]
    document_modified: Callable[[], bool]
    bookmarks: Callable[[], tuple[int, ...]]
    reference_store: SnapshotStore
    reference_set_store: SnapshotStore
    set_cursor_offset: Callable[[int], Any]
    get_cursor_offset: Callable[[], int]
    select_range: Callable[[int, int], Any]
    show_reference: Callable[[str], Any]
    show_source_note: Callable[[str], Any]
    show_reference_set: Callable[[str], Any]
    run_research_check: Callable[[], Any]
    show_error: Callable[[str], Any]
    show_notice: Callable[[str], Any]


@dataclass(frozen=True)
class DocumentOverviewComponents:
    controller: Any
    runtime: Any


def _present_document_editor(present_window, focus_document) -> bool:
    if not callable(present_window) or not callable(focus_document):
        return False
    present_window()
    focus_document()
    return True


def navigate_document_overview_offset(
    document_text,
    set_cursor_offset,
    get_cursor_offset,
    present_window,
    focus_document,
    offset,
):
    if not isinstance(offset, int) or isinstance(offset, bool):
        return False
    if offset < 0 or offset > len(document_text()):
        return False
    set_cursor_offset(offset)
    if get_cursor_offset() != offset:
        return False
    return _present_document_editor(present_window, focus_document)


def navigate_document_overview_range(
    document_text,
    select_range,
    present_window,
    focus_document,
    start,
    end,
):
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in (start, end)):
        return False
    if start < 0 or end <= start or end > len(document_text()):
        return False
    select_range(start, end)
    return _present_document_editor(present_window, focus_document)


def build_document_overview(inputs: DocumentOverviewCompositionInput, *, view_factory=None) -> DocumentOverviewComponents:
    """Compose W96 from exact document/research/window capabilities."""
    from calamus_document_dossier_controller import DocumentDossierController
    from calamus_document_overview_runtime import DocumentOverviewRuntime

    if not isinstance(inputs, DocumentOverviewCompositionInput):
        raise TypeError("inputs must be DocumentOverviewCompositionInput")
    if view_factory is None:
        view_factory = _default_document_overview_view_factory()
    if not callable(view_factory):
        raise TypeError("view_factory must be callable")

    controller = DocumentDossierController(
        lambda: build_document_dossier_inputs(
            document_text=inputs.document_text(),
            document_path=inputs.document_path(),
            modified=inputs.document_modified(),
            bookmarks=inputs.bookmarks(),
            reference_store=inputs.reference_store,
            reference_set_store=inputs.reference_set_store,
        )
    )
    runtime = DocumentOverviewRuntime(
        inputs.dialog_parent,
        controller,
        navigate_offset=lambda offset: navigate_document_overview_offset(
            inputs.document_text,
            inputs.set_cursor_offset,
            inputs.get_cursor_offset,
            inputs.dialog_parent.present,
            inputs.text_view.grab_focus,
            offset,
        ),
        select_range=lambda start, end: navigate_document_overview_range(
            inputs.document_text,
            inputs.select_range,
            inputs.dialog_parent.present,
            inputs.text_view.grab_focus,
            start,
            end,
        ),
        show_reference=inputs.show_reference,
        show_source_note=inputs.show_source_note,
        show_reference_set=inputs.show_reference_set,
        run_research_check=inputs.run_research_check,
        focus_document=inputs.text_view.grab_focus,
        show_error=inputs.show_error,
        show_notice=inputs.show_notice,
        view_factory=view_factory,
    )
    return DocumentOverviewComponents(controller=controller, runtime=runtime)


def show_reference_set_name(show_panel, show_set, name):
    if not callable(show_panel) or not callable(show_set):
        raise TypeError("reference-set presentation capabilities must be callable")
    show_panel("reference-sets")
    return show_set(name)

def refresh_document_overview_if_open(runtime) -> bool:
    return bool(runtime and runtime.refresh_if_open())
