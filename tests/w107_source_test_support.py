"""Source-level authority helpers for historical contracts under W107.

Historical tests keep their semantic invariant while following the W107 owner
instead of requiring implementation to remain physically in ``App``.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_RESEARCH = {
    "refresh_clip_list", "on_research_item_toggled", "on_research_visibility_changed",
    "toggle_research_panel", "show_clip_collection", "show_scratchpad",
    "on_capture_selection_in_scratchpad", "on_new_scratchpad_for_current_section",
    "on_show_scratchpad_for_current_section", "show_references",
    "on_open_bibliography_file", "on_export_bibliography_markdown",
    "on_export_bibliography_text", "show_tags", "show_source_notes",
    "show_reference_sets", "show_authoring_bridge", "source_notes_snapshot",
    "current_heading_identifier", "authoring_selection_snapshot",
    "navigate_authoring_occurrence", "show_source_note_id", "show_scratchpad_entry_id",
    "create_source_note_from_authoring_snapshot", "on_create_source_note_from_selection",
    "on_insert_link_to_heading", "apply_heading_link_plan", "show_reference_key",
    "insert_citation_text", "run_quick_cite", "on_quick_cite", "quick_cite_key",
    "on_open_citation_in_references", "replace_document_for_reference_migration",
    "on_rename_reference_key", "on_research_check", "on_tag_integrity",
    "on_import_bibtex_biblatex", "on_export_references_bibtex_biblatex",
    "on_export_research_apparatus", "on_export_with_pandoc", "show_heading_target",
    "finish_research_mutation", "publish_research_invalidation",
    "research_document_context_changed", "sync_source_notes_document",
    "current_section_target", "selected_text", "insert_scratchpad_body",
    "copy_scratchpad_body", "toggle_clip_collection", "insert_clip_number",
    "on_insert_clip", "on_clip_add_selection", "on_clip_insert", "on_clip_delete",
}
_WORKSPACE = {
    "populate_recent_workspaces_menu", "show_workspace_panel", "on_new_workspace_text_file",
    "create_workspace_text_file", "on_new_workspace_folder", "create_workspace_folder",
    "on_duplicate_workspace_file", "on_move_workspace_item_to_trash", "confirm_workspace_trash",
    "on_rename_workspace_item", "rename_workspace_item", "capture_workspace_path_references",
    "reconcile_workspace_rename", "reconcile_workspace_trash", "on_select_workspace_folder",
    "open_workspace_path", "activate_workspace_path", "on_close_workspace",
    "on_refresh_workspace", "on_reveal_workspace", "on_workspace_item_toggled",
    "toggle_workspace_panel", "on_workspace_root_changed", "on_workspace_visibility_changed",
}
_SEARCH = {
    "on_find_replace", "on_find_all", "on_find_next", "on_find_previous",
    "search_matches", "highlight_all_search", "find_text", "find_text_previous",
    "replace_current_match", "replace_all_literal",
}
_PRINT = {"on_print_preview", "on_print", "on_begin_print", "on_draw_page"}
_SPELL = {
    "on_lang", "clear_spell_tags", "hunspell_dict", "hunspell_base_command",
    "hunspell_misspelled_words", "hunspell_suggestions", "find_next_error",
    "select_range", "spelling_dialog", "replace_buffer_range", "replace_all_word", "on_check",
}


def _method(relative: str, class_name: str, name: str) -> str:
    text = (ROOT / relative).read_text(encoding="utf-8")
    tree = ast.parse(text)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    node = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)
    return ast.get_source_segment(text, node) or ""


def authoritative_method_source(name: str) -> str:
    if name in _RESEARCH:
        return _method("calamus/calamus_research_application.py", "ResearchApplicationRuntime", name)
    if name in _WORKSPACE:
        return _method("calamus/calamus_workspace_host_runtime.py", "WorkspaceHostRuntime", name)
    if name in _SEARCH:
        return _method("calamus/calamus_search_runtime.py", "SearchApplicationRuntime", name)
    if name in _PRINT:
        return _method("calamus/calamus_print_runtime.py", "PrintRuntime", name)
    if name in _SPELL:
        return _method("calamus/calamus_spellcheck_runtime.py", "SpellcheckApplicationRuntime", name)
    return _method("bin/calamus", "App", name)


def app_method_source(name: str) -> str:
    return _method("bin/calamus", "App", name)


def research_composition_source() -> str:
    return (ROOT / "calamus/calamus_research_composition.py").read_text(encoding="utf-8")


def workspace_host_source() -> str:
    return (ROOT / "calamus/calamus_workspace_host_runtime.py").read_text(encoding="utf-8")
