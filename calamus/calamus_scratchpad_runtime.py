"""UI coordinator for the document-local Scratchpad client."""
from __future__ import annotations

from typing import Callable

from calamus_document_structure import DocumentStructure
from calamus_modal_dialog import destroy_modal, run_modal
from calamus_scratchpad import ScratchpadEntry, new_scratchpad_id, now_iso
from calamus_scratchpad_controller import ScratchpadController
from calamus_scratchpad_dialogs import (
    choose_scratchpad_section,
    confirm_scratchpad_delete,
    resolve_external_scratchpad_change,
    run_scratchpad_dialog,
)
from calamus_scratchpad_panel import build_scratchpad_panel_view


class ScratchpadRuntime:
    def __init__(
        self,
        parent,
        *,
        document_path_provider: Callable[[], str | None],
        document_structure_provider: Callable[[], DocumentStructure],
        current_section_provider: Callable[[], str | None],
        selected_text_provider: Callable[[], str],
        show_target: Callable[[str], bool],
        insert_body: Callable[[str], bool],
        copy_body: Callable[[str], bool],
        store_factory=None,
    ) -> None:
        callbacks = (
            document_path_provider,
            document_structure_provider,
            current_section_provider,
            selected_text_provider,
            show_target,
            insert_body,
            copy_body,
        )
        if not all(callable(callback) for callback in callbacks):
            raise TypeError("Scratchpad callbacks must be callable")
        self._parent = parent
        self._document_path_provider = document_path_provider
        self._document_structure_provider = document_structure_provider
        self._current_section_provider = current_section_provider
        self._selected_text_provider = selected_text_provider
        self._show_target = show_target
        self._insert_body = insert_body
        self._copy_body = copy_body
        self._view = build_scratchpad_panel_view(
            self.on_add,
            self.on_edit,
            self.on_archive,
            self.on_delete,
            self.on_open_section,
            self.on_insert,
            self.on_copy,
            self.on_clear_section_filter,
            self.on_refresh,
        )
        kwargs = {
            "document_structure_provider": document_structure_provider,
            "resolve_conflict": lambda: resolve_external_scratchpad_change(parent),
            "on_error": self._show_error,
        }
        if store_factory is not None:
            kwargs["store_factory"] = store_factory
        self._controller = ScratchpadController(self._view, **kwargs)
        self._view.bind_filters(
            lambda query: self._controller.refresh(query=query),
            lambda entry_type: self._controller.refresh(entry_type=entry_type),
            lambda status: self._controller.refresh(status=status),
            lambda tag: self._controller.refresh(tag=tag),
        )

    @property
    def widget(self):
        return self._view.widget

    @property
    def controller(self) -> ScratchpadController:
        return self._controller

    def activate(self) -> None:
        self.sync_document()
        self._view.focus_search()

    def sync_document(self, *, force: bool = False) -> bool:
        return self._controller.bind_document(self._document_path_provider(), force=force)

    def entries_snapshot(self, *, force: bool = False):
        self.sync_document(force=force)
        return self._controller.entries

    def show_entry(self, entry_id: str) -> bool:
        """Reload the current sidecar and reveal one explicit Scratchpad entry."""
        self.sync_document(force=True)
        selected = self._controller.select_id(entry_id)
        if selected:
            self._view.focus_search()
        return selected

    def on_add(self, *_):
        return self.new_entry()

    def new_entry(self, *, sections: tuple[str, ...] = (), body: str = "", title: str = "", entry_type: str = "note") -> bool:
        self.sync_document()
        if not self._controller.available:
            self._show_error("Save the document before using Scratchpad.")
            return False
        stamp = now_iso()
        draft = ScratchpadEntry(
            id=new_scratchpad_id(self._controller.ids),
            type=entry_type,
            title=title or self._title_from_body(body) or "New Scratchpad Entry",
            status="inbox",
            tags=(),
            sections=sections,
            created=stamp,
            updated=stamp,
            body=body,
        )
        result = run_scratchpad_dialog(
            self._parent,
            self._controller.target_options,
            self._controller.ids,
            draft=draft,
        )
        return bool(result is not None and self._controller.add(result))

    def capture_selection(self) -> bool:
        text = self._selected_text_provider()
        if not isinstance(text, str) or not text.strip():
            self._show_error("Select document text before capturing it in Scratchpad.")
            return False
        current = self._current_section_provider()
        sections = (current,) if current else ()
        return self.new_entry(
            sections=sections,
            body=text,
            title=self._title_from_body(text),
            entry_type="note",
        )

    def new_for_current_section(self) -> bool:
        current = self._current_section_provider()
        if not current:
            self._show_error("The current section needs a unique explicit {#heading-id}.")
            return False
        return self.new_entry(sections=(current,))

    def show_for_current_section(self) -> bool:
        self.sync_document()
        current = self._current_section_provider()
        if not current:
            self._show_error("The current section needs a unique explicit {#heading-id}.")
            return False
        self._controller.show_for_section(current)
        return True

    def on_clear_section_filter(self, *_):
        self._controller.clear_section_filter()

    def on_refresh(self, *_):
        return self.sync_document(force=True)

    def on_edit(self, *_):
        self.sync_document()
        selected = self._controller.selected_entry()
        if selected is None:
            return False
        result = run_scratchpad_dialog(
            self._parent,
            self._controller.target_options,
            self._controller.ids,
            selected,
        )
        return bool(result is not None and self._controller.update(selected.id, result))

    def on_archive(self, *_):
        self.sync_document()
        selected = self._controller.selected_entry()
        if selected is None:
            return False
        revised = selected.revised(
            updated=now_iso(),
            status="active" if selected.status == "archived" else "archived",
        )
        return self._controller.update(selected.id, revised)

    def on_delete(self, *_):
        self.sync_document()
        selected = self._controller.selected_entry()
        if selected is None:
            return False
        return bool(
            confirm_scratchpad_delete(self._parent, selected)
            and self._controller.delete(selected.id)
        )

    def on_open_section(self, *_):
        self.sync_document()
        selected = self._controller.selected_entry()
        if selected is None or not selected.sections:
            return False
        target = choose_scratchpad_section(self._parent, selected.sections)
        if not target:
            return False
        state = self._controller.target_state(target)
        if state == "missing":
            self._show_error(f"Heading target is missing: {target}")
            return False
        if state == "ambiguous":
            self._show_error(f"Heading target is ambiguous: {target}")
            return False
        return bool(self._show_target(target))

    def on_insert(self, *_):
        self.sync_document()
        selected = self._controller.selected_entry()
        if selected is None or not selected.body:
            return False
        return bool(self._insert_body(selected.body))

    def on_copy(self, *_):
        self.sync_document()
        selected = self._controller.selected_entry()
        if selected is None:
            return False
        return bool(self._copy_body(selected.body))

    @staticmethod
    def _title_from_body(body: str) -> str:
        compact = " ".join(body.split()) if isinstance(body, str) else ""
        if not compact:
            return ""
        return compact if len(compact) <= 70 else compact[:67].rstrip() + "…"

    def _show_error(self, message: str) -> None:
        from gi.repository import Gtk
        dialog = Gtk.MessageDialog(
            transient_for=self._parent,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Scratchpad",
        )
        dialog.format_secondary_text(message)
        dialog.show_all()
        run_modal(dialog)
        destroy_modal(dialog)
