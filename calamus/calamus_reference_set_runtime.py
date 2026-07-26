"""Thin GTK runtime for transparent static Reference Sets."""
from __future__ import annotations

from calamus_reference_set_controller import ReferenceSetController
from calamus_reference_set_dialogs import (
    confirm_reference_set_delete,
    resolve_external_reference_set_change,
    run_reference_set_dialog,
)
from calamus_reference_set_store import MarkdownReferenceSetStore
from calamus_reference_set_view import build_reference_set_view

from calamus_modal_dialog import destroy_modal, run_modal


def _gtk():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    return Gtk

class ReferenceSetRuntime:
    def __init__(
        self,
        parent,
        *,
        records_provider,
        show_reference,
        store=None,
    ) -> None:
        if not callable(records_provider) or not callable(show_reference):
            raise TypeError("Reference Set runtime callbacks must be callable")
        self._parent = parent
        self._records_provider = records_provider
        self._show_reference = show_reference
        self._view = build_reference_set_view(
            self.on_add,
            self.on_edit,
            self.on_delete,
            self.on_open,
        )
        self._controller = ReferenceSetController(
            store or MarkdownReferenceSetStore(),
            self._view,
            records_provider=records_provider,
            resolve_conflict=lambda: resolve_external_reference_set_change(parent),
            on_error=self._show_error,
        )
        self._view.bind_search(self._controller.refresh)
        self._view.bind_set_changed(self._controller.refresh)

    @property
    def widget(self):
        return self._view.widget

    @property
    def controller(self) -> ReferenceSetController:
        return self._controller

    @property
    def sets(self):
        self._controller.ensure_loaded()
        return self._controller.sets

    def sets_snapshot(self, *, force: bool = False):
        selected = self._controller.selected_set()
        selected_name = selected.name if selected else None
        if force:
            self._controller.load()
            if selected_name:
                self._controller.select_set(selected_name)
        return self.sets

    def reload(self) -> None:
        self._controller.load()

    def activate(self) -> None:
        self._controller.ensure_loaded()
        self._controller.refresh()
        self._view.focus_search()

    def on_add(self, *_):
        self._controller.ensure_loaded()
        item = run_reference_set_dialog(
            self._parent,
            self._controller.records,
            self._controller.names,
        )
        return self._controller.add(item) if item is not None else False

    def on_edit(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_set()
        if selected is None:
            return False
        item = run_reference_set_dialog(
            self._parent,
            self._controller.records,
            self._controller.names,
            selected,
        )
        return self._controller.update(selected.name, item) if item is not None else False

    def on_delete(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_set()
        if selected is None or not confirm_reference_set_delete(self._parent, selected):
            return False
        return self._controller.delete(selected.name)

    def on_open(self, *_):
        self._controller.ensure_loaded()
        key = self._controller.selected_member_key()
        return bool(key and self._show_reference(key))

    def _show_error(self, message: str) -> None:
        Gtk = _gtk()
        dialog = Gtk.MessageDialog(
            transient_for=self._parent,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Reference Sets",
        )
        dialog.format_secondary_text(message)
        run_modal(dialog)
        destroy_modal(dialog)
