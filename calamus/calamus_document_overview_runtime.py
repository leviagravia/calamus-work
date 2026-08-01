"""Single-instance GTK runtime for W96 Document Overview Core."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calamus_document_dossier import DocumentDossierSnapshot
from calamus_document_dossier_controller import DocumentDossierController
from calamus_document_overview_model import DocumentOverviewRow


class DocumentOverviewRuntime:
    def __init__(
        self,
        parent,
        controller: DocumentDossierController,
        *,
        navigate_offset: Callable[[int], object],
        select_range: Callable[[int, int], object],
        show_reference: Callable[[str], object],
        show_source_note: Callable[[str], object],
        show_reference_set: Callable[[str], object],
        run_research_check: Callable[[], object],
        focus_document: Callable[[], object],
        show_error: Callable[[str], object],
        show_notice: Callable[[str], object],
        view_factory: Callable[[Any], object],
    ) -> None:
        callbacks = (
            navigate_offset, select_range, show_reference, show_source_note,
            show_reference_set, run_research_check, focus_document, show_error,
            show_notice, view_factory,
        )
        if not isinstance(controller, DocumentDossierController):
            raise TypeError("controller must be DocumentDossierController")
        if any(not callable(callback) for callback in callbacks):
            raise TypeError("Document Overview runtime callbacks must be callable")
        self._parent = parent
        self._controller = controller
        self._navigate_offset = navigate_offset
        self._select_range = select_range
        self._show_reference = show_reference
        self._show_source_note = show_source_note
        self._show_reference_set = show_reference_set
        self._run_research_check = run_research_check
        self._focus_document = focus_document
        self._show_error = show_error
        self._show_notice = show_notice
        self._view_factory = view_factory
        self._view = None
        self._selected_category = "overview"
        self._selected_item_id: str | None = None
        self._rows: tuple[DocumentOverviewRow, ...] = ()
        self._snapshot: DocumentDossierSnapshot | None = None
        self._shutting_down = False

    @property
    def is_open(self) -> bool:
        return self._view is not None

    @property
    def window(self):
        return self._view.window if self._view is not None else None

    @property
    def selected_category(self) -> str:
        return self._selected_category

    @property
    def snapshot(self) -> DocumentDossierSnapshot | None:
        return self._snapshot

    def open(self, *_):
        if self._view is None:
            self._view = self._view_factory(self._parent)
            self._view.bind(
                on_category=self.select_category,
                on_item=self.select_item,
                on_refresh=self.refresh,
                on_primary=self.activate_primary,
                on_secondary=self.activate_secondary,
            )
            self._view.window.connect("destroy", self._on_destroy)
        self.refresh()
        self._view.present()
        return True

    def close(self, *_):
        if self._view is None:
            return False
        self._view.destroy()
        return True

    def shutdown(self) -> None:
        self._shutting_down = True
        try:
            if self._view is not None:
                self._view.destroy()
        finally:
            self._view = None
            self._snapshot = None
            self._rows = ()

    def mark_stale(self) -> None:
        self._controller.mark_stale()
        if self._view is not None:
            self._view.set_stale(True)

    def refresh_if_open(self) -> bool:
        if self._view is None:
            self.mark_stale()
            return False
        self.refresh()
        return True

    def refresh(self, *_):
        try:
            self._snapshot = self._controller.refresh()
        except Exception as error:
            self._show_error(f"Document Overview could not be refreshed.\n\n{error}")
            return False
        self._selected_item_id = None
        self._render()
        return True

    def select_category(self, category_id: str):
        if category_id not in {"overview", "structure", "research", "integrity", "statistics"}:
            return False
        self._selected_category = category_id
        self._selected_item_id = None
        self._render()
        return True

    def select_item(self, item_id: str | None):
        self._selected_item_id = item_id
        self._render_detail()
        return item_id is not None

    def activate_primary(self):
        row = self._validated_selected_row()
        if row is None:
            return False
        return self._dispatch(row, secondary=False)

    def activate_secondary(self):
        row = self._validated_selected_row()
        if row is None:
            return False
        return self._dispatch(row, secondary=True)

    def _on_destroy(self, *_):
        self._view = None
        self._snapshot = None
        self._rows = ()
        self._selected_item_id = None
        self._selected_category = "overview"
        if not self._shutting_down:
            self._focus_document()
        return False

    def _render(self) -> None:
        if self._view is None or self._snapshot is None:
            return
        snapshot = self._snapshot
        self._view.render_header(
            name=snapshot.identity.name,
            path=snapshot.identity.path,
            modified=snapshot.identity.modified,
            refreshed_at=snapshot.refreshed_at,
            stale=not self._controller.is_current(),
        )
        self._view.render_categories(self._selected_category, self._category_counts(snapshot))
        heading, rows = self._category_rows(snapshot, self._selected_category)
        self._rows = rows
        selected = self._selected_item_id if any(row.id == self._selected_item_id for row in rows) else None
        self._selected_item_id = selected
        self._view.render_items(heading, rows, selected)
        self._render_detail()

    def _render_detail(self) -> None:
        if self._view is None or self._snapshot is None:
            return
        row = self._selected_row()
        if row is None:
            title, body = self._category_summary(self._snapshot, self._selected_category)
            self._view.render_detail(title=title, body=body)
            return
        title, body, primary, secondary = self._row_detail(row)
        self._view.render_detail(title=title, body=body, primary_label=primary, secondary_label=secondary)

    def _selected_row(self) -> DocumentOverviewRow | None:
        return next((row for row in self._rows if row.id == self._selected_item_id), None)

    def _validated_selected_row(self) -> DocumentOverviewRow | None:
        """Return the selected row only while every source authority is current.

        Gate C is deliberately fail-closed. A buffer/file authority change
        refreshes the dossier, clears selection and requires a new explicit
        selection before any navigation or delegated action can run.
        """
        row = self._selected_row()
        if row is None:
            return None
        try:
            current = self._controller.is_current()
        except Exception as error:
            self._show_error(
                f"Document Overview could not validate the selected item.\n\n{error}"
            )
            return None
        if not current:
            if not self.refresh():
                return None
            self._show_notice(
                "Action blocked. Document Overview has now been refreshed because "
                "the document or its research authorities changed. Select the "
                "item again before running an action."
            )
            return None

        if self._snapshot is None:
            return None
        _heading, rows = self._category_rows(self._snapshot, self._selected_category)
        fresh = next((candidate for candidate in rows if candidate.id == row.id), None)
        if fresh is None:
            if not self.refresh():
                return None
            self._show_notice(
                "The selected Document Overview item no longer exists. The "
                "overview was refreshed; select another item."
            )
            return None
        return fresh

    @staticmethod
    def _category_counts(snapshot: DocumentDossierSnapshot) -> dict[str, int]:
        return {
            "overview": 0,
            "structure": len(snapshot.sections) + len(snapshot.bookmarks) + len(snapshot.links),
            "research": len(snapshot.citations) + len(snapshot.source_notes) + len(snapshot.references) + len(snapshot.reference_sets),
            "integrity": len(snapshot.issues),
            "statistics": len(snapshot.sections),
        }

    def _category_rows(self, snapshot: DocumentDossierSnapshot, category: str):
        rows: list[DocumentOverviewRow] = []
        if category == "structure":
            for item in snapshot.sections:
                rows.append(DocumentOverviewRow(
                    f"section:{item.id}", "section", item.title,
                    f"H{item.level} · line {item.line} · {item.word_count} words",
                    item,
                ))
            for item in snapshot.bookmarks:
                rows.append(DocumentOverviewRow(
                    f"bookmark:{item.id}", "bookmark", item.label or f"Bookmark at line {item.line}",
                    f"Line {item.line}" + (f" · section {item.section_id}" if item.section_id else ""),
                    item,
                ))
            for item in snapshot.links:
                rows.append(DocumentOverviewRow(
                    f"link:{item.id}", "link", item.label,
                    f"Line {item.line} · target #{item.identifier} · {item.status}",
                    item,
                ))
            return "Structure", tuple(rows)
        if category == "research":
            for item in snapshot.citations:
                state = "resolved" if not item.missing_keys and not item.ambiguous_keys else "needs attention"
                rows.append(DocumentOverviewRow(
                    f"citation:{item.id}", "citation", item.raw,
                    f"Line {item.line} · {len(item.requested_keys)} key(s) · {state}",
                    item,
                ))
            for item in snapshot.source_notes:
                rows.append(DocumentOverviewRow(
                    f"source-note:{item.id}", "source-note", item.excerpt,
                    f"{item.kind} · {item.status}" + (f" · {item.reference_key}" if item.reference_key else ""),
                    item,
                ))
            for item in snapshot.references:
                roles = ", ".join(item.roles)
                title = item.title or item.key
                rows.append(DocumentOverviewRow(
                    f"reference:{item.key}", "reference", title,
                    f"{item.key} · {item.status} · {roles}",
                    item,
                ))
            for item in snapshot.reference_sets:
                rows.append(DocumentOverviewRow(
                    f"reference-set:{item.name}", "reference-set", item.name,
                    f"{len(item.relevant_members)} relevant · {len(item.members)} member(s)",
                    item,
                ))
            return "Research", tuple(rows)
        if category == "integrity":
            for index, item in enumerate(snapshot.issues, start=1):
                rows.append(DocumentOverviewRow(
                    f"issue:{index}:{item.kind}:{item.subject}", "issue", item.message,
                    f"{item.severity} · {item.kind} · {item.subject}",
                    item,
                ))
            return "Integrity", tuple(rows)
        if category == "statistics":
            for item in snapshot.sections:
                rows.append(DocumentOverviewRow(
                    f"section-statistics:{item.id}", "section-statistics", item.title,
                    f"{item.word_count} words · {item.citation_count} citation(s) · {item.source_note_count} note(s)",
                    item,
                ))
            return "Statistics by section", tuple(rows)
        return "Overview", ()

    @staticmethod
    def _category_summary(snapshot: DocumentDossierSnapshot, category: str):
        stats = snapshot.statistics
        counts = snapshot.counts
        if category == "overview":
            body = (
                f"Path: {snapshot.identity.path or 'Untitled document'}\n"
                f"State: {'modified' if snapshot.identity.modified else 'saved'}\n\n"
                f"Words: {stats.words}\nCharacters: {stats.characters}\nSections: {counts.sections}\n"
                f"Citations: {counts.citations}\nSource Notes: {counts.source_notes}\n"
                f"References in context: {counts.references}\nRelated References: {counts.related_references}\n"
                f"Collected but unused: {counts.collected_unused_references}\n"
                f"Pertinent Reference Sets: {counts.relevant_reference_sets}\nIssues: {counts.issues}"
            )
            return snapshot.identity.name, body
        if category == "structure":
            return "Structure", f"{counts.sections} section(s), {counts.bookmarks} bookmark(s), {counts.links} internal link(s)."
        if category == "research":
            return "Research", (
                f"{counts.citations} citation key occurrence(s), {counts.source_notes} Source Note(s), "
                f"{counts.references} reference(s), {counts.relevant_reference_sets} pertinent set(s)."
            )
        if category == "integrity":
            return "Integrity", f"{stats.errors} error(s), {stats.warnings} warning(s), {stats.advisories} advisory item(s)."
        return "Statistics", (
            f"Words: {stats.words}\nCharacters: {stats.characters}\nCharacters without spaces: {stats.characters_no_spaces}\n"
            f"Paragraphs: {stats.paragraphs}\nLines: {stats.lines}\nEstimated reading time: {stats.reading_minutes} min\n"
            f"Sections without citations: {stats.sections_without_citations}\n"
            f"Sections without Source Notes: {stats.sections_without_source_notes}"
        )

    def _row_detail(self, row: DocumentOverviewRow):
        item = row.payload
        if row.kind in {"section", "section-statistics"}:
            body = (
                f"Line {item.line}\nHeading level: {item.level}\nWords: {item.word_count}\n"
                f"Citations: {item.citation_count}\nSource Notes: {item.source_note_count}\n"
                f"Bookmarks: {item.bookmark_count}\nIncoming links: {item.incoming_link_count}\n"
                f"Outgoing links: {item.outgoing_link_count}\n\n{item.excerpt or 'No excerpt.'}"
            )
            return item.title, body, "Go to Section", ""
        if row.kind == "bookmark":
            return row.title, f"Line {item.line}\nOffset {item.offset}\nSection: {item.section_id or 'none'}", "Go to Bookmark", ""
        if row.kind == "link":
            body = (
                f"Target: #{item.identifier}\nStatus: {item.status}\nSource line: {item.line}\n"
                f"Destination line: {item.destination_line or 'unavailable'}"
            )
            secondary = "Go to Destination" if item.status == "resolved" else ""
            return item.label, body, "Go to Link Source", secondary
        if row.kind == "citation":
            body = (
                f"Line {item.line}\nRequested: {', '.join(item.requested_keys) or 'none'}\n"
                f"Resolved: {', '.join(item.canonical_keys) or 'none'}\n"
                f"Missing: {', '.join(item.missing_keys) or 'none'}\n"
                f"Ambiguous: {', '.join(item.ambiguous_keys) or 'none'}"
            )
            secondary = "Show Reference" if item.canonical_keys else ""
            return item.raw, body, "Go to Citation", secondary
        if row.kind == "source-note":
            body = (
                f"Type: {item.kind}\nStatus: {item.status}\nReference: {item.reference_key or 'none'}\n"
                f"Locator: {item.locator or 'none'}\nTarget: {item.target or 'none'}\nSection: {item.section_id or 'none'}"
            )
            secondary = "Show Reference" if item.canonical_reference_key else ""
            return item.excerpt, body, "Open Source Note", secondary
        if row.kind == "reference":
            body = (
                f"Key: {item.key}\nStatus: {item.status}\nRoles: {', '.join(item.roles)}\n"
                f"Cited: {item.cited_count}\nSource Notes: {item.source_note_count}\n"
                f"Related from: {', '.join(item.related_from) or 'none'}\n"
                f"Reference Sets: {', '.join(item.reference_sets) or 'none'}"
            )
            return item.title or item.key, body, "Show Reference", ""
        if row.kind == "reference-set":
            body = (
                f"Description: {item.description or 'none'}\nMembers: {', '.join(item.members) or 'none'}\n"
                f"Relevant members: {', '.join(item.relevant_members) or 'none'}\n"
                f"Missing members: {', '.join(item.missing_members) or 'none'}"
            )
            return item.name, body, "Open Reference Set", ""
        return row.title, f"Severity: {item.severity}\nKind: {item.kind}\nSubject: {item.subject}\n\n{item.message}", "Run Research Check", ""

    def _handoff_to_document(self, action: Callable[[], object]) -> bool:
        """Hide the transient tool window while a document navigation runs.

        On GTK/X11 window managers a non-modal transient may remain stacked
        above its parent even after the parent is presented and its TextView
        owns the internal focus.  Hiding the tool window before the semantic
        navigation makes the editor target observable without destroying the
        single Document Overview instance.  A failed navigation restores the
        tool window so the user is not left without feedback or controls.
        """
        view = self._view
        if view is not None:
            view.hide()
        try:
            succeeded = bool(action())
        except Exception:
            if view is self._view and view is not None:
                view.present()
            raise
        if not succeeded and view is self._view and view is not None:
            view.present()
        return succeeded

    def _dispatch(self, row: DocumentOverviewRow, *, secondary: bool):
        item = row.payload
        try:
            if row.kind in {"section", "section-statistics"}:
                return self._handoff_to_document(lambda: self._navigate_offset(item.start_offset))
            if row.kind == "bookmark":
                return self._handoff_to_document(lambda: self._navigate_offset(item.offset))
            if row.kind == "link":
                if secondary:
                    if item.status != "resolved" or self._snapshot is None:
                        return False
                    destination = self._snapshot.section(item.destination_section_id)
                    return self._handoff_to_document(
                        lambda: bool(destination and self._navigate_offset(destination.start_offset))
                    )
                return self._handoff_to_document(
                    lambda: self._select_range(item.start_offset, item.end_offset)
                )
            if row.kind == "citation":
                if secondary:
                    return bool(item.canonical_keys and self._show_reference(item.canonical_keys[0]))
                return self._handoff_to_document(
                    lambda: self._select_range(item.start_offset, item.end_offset)
                )
            if row.kind == "source-note":
                if secondary:
                    return bool(item.canonical_reference_key and self._show_reference(item.canonical_reference_key))
                return bool(self._show_source_note(item.id))
            if row.kind == "reference":
                return bool(self._show_reference(item.key))
            if row.kind == "reference-set":
                return bool(self._show_reference_set(item.name))
            if row.kind == "issue":
                return bool(self._run_research_check())
        except Exception as error:
            self._show_error(f"Document Overview action failed.\n\n{error}")
            return False
        return False
