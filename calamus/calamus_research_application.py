"""W107 Research application runtime.

This GTK-free orchestration object owns the application-facing Research command
flow.  It receives narrow editor/document/navigation capabilities and a
set-once Research component bundle; it never receives the whole App object.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from calamus_authoring_bridge import EditorSelectionSnapshot, HeadingLinkPlan
from calamus_commands import insert_at as command_insert_at
from calamus_research_coordination import ResearchInvalidationReason


@dataclass(frozen=True)
class ResearchApplicationPorts:
    document_text: Callable[[], str]
    execute_command: Callable[..., bool]
    set_cursor_offset: Callable[[int], Any]
    selection_offsets: Callable[[], tuple[int, int]]
    cursor_offset: Callable[[], int]
    select_range: Callable[[int, int], Any]
    focus_editor: Callable[[], Any]
    copy_text: Callable[[str], bool]
    show_error: Callable[[str], Any]
    choose_quick_cite: Callable[[Any, str | None], Any]
    refresh_ui_state: Callable[[], Any]

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not callable(value):
                raise TypeError(f"{name} must be callable")


class ResearchApplicationRuntime:
    __slots__ = (
        "document_session",
        "navigation_controller",
        "ports",
        "_components",
    )

    def __init__(self, *, document_session, navigation_controller, ports: ResearchApplicationPorts) -> None:
        if document_session is None or navigation_controller is None:
            raise TypeError("Research application dependencies are required")
        if not isinstance(ports, ResearchApplicationPorts):
            raise TypeError("ports must be ResearchApplicationPorts")
        self.document_session = document_session
        self.navigation_controller = navigation_controller
        self.ports = ports
        self._components = None

    def bind_components(self, components) -> None:
        if self._components is not None:
            raise RuntimeError("Research components already bound")
        if components is None:
            raise TypeError("Research components are required")
        self._components = components

    @property
    def components(self):
        if self._components is None:
            raise RuntimeError("Research runtime used before component binding")
        return self._components

    def refresh_clip_list(self):
        return self.components.clip_collection.refresh()

    def on_research_item_toggled(self, item):
        return self.components.panel_runtime.set_visible(bool(item.get_active()))

    def on_research_visibility_changed(self, _visible):
        self.ports.refresh_ui_state()

    def toggle_research_panel(self, *_):
        return self.components.panel_runtime.toggle()

    def show_clip_collection(self, *_):
        return self.components.panel_runtime.show("clip-collection")

    def show_scratchpad(self, *_):
        return self.components.panel_runtime.show("scratchpad")

    def on_capture_selection_in_scratchpad(self, *_):
        return self.components.scratchpad_runtime.capture_selection()

    def on_new_scratchpad_for_current_section(self, *_):
        return self.components.scratchpad_runtime.new_for_current_section()

    def on_show_scratchpad_for_current_section(self, *_):
        self.components.panel_runtime.show("scratchpad")
        return self.components.scratchpad_runtime.show_for_current_section()

    def show_references(self, *_):
        return self.components.panel_runtime.show("references")

    def on_open_bibliography_file(self, *_):
        if self.components.reference_panel_runtime.open_bibliography_file():
            return True
        self.ports.show_error("The bibliography file is not available.")
        return False

    def on_export_bibliography_markdown(self, *_):
        return self.components.reference_panel_runtime.export_visible_bibliography(markdown=True)

    def on_export_bibliography_text(self, *_):
        return self.components.reference_panel_runtime.export_visible_bibliography(markdown=False)

    def show_tags(self, *_):
        return self.components.panel_runtime.show("tags")

    def show_source_notes(self, *_):
        return self.components.panel_runtime.show("source-notes")

    def show_reference_sets(self, *_):
        return self.components.panel_runtime.show("reference-sets")

    def show_authoring_bridge(self, *_):
        return self.components.panel_runtime.show("authoring-bridge")

    def source_notes_snapshot(self):
        return self.components.source_note_panel_runtime.notes_snapshot(force=True)

    def current_heading_identifier(self):
        heading = self.navigation_controller.current_heading()
        if heading is None or heading.identifier is None:
            return None
        matches = self.navigation_controller.structure.headings_for_identifier(heading.identifier)
        return heading.identifier if len(matches) == 1 else None

    def authoring_selection_snapshot(self):
        text = self.ports.document_text()
        start, end = self.ports.selection_offsets()
        return EditorSelectionSnapshot(text, start, end)

    def navigate_authoring_occurrence(self, start, end, _occurrence_id):
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in (start, end)):
            return False
        if start < 0 or end <= start or end > len(self.ports.document_text()):
            return False
        self.ports.select_range(start, end)
        self.ports.focus_editor()
        return True

    def show_source_note_id(self, note_id):
        self.components.panel_runtime.show("source-notes")
        return self.components.source_note_panel_runtime.show_note(note_id)

    def show_scratchpad_entry_id(self, entry_id):
        self.components.panel_runtime.show("scratchpad")
        return self.components.scratchpad_runtime.show_entry(entry_id)

    def create_source_note_from_authoring_snapshot(self, snapshot, reference_key, target):
        if not isinstance(snapshot, EditorSelectionSnapshot):
            return False
        created = self.components.source_note_panel_runtime.add_from_selection(
            snapshot.selected_text,
            reference_key=reference_key,
            target=target,
        )
        if created:
            self.show_source_notes()
        return created

    def on_create_source_note_from_selection(self, *_):
        return self.components.authoring_bridge_runtime.on_create_source_note()

    def on_insert_link_to_heading(self, *_):
        return self.components.authoring_bridge_runtime.on_insert_heading_link()

    def apply_heading_link_plan(self, plan):
        if not isinstance(plan, HeadingLinkPlan) or not plan.changed:
            return False
        if self.ports.document_text() != plan.document_before:
            self.ports.show_error("The document changed before link insertion. Refresh and retry.")
            return False

        def edit(buffer):
            start = buffer.get_iter_at_offset(plan.replace_start)
            end = buffer.get_iter_at_offset(plan.replace_end)
            buffer.delete(start, end)
            buffer.insert(buffer.get_iter_at_offset(plan.replace_start), plan.replacement)

        changed = self.ports.execute_command(
            "Insert Link to Heading",
            edit,
            select_range=(plan.cursor_after, plan.cursor_after),
        )
        if changed:
            self.ports.focus_editor()
        return bool(changed)

    def show_reference_key(self, key):
        self.components.panel_runtime.show("references")
        return self.components.reference_panel_runtime.show_key(key)

    def insert_citation_text(self, citation):
        if not isinstance(citation, str) or not citation:
            return False
        cursor = self.ports.cursor_offset()
        _, inserted_range = command_insert_at(self.ports.document_text(), cursor, citation)

        def edit(target_buffer):
            target_buffer.insert(target_buffer.get_iter_at_offset(cursor), citation)

        changed = self.ports.execute_command("Quick Cite", edit)
        if changed:
            self.ports.set_cursor_offset(inserted_range[1])
            self.ports.focus_editor()
        return changed

    def run_quick_cite(self, initial_key=None):
        records = self.components.reference_panel_runtime.records
        if not records:
            self.ports.show_error("References is empty. Add a reference before using Quick Cite.")
            return False
        result = self.ports.choose_quick_cite(records, initial_key)
        if result is None:
            return False
        key, locator = result
        return self.components.citation_controller.quick_cite(key, locator)

    def on_quick_cite(self, *_):
        return self.run_quick_cite()

    def quick_cite_key(self, key):
        return self.run_quick_cite(initial_key=key)

    def on_open_citation_in_references(self, *_):
        cursor = self.ports.cursor_offset()
        return self.components.citation_controller.open_citation(self.ports.document_text(), cursor)

    def replace_document_for_reference_migration(self, before, after):
        if not isinstance(before, str) or not isinstance(after, str):
            return False
        if before == after or self.ports.document_text() != before:
            return False

        def edit(buffer):
            start, end = buffer.get_bounds()
            buffer.delete(start, end)
            buffer.insert(buffer.get_start_iter(), after)

        changed = self.ports.execute_command("Rename Reference Key", edit)
        return bool(changed and self.ports.document_text() == after)

    def on_rename_reference_key(self, *_):
        changed = self.components.research_integrity_runtime.rename_reference_key()
        return self.finish_research_mutation(
            changed,
            ResearchInvalidationReason.REFERENCES,
            ResearchInvalidationReason.SOURCE_NOTES,
            ResearchInvalidationReason.REFERENCE_SETS,
            ResearchInvalidationReason.DOCUMENT_CONTENT,
        )

    def on_research_check(self, *_):
        return self.components.research_integrity_runtime.research_check()

    def on_tag_integrity(self, *_):
        changed = self.components.tag_integrity_runtime.manage()
        return self.finish_research_mutation(
            changed,
            ResearchInvalidationReason.REFERENCES,
            ResearchInvalidationReason.SOURCE_NOTES,
            ResearchInvalidationReason.SCRATCHPAD,
        )

    def on_import_bibtex_biblatex(self, *_):
        changed = self.components.bibtex_runtime.import_references()
        return self.finish_research_mutation(changed, ResearchInvalidationReason.REFERENCES)

    def on_export_references_bibtex_biblatex(self, *_):
        return self.components.bibtex_runtime.export_references()

    def on_export_research_apparatus(self, *_):
        return self.components.research_export_runtime.export()

    def on_export_with_pandoc(self, *_):
        return self.components.pandoc_export_runtime.export()

    def show_heading_target(self, target):
        return self.navigation_controller.navigate_identifier(target) is not None

    def finish_research_mutation(self, changed, *reasons):
        if changed:
            self.publish_research_invalidation(*reasons)
        return changed

    def publish_research_invalidation(self, *reasons):
        if self._components is not None:
            self.components.coordinator.publish(reasons)

    def research_document_context_changed(self):
        self.sync_source_notes_document(force=True)
        self.publish_research_invalidation(ResearchInvalidationReason.DOCUMENT_IDENTITY)
        return True

    def sync_source_notes_document(self, *, force=False):
        if self._components is None:
            return True
        self.components.source_note_panel_runtime.sync_document(force=force)
        self.components.scratchpad_runtime.sync_document(force=force)
        return True

    def current_section_target(self):
        identifier = self.current_heading_identifier()
        return f"#{identifier}" if identifier else None

    def selected_text(self):
        start, end = self.ports.selection_offsets()
        if start == end:
            return ""
        return self.ports.document_text()[start:end]

    def insert_scratchpad_body(self, body):
        if not isinstance(body, str) or not body:
            return False
        cursor = self.ports.cursor_offset()

        def edit(target_buffer):
            target_buffer.insert(target_buffer.get_iter_at_offset(cursor), body)

        changed = self.ports.execute_command("Insert Scratchpad Body", edit)
        if changed:
            self.ports.set_cursor_offset(cursor + len(body))
            self.ports.focus_editor()
        return bool(changed)

    def copy_scratchpad_body(self, body):
        return self.ports.copy_text(body)

    def toggle_clip_collection(self, *_):
        return self.show_clip_collection()

    def insert_clip_number(self, number):
        if self.components.clip_collection.select_number(number):
            return self.components.clip_collection_runtime.on_insert()
        return False

    def on_insert_clip(self, *_):
        return self.components.clip_collection_runtime.on_quick_insert()

    def on_clip_add_selection(self, *_):
        return self.components.clip_collection_runtime.on_capture()

    def on_clip_insert(self, *_):
        return self.components.clip_collection_runtime.on_insert()

    def on_clip_delete(self, *_):
        return self.components.clip_collection_runtime.on_delete()
