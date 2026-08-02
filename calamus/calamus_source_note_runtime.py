"""UI coordinator for the document-specific Source Notes client."""
from __future__ import annotations

from typing import Callable

from calamus_document_structure import DocumentStructure
from calamus_source_note_controller import SourceNoteController
from calamus_source_note_dialogs import (
    confirm_source_note_delete,
    resolve_external_source_note_change,
    run_source_note_dialog,
)
from calamus_source_note_panel import build_source_note_panel_view
from calamus_source_notes import SourceNote, new_source_note_id, now_iso


class SourceNotePanelRuntime:
    def __init__(
        self,
        parent,
        *,
        document_path_provider: Callable[[], str | None],
        reference_keys_provider: Callable[[], tuple[str, ...]],
        document_structure_provider: Callable[[], DocumentStructure],
        show_reference: Callable[[str], bool],
        show_target: Callable[[str], bool],
        reference_key_resolver: Callable[[str], str | None] | None = None,
        store_factory=None,
        on_changed=None,
    ) -> None:
        if on_changed is not None and not callable(on_changed):
            raise TypeError("on_changed must be callable")
        if not all(callable(callback) for callback in (
            document_path_provider,
            reference_keys_provider,
            document_structure_provider,
            show_reference,
            show_target,
        )):
            raise TypeError("Source Notes callbacks must be callable")
        self._parent = parent
        self._document_path_provider = document_path_provider
        self._reference_keys_provider = reference_keys_provider
        self._document_structure_provider = document_structure_provider
        if reference_key_resolver is not None and not callable(reference_key_resolver):
            raise TypeError("reference_key_resolver must be callable")
        self._reference_key_resolver = reference_key_resolver
        self._show_reference = show_reference
        self._show_target = show_target
        self._on_changed = on_changed or (lambda: None)
        self._view = build_source_note_panel_view(
            self.on_add,
            self.on_edit,
            self.on_delete,
            self.on_open_reference,
            self.on_open_target,
        )
        controller_kwargs = {
            "reference_keys_provider": reference_keys_provider,
            "document_structure_provider": document_structure_provider,
            "reference_key_resolver": reference_key_resolver,
            "resolve_conflict": lambda: resolve_external_source_note_change(parent),
            "on_error": self._show_error,
        }
        if store_factory is not None:
            controller_kwargs["store_factory"] = store_factory
        self._controller = SourceNoteController(self._view, **controller_kwargs)
        self._view.bind_filters(
            lambda query: self._controller.refresh(query=query),
            lambda kind: self._controller.refresh(kind=kind),
            lambda key: self._controller.refresh(reference_key=key),
        )

    @property
    def widget(self):
        return self._view.widget

    @property
    def controller(self) -> SourceNoteController:
        return self._controller

    def activate(self) -> None:
        self.sync_document()
        self._view.focus_search()

    def sync_document(self, *, force: bool = False) -> bool:
        return self._controller.bind_document(
            self._document_path_provider(),
            force=force,
        )

    def refresh_for_invalidation(self, _reasons=frozenset()) -> bool:
        return self.sync_document(force=True)

    def shutdown(self) -> bool:
        return True

    def _changed(self, result: bool) -> bool:
        if result:
            getattr(self, "_on_changed", lambda: None)()
        return bool(result)

    def notes_snapshot(self, *, force: bool = False):
        self.sync_document(force=force)
        return self._controller.notes

    def on_add(self, *_):
        self.sync_document()
        if not self._controller.available:
            self._show_error("Save the document before creating Source Notes.")
            return False
        note = run_source_note_dialog(
            self._parent,
            self._reference_keys_provider(),
            self._controller.target_options,
            self._controller.ids,
        )
        return self._changed(bool(note is not None and self._controller.add(note)))

    def add_from_selection(
        self,
        text: str,
        *,
        reference_key: str = "",
        target: str = "",
    ) -> bool:
        self.sync_document()
        if not self._controller.available:
            self._show_error("Save the document before creating Source Notes.")
            return False
        if not isinstance(text, str) or not text.strip():
            self._show_error("Select document text before creating a Source Note.")
            return False
        canonical = self._controller.resolve_reference_key(reference_key) if reference_key else None
        if reference_key and canonical is None:
            self._show_error(f"Reference key is missing: {reference_key}")
            return False
        stamp = now_iso()
        try:
            draft = SourceNote(
                id=new_source_note_id(self._controller.ids),
                kind="quote" if canonical else "comment",
                text=text,
                reference_key=canonical or "",
                target=target,
                created=stamp,
                modified=stamp,
            )
        except ValueError as error:
            self._show_error(str(error))
            return False
        note = run_source_note_dialog(
            self._parent,
            self._reference_keys_provider(),
            self._controller.target_options,
            self._controller.ids,
            draft=draft,
        )
        return self._changed(bool(note is not None and self._controller.add(note)))

    def show_note(self, note_id: str) -> bool:
        self.sync_document(force=True)
        return self._controller.select_id(note_id)

    def on_edit(self, *_):
        self.sync_document()
        selected = self._controller.selected_note()
        if selected is None:
            return
        note = run_source_note_dialog(
            self._parent,
            self._reference_keys_provider(),
            self._controller.target_options,
            self._controller.ids,
            selected,
        )
        if note is not None:
            return self._changed(self._controller.update(selected.id, note))
        return False

    def on_delete(self, *_):
        self.sync_document()
        selected = self._controller.selected_note()
        if selected is not None and confirm_source_note_delete(self._parent, selected):
            return self._changed(self._controller.delete(selected.id))
        return False

    def on_open_reference(self, *_):
        self.sync_document()
        selected = self._controller.selected_note()
        if selected is None or not selected.reference_key:
            return False
        canonical = self._controller.resolve_reference_key(selected.reference_key)
        if canonical is None:
            self._show_error(f"Reference key is missing: {selected.reference_key}")
            return False
        return self._show_reference(canonical)

    def on_open_target(self, *_):
        self.sync_document()
        selected = self._controller.selected_note()
        if selected is None or not selected.target:
            return False
        state = self._controller.target_state(selected)
        if state == "missing":
            self._show_error(f"Heading target is missing: {selected.target}")
            return False
        if state == "ambiguous":
            self._show_error(f"Heading target is ambiguous: {selected.target}")
            return False
        return bool(self._show_target(selected.target))

    def _show_error(self, message: str) -> None:
        from gi.repository import Gtk

        dialog = Gtk.MessageDialog(
            transient_for=self._parent,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Source Notes",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
