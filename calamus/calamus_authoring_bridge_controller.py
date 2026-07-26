"""GTK-free controller for the on-demand Calamus Authoring Bridge."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Protocol

from calamus_authoring_bridge import (
    AuthoringBridgeProjection,
    BridgeOccurrence,
    BridgeSubject,
    build_authoring_bridge_projection,
)
from calamus_document_structure import DocumentStructure
from calamus_references import ReferenceRecord
from calamus_source_notes import SourceNote


class AuthoringBridgeView(Protocol):
    @property
    def widget(self) -> Any: ...
    def set_subjects(
        self,
        mode: str,
        subjects: tuple[BridgeSubject, ...],
        selected_id: str | None,
    ) -> None: ...
    def render(
        self,
        occurrences: tuple[BridgeOccurrence, ...],
        selected_id: str | None,
        status: str,
    ) -> None: ...
    def selected_occurrence_id(self) -> str | None: ...
    def select_occurrence_id(self, occurrence_id: str | None) -> bool: ...
    def focus_subject(self) -> None: ...


class AuthoringBridgeController:
    """Own one immutable projection snapshot and direct navigation dispatch."""

    def __init__(
        self,
        view: AuthoringBridgeView,
        *,
        reference_records_provider: Callable[[], Iterable[ReferenceRecord]],
        document_text_provider: Callable[[], str],
        source_notes_provider: Callable[[], Iterable[SourceNote]],
        document_structure_provider: Callable[[], DocumentStructure],
        selected_reference_provider: Callable[[], str | None],
        current_heading_provider: Callable[[], str | None],
        navigate_document: Callable[[int, int, str], bool],
        show_source_note: Callable[[str], bool],
        show_reference: Callable[[str], bool],
        on_error: Callable[[str], None],
    ) -> None:
        required_view = (
            "widget",
            "set_subjects",
            "render",
            "selected_occurrence_id",
            "select_occurrence_id",
            "focus_subject",
        )
        if any(not hasattr(view, name) for name in required_view):
            raise TypeError("view must implement AuthoringBridgeView")
        callbacks = (
            reference_records_provider,
            document_text_provider,
            source_notes_provider,
            document_structure_provider,
            selected_reference_provider,
            current_heading_provider,
            navigate_document,
            show_source_note,
            show_reference,
            on_error,
        )
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("Authoring Bridge callbacks must be callable")
        self._view = view
        self._reference_records_provider = reference_records_provider
        self._document_text_provider = document_text_provider
        self._source_notes_provider = source_notes_provider
        self._document_structure_provider = document_structure_provider
        self._selected_reference_provider = selected_reference_provider
        self._current_heading_provider = current_heading_provider
        self._navigate_document = navigate_document
        self._show_source_note = show_source_note
        self._show_reference = show_reference
        self._on_error = on_error
        self._projection: AuthoringBridgeProjection | None = None
        self._mode = "reference"
        self._subject_id: str | None = None
        self._visible_occurrences: tuple[BridgeOccurrence, ...] = ()
        self._view.set_subjects("reference", (), None)
        self._view.render((), None, "Select Refresh to derive Authoring Bridge relationships.")

    @property
    def widget(self) -> Any:
        return self._view.widget

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def subject_id(self) -> str | None:
        return self._subject_id

    @property
    def projection(self) -> AuthoringBridgeProjection | None:
        return self._projection

    @property
    def visible_occurrences(self) -> tuple[BridgeOccurrence, ...]:
        return self._visible_occurrences

    def activate(self) -> None:
        self.refresh(prefer_context=True)
        self._view.focus_subject()

    def refresh(self, *, prefer_context: bool = False) -> AuthoringBridgeProjection | None:
        try:
            records = tuple(self._reference_records_provider())
            text = self._document_text_provider()
            notes = tuple(self._source_notes_provider())
            structure = self._document_structure_provider()
            projection = build_authoring_bridge_projection(records, text, notes, structure)
        except (TypeError, ValueError, OSError) as error:
            self._on_error(str(error))
            return None
        self._projection = projection
        self._sync_subjects(prefer_context=prefer_context)
        return projection

    def set_mode(self, mode: str) -> bool:
        if mode not in {"reference", "heading", "related", "issues"}:
            self._on_error("Authoring Bridge mode is invalid.")
            return False
        self._mode = mode
        self._sync_subjects(prefer_context=True)
        return True

    def set_subject(self, subject_id: str | None) -> bool:
        if self._projection is None:
            return False
        subjects = self._projection.subjects(self._mode)
        ids = {subject.identifier for subject in subjects}
        if subject_id not in ids:
            self._subject_id = subjects[0].identifier if subjects else None
        else:
            self._subject_id = subject_id
        self._view.set_subjects(self._mode, subjects, self._subject_id)
        self._render()
        return self._subject_id is not None

    def selected_occurrence(self) -> BridgeOccurrence | None:
        occurrence_id = self._view.selected_occurrence_id()
        return next(
            (item for item in self._visible_occurrences if item.id == occurrence_id),
            None,
        )

    def open_selected(self) -> bool:
        occurrence = self.selected_occurrence()
        if occurrence is None:
            self._on_error("Select an Authoring Bridge result first.")
            return False
        if occurrence.navigation_kind == "source-note":
            if not self._show_source_note(occurrence.source_note_id):
                self._on_error(
                    f"Source Note is no longer available: {occurrence.source_note_id}"
                )
                return False
            return True
        if occurrence.navigation_kind == "reference":
            if not self._show_reference(occurrence.reference_key):
                self._on_error(
                    f"Reference is no longer available: {occurrence.reference_key}"
                )
                return False
            return True

        assert occurrence.start_offset is not None and occurrence.end_offset is not None
        if self._projection is None:
            return False
        current_text = self._document_text_provider()
        if not isinstance(current_text, str):
            self._on_error("Document provider returned an invalid snapshot.")
            return False
        if current_text != self._projection.document_text:
            self._on_error(
                "The document changed after this projection was built. "
                "Select Refresh and retry."
            )
            return False
        return bool(
            self._navigate_document(
                occurrence.start_offset,
                occurrence.end_offset,
                occurrence.id,
            )
        )

    def _sync_subjects(self, *, prefer_context: bool) -> None:
        if self._projection is None:
            return
        subjects = self._projection.subjects(self._mode)
        ids = {subject.identifier for subject in subjects}
        preferred: str | None = None
        if prefer_context and self._mode in {"reference", "related"}:
            preferred = self._selected_reference_provider()
        elif prefer_context and self._mode == "heading":
            preferred = self._current_heading_provider()
        if preferred not in ids:
            preferred = self._subject_id if self._subject_id in ids else None
        self._subject_id = preferred or (subjects[0].identifier if subjects else None)
        self._view.set_subjects(self._mode, subjects, self._subject_id)
        self._render()

    def _render(self) -> None:
        if self._projection is None or self._subject_id is None:
            self._visible_occurrences = ()
            mode_label = {
                "reference": "References",
                "heading": "Headings",
                "related": "Related References",
                "issues": "Broken Links",
            }[self._mode]
            self._view.render((), None, f"No {mode_label.lower()} are available.")
            return
        visible = self._projection.items(self._mode, self._subject_id)
        selected = self._view.selected_occurrence_id()
        ids = {item.id for item in visible}
        if selected not in ids:
            selected = visible[0].id if visible else None
        self._visible_occurrences = visible
        noun = "result" if len(visible) == 1 else "results"
        status = (
            f"{len(visible)} derived {noun}. "
            "Refresh after document, References, or Source Notes changes."
        )
        self._view.render(visible, selected, status)
