"""W107 composition for Search, Spellcheck and Print subsystem hosts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from calamus_dialogs import run_spelling_dialog
from calamus_print_runtime import PrintRuntime
from calamus_search_dialogs import run_find_all_dialog, run_find_replace_dialog
from calamus_search_runtime import SearchApplicationRuntime, SearchRuntimePorts
from calamus_spellcheck_runtime import SpellcheckApplicationRuntime, SpellcheckRuntimePorts


@dataclass(frozen=True)
class SubsystemHostCompositionInput:
    dialog_parent: Any
    text_view: Any
    misspelling_tag: Any
    search_controller: Any
    editor_transaction: Any
    editor_buffer_adapter: Any
    document_text: Callable[[], str]
    language_provider: Callable[[], str]
    update_language: Callable[[str], Any]
    show_info: Callable[[str], Any]
    show_error: Callable[[str], Any]
    update_title: Callable[[], Any]
    project_committed_change: Callable[[str], Any]
    font_provider: Callable[[], tuple[str, int]]

    def __post_init__(self) -> None:
        for name in (
            "document_text", "language_provider", "update_language", "show_info",
            "show_error", "update_title", "project_committed_change", "font_provider",
        ):
            if not callable(getattr(self, name)):
                raise TypeError(f"{name} must be callable")


@dataclass(frozen=True)
class SubsystemHostComponents:
    search: SearchApplicationRuntime
    spellcheck: SpellcheckApplicationRuntime
    printer: PrintRuntime


def _decode_spelling_response(response) -> str:
    # Gtk.ResponseType.CANCEL is -6 in GTK3.  The spelling dialog's custom
    # response IDs are deliberately stable and historical.
    value = int(response)
    if value == -6:
        return "cancel"
    return {
        10: "ignore",
        11: "ignore-all",
        20: "replace",
        21: "replace-all",
    }.get(value, f"unknown:{value}")


def build_subsystem_host_components(inputs: SubsystemHostCompositionInput) -> SubsystemHostComponents:
    if not isinstance(inputs, SubsystemHostCompositionInput):
        raise TypeError("inputs must be SubsystemHostCompositionInput")

    search = SearchApplicationRuntime(
        inputs.search_controller,
        inputs.editor_transaction,
        inputs.editor_buffer_adapter,
        SearchRuntimePorts(
            open_find_replace=lambda replace_current, replace_all: run_find_replace_dialog(
                inputs.dialog_parent,
                inputs.search_controller,
                replace_current,
                replace_all,
            ),
            open_find_all=lambda: run_find_all_dialog(inputs.dialog_parent, inputs.search_controller),
            show_info=inputs.show_info,
            project_committed_change=inputs.project_committed_change,
        ),
    )

    def clear_spell_tags():
        buffer = inputs.text_view.get_buffer()
        start, end = buffer.get_bounds()
        buffer.remove_tag(inputs.misspelling_tag, start, end)

    def select_spell_range(start, end):
        buffer = inputs.text_view.get_buffer()
        it1 = buffer.get_iter_at_offset(start)
        it2 = buffer.get_iter_at_offset(end)
        buffer.select_range(it1, it2)
        inputs.text_view.scroll_to_iter(it1, 0.15, False, 0, 0)

    spellcheck = SpellcheckApplicationRuntime(
        inputs.editor_transaction,
        inputs.editor_buffer_adapter,
        SpellcheckRuntimePorts(
            language_provider=inputs.language_provider,
            update_language=inputs.update_language,
            spelling_dialog=lambda word, suggestions: run_spelling_dialog(
                inputs.dialog_parent, word, suggestions
            ),
            decode_response=_decode_spelling_response,
            show_info=inputs.show_info,
            show_error=inputs.show_error,
            clear_spell_tags=clear_spell_tags,
            select_range=select_spell_range,
            update_title=inputs.update_title,
            project_committed_change=inputs.project_committed_change,
        ),
    )

    printer = PrintRuntime(
        inputs.dialog_parent,
        document_text_provider=inputs.document_text,
        font_provider=inputs.font_provider,
        show_error=inputs.show_error,
    )
    return SubsystemHostComponents(search=search, spellcheck=spellcheck, printer=printer)
