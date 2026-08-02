"""UI coordinator for the W97 Bibliography Manager client, kept outside App."""
from __future__ import annotations

import os

from calamus_bibliography import (
    available_tags,
    available_types,
    build_bibliography_context,
    build_delete_impact,
    duplicate_reference,
    render_markdown_bibliography,
    render_plain_bibliography,
)
from calamus_reference_controller import ReferenceController
from calamus_reference_dialogs import (
    choose_bibliography_export_path,
    confirm_reference_delete,
    resolve_external_reference_change,
    run_reference_dialog,
    show_reference_uses,
)
from calamus_reference_panel import build_reference_panel_view
from calamus_reference_store import MarkdownReferenceStore
from calamus_research_file import atomic_write_utf8
from calamus_related_reference_dialogs import run_related_references_dialog
from calamus_workspace_external import open_external_path, reveal_in_file_manager
from calamus_modal_dialog import destroy_modal, run_modal


def _gtk_gdk():
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk
    return Gdk, Gtk


def _gtk():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    return Gtk


class ReferencePanelRuntime:
    def __init__(
        self,
        parent,
        *,
        store=None,
        quick_cite=None,
        document_text_provider=None,
        source_notes_provider=None,
        reference_sets_provider=None,
        open_external=None,
        reveal_external=None,
    ) -> None:
        self._parent = parent
        for name, callback in (
            ("quick_cite", quick_cite),
            ("document_text_provider", document_text_provider),
            ("source_notes_provider", source_notes_provider),
            ("reference_sets_provider", reference_sets_provider),
            ("open_external", open_external),
            ("reveal_external", reveal_external),
        ):
            if callback is not None and not callable(callback):
                raise TypeError(f"{name} must be callable")
        self._quick_cite = quick_cite
        self._document_text_provider = document_text_provider or (lambda: "")
        self._source_notes_provider = source_notes_provider or (lambda: ())
        self._reference_sets_provider = reference_sets_provider or (lambda: ())
        self._open_external = open_external or open_external_path
        self._reveal_external = reveal_external or reveal_in_file_manager
        self._store = store or MarkdownReferenceStore()
        self._view = build_reference_panel_view(
            self.on_add,
            self.on_edit,
            self.on_duplicate,
            self.on_delete,
            self.on_copy_key,
            self.on_quick_cite,
            self.on_show_uses,
            self.on_open_file,
            self.on_reveal_file,
            self.on_related_references,
            self.on_refresh,
        )
        self._controller = ReferenceController(
            self._store,
            self._view,
            resolve_conflict=lambda: resolve_external_reference_change(parent),
            on_error=self._show_error,
        )
        self._view.bind_search(lambda query: self._controller.set_filters(query=query))
        for name in ("reference_type", "tag", "use", "file", "integrity", "sort"):
            self._view.bind_filter(name, lambda value, name=name: self._controller.set_filters(**{name: value}))
        self._view.bind_selection(self._controller.sync_selection_from_view)

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

    @property
    def selected_key(self) -> str | None:
        self._controller.ensure_loaded()
        return self._controller.selected_key

    @property
    def bibliography_path(self) -> str:
        return self._store.path

    def _context_inputs(self):
        try:
            text = self._document_text_provider()
        except Exception:
            text = ""
        try:
            notes = tuple(self._source_notes_provider())
        except Exception:
            notes = ()
        try:
            sets = tuple(self._reference_sets_provider())
        except Exception:
            sets = ()
        return text if isinstance(text, str) else "", notes, sets

    def _refresh_context(self) -> None:
        self._controller.ensure_loaded()
        text, notes, sets = self._context_inputs()
        self._controller.set_context(build_bibliography_context(
            self._controller.records,
            document_text=text,
            source_notes=notes,
            reference_sets=sets,
        ))
        self._view.set_filter_options(
            available_types(self._controller.records),
            available_tags(self._controller.records),
        )

    def records_snapshot(self, *, force: bool = False):
        selected = self.selected_key
        if force:
            self._controller.load()
            self._refresh_context()
            if selected:
                self._controller.select_key(selected)
        return self.records

    def resolve_key(self, key: str) -> str | None:
        self._controller.ensure_loaded()
        return self._controller.resolve_key(key)

    def reload(self) -> None:
        self._controller.load()
        self._refresh_context()

    def activate(self) -> None:
        self._controller.ensure_loaded()
        self._refresh_context()
        self._view.focus_search()

    def show_key(self, key: str) -> bool:
        self._controller.ensure_loaded()
        self._refresh_context()
        if hasattr(self._view, "clear_search"):
            self._view.clear_search()
        selected = self._controller.select_key(key)
        if selected:
            self._controller.refresh_detail()
        return selected

    def on_refresh(self, *_):
        self.reload()
        return True

    def on_add(self, *_):
        self._controller.ensure_loaded()
        record = run_reference_dialog(self._parent, self._controller.identity_keys)
        if record is not None and self._controller.add(record):
            self._refresh_context()
            return True
        return False

    def on_edit(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is None:
            return False
        record = run_reference_dialog(self._parent, self._controller.identity_keys, selected)
        if record is not None and self._controller.update(selected.key, record):
            self._refresh_context()
            return True
        return False

    def on_duplicate(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is None:
            return False
        draft = duplicate_reference(selected, self._controller.identity_keys)
        record = run_reference_dialog(
            self._parent,
            self._controller.identity_keys,
            draft,
            allow_key_edit=True,
            title="Duplicate Reference",
        )
        if record is not None and self._controller.add(record):
            self._refresh_context()
            return True
        return False

    def _selected_impact(self):
        selected = self._controller.selected_record()
        if selected is None:
            return None, None
        text, notes, sets = self._context_inputs()
        return selected, build_delete_impact(
            self._controller.records,
            selected.key,
            document_text=text,
            source_notes=notes,
            reference_sets=sets,
        )

    def on_delete(self, *_):
        self._controller.ensure_loaded()
        selected, impact = self._selected_impact()
        if selected is None or impact is None:
            return False
        if confirm_reference_delete(self._parent, selected, impact) and self._controller.delete(selected.key):
            self._refresh_context()
            return True
        return False

    def on_show_uses(self, *_):
        self._controller.ensure_loaded()
        selected, impact = self._selected_impact()
        if selected is None or impact is None:
            return False
        show_reference_uses(self._parent, selected, impact)
        return True

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
            return False
        Gdk, Gtk = _gtk_gdk()
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(selected.key, -1)
        clipboard.store()
        return True

    def on_open_file(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is None or not selected.file_path or not self._open_external(os.path.expanduser(selected.file_path)):
            self._show_error("The selected Reference has no available local file.")
            return False
        return True

    def on_reveal_file(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is None or not selected.file_path or not self._reveal_external(os.path.expanduser(selected.file_path)):
            self._show_error("The selected Reference has no available local file to reveal.")
            return False
        return True

    def on_related_references(self, *_):
        self._controller.ensure_loaded()
        selected = self._controller.selected_record()
        if selected is None:
            return False
        plan = run_related_references_dialog(self._parent, self._controller.records, selected.key)
        if plan is None:
            return False
        changed = self._controller.replace_records(plan.records_after, select_key=selected.key)
        if changed:
            self._refresh_context()
        return changed

    def open_bibliography_file(self) -> bool:
        return bool(self._open_external(self.bibliography_path))

    def export_visible_bibliography(self, *, markdown: bool) -> bool:
        """Export the current deterministic search/filter projection."""
        self._controller.ensure_loaded()
        self._refresh_context()
        records = self._controller.filtered_records()
        if not records:
            self._show_error("The current Bibliography view contains no references to export.")
            return False
        path = choose_bibliography_export_path(self._parent, markdown=markdown)
        if not path:
            return False
        text = render_markdown_bibliography(records) if markdown else render_plain_bibliography(records)
        try:
            atomic_write_utf8(path, text)
        except (OSError, TypeError, ValueError) as error:
            self._show_error(f"Could not export the bibliography: {error}")
            return False
        return True

    def _show_error(self, message: str) -> None:
        Gtk = _gtk()
        dialog = Gtk.MessageDialog(
            transient_for=self._parent,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Bibliography",
        )
        dialog.format_secondary_text(message)
        run_modal(dialog)
        destroy_modal(dialog)
