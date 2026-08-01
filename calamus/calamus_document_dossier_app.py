"""GTK-free App boundary for building W96 Document Dossier inputs.

The App supplies only live editor state and existing authority stores.  This
module performs bounded, read-only loading and returns the immutable input
value consumed by :mod:`calamus_document_dossier`.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Protocol

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


def build_document_overview(app, *, view_factory=None) -> None:
    """Compose W96 from App authorities and the application-owned GTK view."""
    from calamus_document_dossier_controller import DocumentDossierController
    from calamus_document_overview_runtime import DocumentOverviewRuntime

    if view_factory is None:
        view_factory = _default_document_overview_view_factory()
    if not callable(view_factory):
        raise TypeError("view_factory must be callable")

    app.document_dossier_controller = DocumentDossierController(
        lambda: build_document_dossier_inputs(
            document_text=app.buffer_text(),
            document_path=app.document.file_path,
            modified=app.modified,
            bookmarks=tuple(app.bookmarks),
            reference_store=app.reference_store,
            reference_set_store=app.reference_set_store,
        )
    )
    app.document_overview_runtime = DocumentOverviewRuntime(
        app,
        app.document_dossier_controller,
        navigate_offset=lambda offset: navigate_document_overview_offset(app, offset),
        select_range=lambda start, end: navigate_document_overview_range(app, start, end),
        show_reference=app.show_reference_key,
        show_source_note=app.show_source_note_id,
        show_reference_set=lambda name: show_reference_set_name(app, name),
        run_research_check=lambda: app.on_research_check(),
        focus_document=app.text.grab_focus,
        show_error=lambda message: app.error(message),
        show_notice=lambda message: app.info(message),
        view_factory=view_factory,
    )


def on_document_overview(app, *_):
    return app.document_overview_runtime.open()


def refresh_document_overview_if_open(app):
    runtime = getattr(app, "document_overview_runtime", None)
    return bool(runtime and runtime.refresh_if_open())


def _present_document_editor(app) -> bool:
    """Transfer the user from a non-modal tool window back to the editor.

    A widget-level focus request only chooses the focus widget inside its own
    toplevel.  It does not make an inactive parent window visible or active.
    Document Overview navigation therefore owns the whole handoff: present the
    main window first, then focus the text view.  The caller has already moved
    the insert mark or selection before this function is invoked.
    """
    present = getattr(app, "present", None)
    text = getattr(app, "text", None)
    grab_focus = getattr(text, "grab_focus", None)
    if not callable(present) or not callable(grab_focus):
        return False
    present()
    grab_focus()
    return True


def navigate_document_overview_offset(app, offset):
    if not isinstance(offset, int) or isinstance(offset, bool):
        return False
    if offset < 0 or offset > len(app.buffer_text()):
        return False
    app.set_cursor_offset(offset)
    if app.get_cursor_offset() != offset:
        return False
    return _present_document_editor(app)


def navigate_document_overview_range(app, start, end):
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in (start, end)):
        return False
    if start < 0 or end <= start or end > len(app.buffer_text()):
        return False
    app.select_range(start, end)
    return _present_document_editor(app)


def show_reference_set_name(app, name):
    app.research_panel_runtime.show("reference-sets")
    return app.reference_set_runtime.show_set(name)
