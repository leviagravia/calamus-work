"""UI coordinator for the References client, kept outside App."""
from __future__ import annotations

from calamus_reference_controller import ReferenceController
from calamus_reference_dialogs import (
    confirm_reference_delete,
    resolve_external_reference_change,
    run_reference_dialog,
)
from calamus_reference_panel import build_reference_panel_view
from calamus_reference_store import MarkdownReferenceStore


class ReferencePanelRuntime:
    def __init__(self, parent, *, store=None, quick_cite=None) -> None:
        self._parent = parent
        if quick_cite is not None and not callable(quick_cite):
            raise TypeError("quick_cite must be callable")
        self._quick_cite = quick_cite
        self._view = build_reference_panel_view(
            self.on_add,
            self.on_edit,
            self.on_delete,
            self.on_copy_key,
            self.on_quick_cite,
        )
        self._controller = ReferenceController(
            store or MarkdownReferenceStore(),
            self._view,
            resolve_conflict=lambda: resolve_external_reference_change(parent),
            on_error=self._show_error,
        )
        self._view.bind_search(self._controller.refresh)

    @property
    def widget(self):
        return self._view.widget

    @property
    def controller(self) -> ReferenceController:
        return self._controller

    @property
    def records(self):
        self._controller.ensure_loaded()
        return self._controller.records

    @property
    def keys(self) -> tuple[str, ...]:
        self._controller.ensure_loaded()
        return self._controller.keys

    def activate(self) -> None:
        self._controller.ensure_loaded()
        self._view.focus_search()

    def show_key(self, key: str) -> bool:
        self._controller.ensure_loaded()
        selected = self._controller.select_key(key)
        if selected:
            self._view.focus_search()
        return selected

    def on_add(self, *_):
        self._controller.ensure_loaded()
        record = run_reference_dialog(self._parent, self._controller.keys)
        if record is not None:
            self._controller.add(record)

    def on_edit(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is None:
            return
        record = run_reference_dialog(self._parent, self._controller.keys, selected)
        if record is not None:
            self._controller.update(selected.key, record)

    def on_delete(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is not None and confirm_reference_delete(self._parent, selected):
            self._controller.delete(selected.key)

    def on_quick_cite(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is not None and self._quick_cite is not None:
            return self._quick_cite(selected.key)
        return False

    def on_copy_key(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is None:
            return
        from gi.repository import Gdk, Gtk
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(selected.key, -1)
        clipboard.store()

    def _show_error(self, message: str) -> None:
        from gi.repository import Gtk
        dialog = Gtk.MessageDialog(
            transient_for=self._parent,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="References",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
