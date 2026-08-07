"""W107 Research subsystem composition boundary.

The old 246-line ``App.build_research_panel`` graph is constructed here from
explicit narrow inputs.  The returned immutable component record is the owner;
App projections exist only for published compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from calamus_authoring_bridge_runtime import AuthoringBridgeRuntime
from calamus_bibtex_controller import BibtexController
from calamus_bibtex_runtime import BibtexRuntime
from calamus_citation_controller import CitationController
from calamus_citation_dialogs import choose_citation_key, run_quick_cite_dialog
from calamus_clipboard_gtk import copy_text as copy_clipboard_text
from calamus_pandoc_controller import PandocExportController
from calamus_pandoc_runtime import PandocExportRuntime
from calamus_reference_runtime import ReferencePanelRuntime
from calamus_reference_set_runtime import ReferenceSetRuntime
from calamus_reference_set_store import MarkdownReferenceSetStore
from calamus_reference_store import MarkdownReferenceStore
from calamus_research_application import ResearchApplicationPorts, ResearchApplicationRuntime
from calamus_research_coordination import (
    ResearchClientSpec,
    ResearchInvalidationReason,
    ResearchPanelCoordinator,
)
from calamus_research_export_controller import ResearchExportController
from calamus_research_export_runtime import ResearchExportRuntime
from calamus_research_integrity_controller import ResearchIntegrityController
from calamus_research_integrity_runtime import ResearchIntegrityRuntime
from calamus_research_panel import ResearchPanelRuntime
from calamus_research_panel_view import ResearchPanelViewAdapter
from calamus_scratchpad_runtime import ScratchpadRuntime
from calamus_source_note_runtime import SourceNotePanelRuntime
from calamus_tag_integrity_controller import TagIntegrityController
from calamus_tag_integrity_runtime import TagIntegrityRuntime
from calamus_tags_runtime import TagsRuntime
from calamus_workspace_external import open_external_path, reveal_in_file_manager
from calamus_dialogs import show_error, show_info


@dataclass(frozen=True)
class ResearchCompositionInput:
    dialog_parent: Any
    right_panel_host: Any
    text_view: Any
    document_session: Any
    navigation_controller: Any
    clip_collection: Any
    clip_collection_runtime: Any
    document_text: Callable[[], str]
    execute_command: Callable[..., bool]
    set_cursor_offset: Callable[[int], Any]
    refresh_ui_state: Callable[[], Any]
    schedule: Callable[[int, Callable[..., Any]], Any]
    cancel: Callable[[Any], Any]

    def __post_init__(self) -> None:
        required = (
            self.document_text,
            self.execute_command,
            self.set_cursor_offset,
            self.refresh_ui_state,
            self.schedule,
            self.cancel,
        )
        if any(not callable(value) for value in required):
            raise TypeError("Research composition callables must be callable")


@dataclass(frozen=True)
class ResearchSubsystemComponents:
    runtime: ResearchApplicationRuntime
    reference_store: Any
    reference_set_store: Any
    reference_panel_runtime: Any
    reference_set_runtime: Any
    citation_controller: Any
    source_note_panel_runtime: Any
    authoring_bridge_runtime: Any
    scratchpad_runtime: Any
    tag_integrity_controller: Any
    tags_runtime: Any
    tag_integrity_runtime: Any
    panel_view: Any
    coordinator: Any
    panel_runtime: Any
    research_integrity_controller: Any
    research_integrity_runtime: Any
    research_export_controller: Any
    research_export_runtime: Any
    bibtex_controller: Any
    bibtex_runtime: Any
    pandoc_export_controller: Any
    pandoc_export_runtime: Any
    clip_collection: Any
    clip_collection_runtime: Any


def build_research_subsystem(inputs: ResearchCompositionInput) -> ResearchSubsystemComponents:
    if not isinstance(inputs, ResearchCompositionInput):
        raise TypeError("inputs must be ResearchCompositionInput")

    def selection_offsets():
        buffer = inputs.text_view.get_buffer()
        if buffer.get_has_selection():
            start, end = buffer.get_selection_bounds()
            return start.get_offset(), end.get_offset()
        cursor = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()
        return cursor, cursor

    def cursor_offset():
        buffer = inputs.text_view.get_buffer()
        return buffer.get_iter_at_mark(buffer.get_insert()).get_offset()

    def select_range(start, end):
        buffer = inputs.text_view.get_buffer()
        it1 = buffer.get_iter_at_offset(start)
        it2 = buffer.get_iter_at_offset(end)
        buffer.select_range(it1, it2)
        inputs.text_view.scroll_to_iter(it1, 0.15, False, 0, 0)

    runtime = ResearchApplicationRuntime(
        document_session=inputs.document_session,
        navigation_controller=inputs.navigation_controller,
        ports=ResearchApplicationPorts(
            document_text=inputs.document_text,
            execute_command=inputs.execute_command,
            set_cursor_offset=inputs.set_cursor_offset,
            selection_offsets=selection_offsets,
            cursor_offset=cursor_offset,
            select_range=select_range,
            focus_editor=inputs.text_view.grab_focus,
            copy_text=copy_clipboard_text,
            show_error=lambda message: show_error(inputs.dialog_parent, message),
            choose_quick_cite=lambda records, initial_key: run_quick_cite_dialog(
                inputs.dialog_parent, records, initial_key=initial_key
            ),
            refresh_ui_state=inputs.refresh_ui_state,
        ),
    )

    reference_store = MarkdownReferenceStore()
    reference_set_store = MarkdownReferenceSetStore()

    reference_panel_runtime = ReferencePanelRuntime(
        inputs.dialog_parent,
        store=reference_store,
        quick_cite=runtime.quick_cite_key,
        document_text_provider=inputs.document_text,
        source_notes_provider=runtime.source_notes_snapshot,
        reference_sets_provider=lambda: reference_set_runtime.sets_snapshot(force=True),
        open_external=open_external_path,
        reveal_external=reveal_in_file_manager,
        on_changed=lambda: runtime.publish_research_invalidation(ResearchInvalidationReason.REFERENCES),
    )

    reference_set_runtime = ReferenceSetRuntime(
        inputs.dialog_parent,
        records_provider=lambda: reference_panel_runtime.records,
        show_reference=runtime.show_reference_key,
        store=reference_set_store,
        on_changed=lambda: runtime.publish_research_invalidation(ResearchInvalidationReason.REFERENCE_SETS),
    )

    citation_controller = CitationController(
        reference_records_provider=lambda: reference_panel_runtime.records,
        insert_text=runtime.insert_citation_text,
        show_reference=runtime.show_reference_key,
        choose_key=lambda keys: choose_citation_key(inputs.dialog_parent, keys),
        on_error=lambda message: show_error(inputs.dialog_parent, message),
    )

    source_note_panel_runtime = SourceNotePanelRuntime(
        inputs.dialog_parent,
        document_path_provider=lambda: inputs.document_session.file_path,
        reference_keys_provider=lambda: reference_panel_runtime.keys,
        document_structure_provider=lambda: inputs.navigation_controller.structure,
        show_reference=runtime.show_reference_key,
        reference_key_resolver=reference_panel_runtime.resolve_key,
        show_target=runtime.show_heading_target,
        on_changed=lambda: runtime.publish_research_invalidation(ResearchInvalidationReason.SOURCE_NOTES),
    )

    authoring_bridge_runtime = AuthoringBridgeRuntime(
        inputs.dialog_parent,
        reference_records_provider=lambda: reference_panel_runtime.records_snapshot(force=True),
        document_text_provider=inputs.document_text,
        source_notes_provider=runtime.source_notes_snapshot,
        document_structure_provider=lambda: inputs.navigation_controller.structure,
        selected_reference_provider=lambda: reference_panel_runtime.selected_key,
        current_heading_provider=runtime.current_heading_identifier,
        selection_provider=runtime.authoring_selection_snapshot,
        navigate_document=runtime.navigate_authoring_occurrence,
        show_source_note=runtime.show_source_note_id,
        show_reference=runtime.show_reference_key,
        create_source_note_from_snapshot=runtime.create_source_note_from_authoring_snapshot,
        apply_heading_link_plan=runtime.apply_heading_link_plan,
        on_error=lambda message: show_error(inputs.dialog_parent, message),
    )

    scratchpad_runtime = ScratchpadRuntime(
        inputs.dialog_parent,
        document_path_provider=lambda: inputs.document_session.file_path,
        document_structure_provider=lambda: inputs.navigation_controller.structure,
        current_section_provider=runtime.current_section_target,
        selected_text_provider=runtime.selected_text,
        show_target=runtime.show_heading_target,
        insert_body=runtime.insert_scratchpad_body,
        copy_body=runtime.copy_scratchpad_body,
        on_changed=lambda: runtime.publish_research_invalidation(ResearchInvalidationReason.SCRATCHPAD),
    )

    tag_integrity_controller = TagIntegrityController(
        reference_store=reference_store,
        document_path_provider=lambda: inputs.document_session.file_path,
        refresh_references=reference_panel_runtime.reload,
        refresh_source_notes=lambda: source_note_panel_runtime.sync_document(force=True),
        refresh_scratchpad=lambda: scratchpad_runtime.sync_document(force=True),
    )

    tags_runtime = TagsRuntime(
        inputs.dialog_parent,
        tag_integrity_controller,
        show_reference=runtime.show_reference_key,
        show_source_note=runtime.show_source_note_id,
        show_scratchpad_entry=runtime.show_scratchpad_entry_id,
        on_changed=lambda: runtime.publish_research_invalidation(
            ResearchInvalidationReason.REFERENCES,
            ResearchInvalidationReason.SOURCE_NOTES,
            ResearchInvalidationReason.SCRATCHPAD,
        ),
    )
    tag_integrity_runtime = TagIntegrityRuntime(inputs.dialog_parent, tag_integrity_controller)

    panel_runtime_box = {"value": None}
    panel_view = ResearchPanelViewAdapter(lambda: panel_runtime_box["value"].hide())
    coordinator = ResearchPanelCoordinator(
        active_client_provider=lambda: panel_view.active_client,
        schedule=inputs.schedule,
        cancel=inputs.cancel,
    )

    client_specs = (
        ResearchClientSpec(
            "clip-collection", "Clips", inputs.clip_collection.widget,
            inputs.clip_collection_runtime.activate,
            frozenset({ResearchInvalidationReason.CLIPS}),
            inputs.clip_collection_runtime.refresh_for_invalidation,
            inputs.clip_collection_runtime.shutdown,
        ),
        ResearchClientSpec(
            "scratchpad", "Scratchpad", scratchpad_runtime.widget,
            scratchpad_runtime.activate,
            frozenset({
                ResearchInvalidationReason.DOCUMENT_IDENTITY,
                ResearchInvalidationReason.DOCUMENT_CONTENT,
                ResearchInvalidationReason.SCRATCHPAD,
            }),
            scratchpad_runtime.refresh_for_invalidation,
            scratchpad_runtime.shutdown,
        ),
        ResearchClientSpec(
            "references", "Bibliography", reference_panel_runtime.widget,
            reference_panel_runtime.activate,
            frozenset({
                ResearchInvalidationReason.DOCUMENT_IDENTITY,
                ResearchInvalidationReason.DOCUMENT_CONTENT,
                ResearchInvalidationReason.REFERENCES,
                ResearchInvalidationReason.SOURCE_NOTES,
                ResearchInvalidationReason.REFERENCE_SETS,
            }),
            reference_panel_runtime.refresh_for_invalidation,
            reference_panel_runtime.shutdown,
        ),
        ResearchClientSpec(
            "tags", "Tags", tags_runtime.widget,
            tags_runtime.activate,
            frozenset({
                ResearchInvalidationReason.DOCUMENT_IDENTITY,
                ResearchInvalidationReason.REFERENCES,
                ResearchInvalidationReason.SOURCE_NOTES,
                ResearchInvalidationReason.SCRATCHPAD,
            }),
            tags_runtime.refresh_for_invalidation,
            tags_runtime.shutdown,
        ),
        ResearchClientSpec(
            "reference-sets", "Reference Sets", reference_set_runtime.widget,
            reference_set_runtime.activate,
            frozenset({ResearchInvalidationReason.REFERENCES, ResearchInvalidationReason.REFERENCE_SETS}),
            reference_set_runtime.refresh_for_invalidation,
            reference_set_runtime.shutdown,
        ),
        ResearchClientSpec(
            "source-notes", "Source Notes", source_note_panel_runtime.widget,
            source_note_panel_runtime.activate,
            frozenset({
                ResearchInvalidationReason.DOCUMENT_IDENTITY,
                ResearchInvalidationReason.DOCUMENT_CONTENT,
                ResearchInvalidationReason.REFERENCES,
                ResearchInvalidationReason.SOURCE_NOTES,
            }),
            source_note_panel_runtime.refresh_for_invalidation,
            source_note_panel_runtime.shutdown,
        ),
        ResearchClientSpec(
            "authoring-bridge", "Authoring Bridge", authoring_bridge_runtime.widget,
            authoring_bridge_runtime.activate,
            frozenset({
                ResearchInvalidationReason.DOCUMENT_IDENTITY,
                ResearchInvalidationReason.DOCUMENT_CONTENT,
                ResearchInvalidationReason.REFERENCES,
                ResearchInvalidationReason.SOURCE_NOTES,
            }),
            authoring_bridge_runtime.refresh_for_invalidation,
            authoring_bridge_runtime.shutdown,
        ),
    )
    for spec in client_specs:
        coordinator.register(spec)
        panel_view.register_client(
            spec.client_id,
            spec.title,
            spec.widget,
            lambda client_id=spec.client_id: coordinator.activate(client_id),
        )
    coordinator.assert_complete()
    inputs.right_panel_host.register("research", panel_view.widget)
    panel_runtime = ResearchPanelRuntime(
        inputs.right_panel_host,
        panel_view,
        inputs.text_view.grab_focus,
        on_visibility_changed=runtime.on_research_visibility_changed,
    )
    panel_runtime_box["value"] = panel_runtime

    research_integrity_controller = ResearchIntegrityController(
        reference_store=reference_store,
        document_path_provider=lambda: inputs.document_session.file_path,
        document_text_provider=inputs.document_text,
        document_structure_provider=lambda: inputs.navigation_controller.structure,
        replace_document_text=runtime.replace_document_for_reference_migration,
        refresh_references=reference_panel_runtime.reload,
        refresh_source_notes=lambda: source_note_panel_runtime.sync_document(force=True),
        reference_set_store=reference_set_store,
        refresh_reference_sets=reference_set_runtime.reload,
    )
    research_integrity_runtime = ResearchIntegrityRuntime(
        inputs.dialog_parent,
        research_integrity_controller,
        records_provider=lambda: reference_panel_runtime.records,
        selected_key_provider=lambda: reference_panel_runtime.selected_key,
    )
    research_export_controller = ResearchExportController(
        reference_store=reference_store,
        document_path_provider=lambda: inputs.document_session.file_path,
        document_text_provider=inputs.document_text,
        document_structure_provider=lambda: inputs.navigation_controller.structure,
    )
    research_export_runtime = ResearchExportRuntime(
        inputs.dialog_parent,
        research_export_controller,
        document_path_provider=lambda: inputs.document_session.file_path,
        show_error=lambda message: show_error(inputs.dialog_parent, message),
        show_info=lambda message: show_info(inputs.dialog_parent, message),
    )
    bibtex_controller = BibtexController(reference_store, refresh_references=reference_panel_runtime.reload)
    bibtex_runtime = BibtexRuntime(inputs.dialog_parent, bibtex_controller)
    pandoc_export_controller = PandocExportController(
        reference_store,
        reference_set_store,
        document_path_provider=lambda: inputs.document_session.file_path,
        document_text_provider=inputs.document_text,
    )
    pandoc_export_runtime = PandocExportRuntime(
        inputs.dialog_parent,
        pandoc_export_controller,
        document_path_provider=lambda: inputs.document_session.file_path,
        reference_set_names_provider=lambda: tuple(
            item.name for item in reference_set_runtime.sets_snapshot(force=True)
        ),
    )

    bundle = ResearchSubsystemComponents(
        runtime=runtime,
        reference_store=reference_store,
        reference_set_store=reference_set_store,
        reference_panel_runtime=reference_panel_runtime,
        reference_set_runtime=reference_set_runtime,
        citation_controller=citation_controller,
        source_note_panel_runtime=source_note_panel_runtime,
        authoring_bridge_runtime=authoring_bridge_runtime,
        scratchpad_runtime=scratchpad_runtime,
        tag_integrity_controller=tag_integrity_controller,
        tags_runtime=tags_runtime,
        tag_integrity_runtime=tag_integrity_runtime,
        panel_view=panel_view,
        coordinator=coordinator,
        panel_runtime=panel_runtime,
        research_integrity_controller=research_integrity_controller,
        research_integrity_runtime=research_integrity_runtime,
        research_export_controller=research_export_controller,
        research_export_runtime=research_export_runtime,
        bibtex_controller=bibtex_controller,
        bibtex_runtime=bibtex_runtime,
        pandoc_export_controller=pandoc_export_controller,
        pandoc_export_runtime=pandoc_export_runtime,
        clip_collection=inputs.clip_collection,
        clip_collection_runtime=inputs.clip_collection_runtime,
    )
    runtime.bind_components(bundle)
    return bundle
