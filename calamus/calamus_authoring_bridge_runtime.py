"""UI coordinator for the on-demand Calamus Authoring Bridge client."""
from __future__ import annotations

from typing import Callable, Iterable

from calamus_authoring_bridge import (
    EditorSelectionSnapshot,
    plan_heading_link_insertion,
    unique_heading_identifier_at_offset,
)
from calamus_authoring_bridge_controller import AuthoringBridgeController
from calamus_authoring_bridge_dialogs import run_heading_link_dialog
from calamus_authoring_bridge_view import build_authoring_bridge_view
from calamus_document_structure import DocumentStructure, build_document_structure
from calamus_references import ReferenceRecord
from calamus_source_notes import SourceNote


class AuthoringBridgeRuntime:
    """Coordinate projections and explicit authoring actions.

    Modal actions capture one immutable editor snapshot before opening a
    dialog.  The nested GTK loop may move focus or clear the visible selection,
    but the planned operation continues to use the original text and offsets.
    """

    def __init__(
        self,
        parent,
        *,
        reference_records_provider: Callable[[], Iterable[ReferenceRecord]],
        document_text_provider: Callable[[], str],
        source_notes_provider: Callable[[], Iterable[SourceNote]],
        document_structure_provider: Callable[[], DocumentStructure],
        selected_reference_provider: Callable[[], str | None],
        current_heading_provider: Callable[[], str | None],
        selection_provider: Callable[[], EditorSelectionSnapshot],
        navigate_document: Callable[[int, int, str], bool],
        show_source_note: Callable[[str], bool],
        create_source_note_from_snapshot: Callable[
            [EditorSelectionSnapshot, str, str], bool
        ],
        apply_heading_link_plan: Callable[[object], bool],
        on_error: Callable[[str], None],
    ) -> None:
        callbacks = (
            reference_records_provider,
            document_text_provider,
            source_notes_provider,
            document_structure_provider,
            selected_reference_provider,
            current_heading_provider,
            selection_provider,
            navigate_document,
            show_source_note,
            create_source_note_from_snapshot,
            apply_heading_link_plan,
            on_error,
        )
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("Authoring Bridge runtime callbacks must be callable")
        self._parent = parent
        self._selected_reference_provider = selected_reference_provider
        self._selection_provider = selection_provider
        self._create_source_note_from_snapshot = create_source_note_from_snapshot
        self._apply_heading_link_plan = apply_heading_link_plan
        self._on_error = on_error
        self._view = build_authoring_bridge_view(
            self.on_open,
            self.on_refresh,
            self.on_create_source_note,
            self.on_insert_heading_link,
        )
        self._controller = AuthoringBridgeController(
            self._view,
            reference_records_provider=reference_records_provider,
            document_text_provider=document_text_provider,
            source_notes_provider=source_notes_provider,
            document_structure_provider=document_structure_provider,
            selected_reference_provider=selected_reference_provider,
            current_heading_provider=current_heading_provider,
            navigate_document=navigate_document,
            show_source_note=show_source_note,
            on_error=on_error,
        )
        self._view.bind_controls(
            self._controller.set_mode,
            self._controller.set_subject,
        )

    @property
    def widget(self):
        return self._view.widget

    @property
    def controller(self) -> AuthoringBridgeController:
        return self._controller

    def activate(self) -> None:
        self._controller.activate()

    def on_refresh(self, *_):
        return self._controller.refresh(prefer_context=False) is not None

    def on_open(self, *_):
        return self._controller.open_selected()

    def _capture_selection(self) -> EditorSelectionSnapshot | None:
        try:
            snapshot = self._selection_provider()
        except (TypeError, ValueError, OSError) as error:
            self._on_error(str(error))
            return None
        if not isinstance(snapshot, EditorSelectionSnapshot):
            self._on_error("Editor selection provider returned an invalid snapshot.")
            return None
        return snapshot

    def on_create_source_note(self, *_):
        snapshot = self._capture_selection()
        if snapshot is None:
            return False
        if not snapshot.has_selection or not snapshot.selected_text.strip():
            self._on_error("Select document text before creating a Source Note.")
            return False
        structure = build_document_structure(snapshot.document_text)
        heading_id = unique_heading_identifier_at_offset(
            structure,
            snapshot.start_offset,
        )
        reference_key = self._selected_reference_provider() or ""
        target = f"#{heading_id}" if heading_id else ""
        return bool(
            self._create_source_note_from_snapshot(
                snapshot,
                reference_key,
                target,
            )
        )

    def on_insert_heading_link(self, *_):
        snapshot = self._capture_selection()
        if snapshot is None:
            return False
        selected_text = snapshot.selected_text
        if selected_text and ("\n" in selected_text or "\r" in selected_text):
            self._on_error("Heading link text must stay on one line.")
            return False

        structure = build_document_structure(snapshot.document_text)
        headings = []
        for heading in structure.headings:
            identifier = heading.identifier
            if identifier is None:
                continue
            if len(structure.headings_for_identifier(identifier)) != 1:
                continue
            headings.append(
                (
                    identifier,
                    f"{heading.display_title} — #{identifier} — line {heading.line}",
                    heading.display_title,
                )
            )
        if not headings:
            self._on_error(
                "The document has no explicit, unique {#heading-id} available for linking."
            )
            return False
        current = unique_heading_identifier_at_offset(
            structure,
            snapshot.start_offset,
        ) or ""
        result = run_heading_link_dialog(
            self._parent,
            tuple(headings),
            default_identifier=current,
            default_label=selected_text,
        )
        if result is None:
            return False
        identifier, label = result
        try:
            plan = plan_heading_link_insertion(
                snapshot.document_text,
                snapshot.start_offset,
                snapshot.end_offset,
                identifier,
                label,
                structure,
            )
        except (TypeError, ValueError) as error:
            self._on_error(str(error))
            return False
        return bool(self._apply_heading_link_plan(plan))
