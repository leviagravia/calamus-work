"""Application-bound W104 command execution adapters.

This is the explicit composition boundary where stable GTK-free command IDs are
bound to existing application callbacks.  The command core never receives App.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Mapping

from calamus_command_catalog import build_command_registry
from calamus_command_context import CommandContext, CommandInputError
from calamus_command_layer import CommandLayer


@dataclass(frozen=True)
class ApplicationCommandTarget:
    command_id: str
    payload: tuple[tuple[str, object], ...] = ()

    def data(self):
        return dict(self.payload)


@dataclass(frozen=True)
class EditCommandPorts:
    on_copy: Callable[..., object]
    on_cut: Callable[..., object]
    on_duplicate_line_or_selection: Callable[..., object]
    on_find_all: Callable[..., object]
    on_find_next: Callable[..., object]
    on_find_previous: Callable[..., object]
    on_find_replace: Callable[..., object]
    on_lowercase: Callable[..., object]
    on_paste: Callable[..., object]
    on_paste_clean_pdf: Callable[..., object]
    on_paste_plain_text: Callable[..., object]
    on_redo: Callable[..., object]
    on_replace_all_dialog: Callable[..., object]
    on_select_all: Callable[..., object]
    on_undo: Callable[..., object]
    on_uppercase: Callable[..., object]
    on_move_line: Callable[..., object]

@dataclass(frozen=True)
class FileCommandPorts:
    on_add_favourite: Callable[..., object]
    on_edit_favourites: Callable[..., object]
    on_reload_favourites: Callable[..., object]
    on_new: Callable[..., object]
    on_open: Callable[..., object]
    on_print: Callable[..., object]
    on_print_preview: Callable[..., object]
    on_quit: Callable[..., object]
    on_save: Callable[..., object]
    on_save_as: Callable[..., object]
    on_manage_templates: Callable[..., object]
    on_save_as_template: Callable[..., object]
    on_close_workspace: Callable[..., object]
    on_duplicate_workspace_file: Callable[..., object]
    on_new_workspace_folder: Callable[..., object]
    on_new_workspace_text_file: Callable[..., object]
    on_refresh_workspace: Callable[..., object]
    on_rename_workspace_item: Callable[..., object]
    on_reveal_workspace: Callable[..., object]
    on_select_workspace_folder: Callable[..., object]
    show_workspace_panel: Callable[..., object]
    on_move_workspace_item_to_trash: Callable[..., object]
    on_new_from_template: Callable[..., object]
    open_recent_path: Callable[..., object]
    open_favourite_path: Callable[..., object]
    activate_workspace_path: Callable[..., object]
    open_path: Callable[..., object]
    may_continue: Callable[..., object]
    on_clear_recent: Callable[..., object]

@dataclass(frozen=True)
class HelpCommandPorts:
    on_about: Callable[..., object]
    on_keyboard_shortcuts: Callable[..., object]
    on_user_guide: Callable[..., object]

@dataclass(frozen=True)
class NavigateCommandPorts:
    on_manage_bookmarks: Callable[..., object]
    next_bookmark: Callable[..., object]
    previous_bookmark: Callable[..., object]
    toggle_bookmark: Callable[..., object]
    on_document_overview: Callable[..., object]
    on_go_to_line: Callable[..., object]
    on_go_to_section: Callable[..., object]
    on_next_heading: Callable[..., object]
    on_previous_heading: Callable[..., object]
    on_navigator_item_toggled: Callable[..., object]
    toggle_navigator_panel: Callable[..., object]
    on_workspace_item_toggled: Callable[..., object]
    toggle_workspace_panel: Callable[..., object]

@dataclass(frozen=True)
class OptionsCommandPorts:
    on_font: Callable[..., object]
    on_opacity_selection: Callable[..., object]
    change_font: Callable[..., object]
    set_opacity_value: Callable[..., object]
    on_word_wrap: Callable[..., object]
    toggle_word_wrap: Callable[..., object]
    on_transparent_mode: Callable[..., object]
    toggle_transparent_mode: Callable[..., object]
    on_top: Callable[..., object]
    toggle_always_on_top: Callable[..., object]
    on_line_numbers: Callable[..., object]
    toggle_line_numbers: Callable[..., object]
    on_white_background: Callable[..., object]
    on_dark_mode: Callable[..., object]

@dataclass(frozen=True)
class ResearchCommandPorts:
    show_authoring_bridge: Callable[..., object]
    show_references: Callable[..., object]
    on_capture_selection_in_scratchpad: Callable[..., object]
    on_research_check: Callable[..., object]
    show_clip_collection: Callable[..., object]
    on_create_source_note_from_selection: Callable[..., object]
    on_export_research_apparatus: Callable[..., object]
    on_export_references_bibtex_biblatex: Callable[..., object]
    on_export_bibliography_markdown: Callable[..., object]
    on_export_bibliography_text: Callable[..., object]
    on_export_with_pandoc: Callable[..., object]
    on_import_bibtex_biblatex: Callable[..., object]
    on_insert_clip: Callable[..., object]
    on_insert_link_to_heading: Callable[..., object]
    on_new_scratchpad_for_current_section: Callable[..., object]
    on_open_bibliography_file: Callable[..., object]
    on_open_citation_in_references: Callable[..., object]
    on_quick_cite: Callable[..., object]
    show_reference_sets: Callable[..., object]
    on_rename_reference_key: Callable[..., object]
    show_scratchpad: Callable[..., object]
    on_show_scratchpad_for_current_section: Callable[..., object]
    show_source_notes: Callable[..., object]
    on_tag_integrity: Callable[..., object]
    show_tags: Callable[..., object]
    insert_clip_number: Callable[..., object]
    on_research_item_toggled: Callable[..., object]
    toggle_research_panel: Callable[..., object]

@dataclass(frozen=True)
class ToolsCommandPorts:
    on_language_selection: Callable[..., object]
    on_check: Callable[..., object]
    on_system_info: Callable[..., object]

@dataclass(frozen=True)
class ViewCommandPorts:
    on_character_map: Callable[..., object]
    toggle_current_line_highlight: Callable[..., object]
    toggle_distraction_free: Callable[..., object]
    toggle_focus_mode: Callable[..., object]

@dataclass(frozen=True)
class WritingCommandPorts:
    on_clean_selected_pdf: Callable[..., object]
    on_insert_date: Callable[..., object]
    on_insert_datetime: Callable[..., object]
    on_insert_time: Callable[..., object]
    on_join_lines: Callable[..., object]
    on_reflow_paragraph: Callable[..., object]
    on_remove_extra_spaces: Callable[..., object]
    on_remove_trailing_spaces: Callable[..., object]
    on_sentence_case: Callable[..., object]
    on_smart_typography: Callable[..., object]
    on_document_statistics: Callable[..., object]
    on_title_case: Callable[..., object]
    on_sort_lines_descending: Callable[..., object]
    on_sort_lines_ascending: Callable[..., object]
    on_typewriter_item_toggled: Callable[..., object]
    toggle_typewriter_mode: Callable[..., object]

@dataclass(frozen=True)
class ApplicationCommandPorts:
    edit: EditCommandPorts
    file: FileCommandPorts
    help: HelpCommandPorts
    navigate: NavigateCommandPorts
    options: OptionsCommandPorts
    research: ResearchCommandPorts
    tools: ToolsCommandPorts
    view: ViewCommandPorts
    writing: WritingCommandPorts

class _ActiveValue:
    def __init__(self, active): self._active = bool(active)
    def get_active(self): return self._active


def _required(context, key, expected_type):
    value = context.get(key)
    if not isinstance(value, expected_type):
        raise CommandInputError(f"{key} must be {expected_type.__name__}")
    return value


def _int_in(context, key, allowed):
    value = context.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value not in allowed:
        raise CommandInputError(f"invalid {key}: {value!r}")
    return value

APPLICATION_METHOD_TARGETS = {
    'next_bookmark': ApplicationCommandTarget('navigate.bookmark.next', ()),
    'on_about': ApplicationCommandTarget('help.about', ()),
    'on_add_favourite': ApplicationCommandTarget('file.favourite.add', ()),
    'on_capture_selection_in_scratchpad': ApplicationCommandTarget('research.capture-scratchpad', ()),
    'on_character_map': ApplicationCommandTarget('view.character-map', ()),
    'on_clear_recent': ApplicationCommandTarget('file.recent.clear', ()),
    'on_check': ApplicationCommandTarget('tools.spellcheck', ()),
    'on_clean_selected_pdf': ApplicationCommandTarget('writing.clean-pdf', ()),
    'on_close_workspace': ApplicationCommandTarget('file.workspace.close', ()),
    'on_copy': ApplicationCommandTarget('edit.copy', ()),
    'on_create_source_note_from_selection': ApplicationCommandTarget('research.create-source-note', ()),
    'on_cut': ApplicationCommandTarget('edit.cut', ()),
    'on_document_overview': ApplicationCommandTarget('navigate.document-overview', ()),
    'on_document_statistics': ApplicationCommandTarget('writing.statistics', ()),
    'on_duplicate_line_or_selection': ApplicationCommandTarget('edit.duplicate-line-selection', ()),
    'on_duplicate_workspace_file': ApplicationCommandTarget('file.workspace.duplicate', ()),
    'on_edit_favourites': ApplicationCommandTarget('file.favourite.edit', ()),
    'on_export_bibliography_markdown': ApplicationCommandTarget('research.export-bibliography-markdown', ()),
    'on_export_bibliography_text': ApplicationCommandTarget('research.export-bibliography-text', ()),
    'on_export_references_bibtex_biblatex': ApplicationCommandTarget('research.export-bib', ()),
    'on_export_research_apparatus': ApplicationCommandTarget('research.export-apparatus', ()),
    'on_export_with_pandoc': ApplicationCommandTarget('research.export-pandoc', ()),
    'on_find_all': ApplicationCommandTarget('edit.find-all', ()),
    'on_find_next': ApplicationCommandTarget('edit.find-next', ()),
    'on_find_previous': ApplicationCommandTarget('edit.find-previous', ()),
    'on_find_replace': ApplicationCommandTarget('edit.find-replace', ()),
    'on_font': ApplicationCommandTarget('options.font', ()),
    'on_go_to_line': ApplicationCommandTarget('navigate.go-line', ()),
    'on_go_to_section': ApplicationCommandTarget('navigate.go-section', ()),
    'on_import_bibtex_biblatex': ApplicationCommandTarget('research.import-bib', ()),
    'on_insert_clip': ApplicationCommandTarget('research.insert-clip', ()),
    'on_insert_date': ApplicationCommandTarget('writing.insert-date', ()),
    'on_insert_datetime': ApplicationCommandTarget('writing.insert-date-time', ()),
    'on_insert_link_to_heading': ApplicationCommandTarget('research.insert-heading-link', ()),
    'on_insert_time': ApplicationCommandTarget('writing.insert-time', ()),
    'on_join_lines': ApplicationCommandTarget('writing.join-lines', ()),
    'on_keyboard_shortcuts': ApplicationCommandTarget('help.keyboard-shortcuts', ()),
    'on_language_selection': ApplicationCommandTarget('tools.language', ()),
    'on_lowercase': ApplicationCommandTarget('edit.lowercase', ()),
    'on_manage_bookmarks': ApplicationCommandTarget('navigate.bookmark.manage', ()),
    'on_manage_templates': ApplicationCommandTarget('file.template.manage', ()),
    'on_move_workspace_item_to_trash': ApplicationCommandTarget('file.workspace.trash', ()),
    'on_new': ApplicationCommandTarget('file.new', ()),
    'on_new_scratchpad_for_current_section': ApplicationCommandTarget('research.new-scratchpad-section', ()),
    'on_new_workspace_folder': ApplicationCommandTarget('file.workspace.new-folder', ()),
    'on_new_workspace_text_file': ApplicationCommandTarget('file.workspace.new-text-file', ()),
    'on_next_heading': ApplicationCommandTarget('navigate.heading.next', ()),
    'on_opacity_selection': ApplicationCommandTarget('options.opacity.select', ()),
    'on_open': ApplicationCommandTarget('file.open', ()),
    'on_open_bibliography_file': ApplicationCommandTarget('research.open-bibliography', ()),
    'on_open_citation_in_references': ApplicationCommandTarget('research.open-citation', ()),
    'on_paste': ApplicationCommandTarget('edit.paste', ()),
    'on_paste_clean_pdf': ApplicationCommandTarget('edit.paste-clean-pdf', ()),
    'on_paste_plain_text': ApplicationCommandTarget('edit.paste-plain', ()),
    'on_previous_heading': ApplicationCommandTarget('navigate.heading.previous', ()),
    'on_print': ApplicationCommandTarget('file.print', ()),
    'on_print_preview': ApplicationCommandTarget('file.print-preview', ()),
    'on_quick_cite': ApplicationCommandTarget('research.quick-cite', ()),
    'on_quit': ApplicationCommandTarget('file.quit', ()),
    'on_redo': ApplicationCommandTarget('edit.redo', ()),
    'on_reflow_paragraph': ApplicationCommandTarget('writing.reflow-paragraph', ()),
    'on_refresh_workspace': ApplicationCommandTarget('file.workspace.refresh', ()),
    'on_reload_favourites': ApplicationCommandTarget('file.favourite.reload', ()),
    'on_remove_extra_spaces': ApplicationCommandTarget('writing.remove-extra-spaces', ()),
    'on_remove_trailing_spaces': ApplicationCommandTarget('writing.remove-trailing-spaces', ()),
    'on_rename_reference_key': ApplicationCommandTarget('research.rename-reference-key', ()),
    'on_rename_workspace_item': ApplicationCommandTarget('file.workspace.rename', ()),
    'on_replace_all_dialog': ApplicationCommandTarget('edit.replace-all', ()),
    'on_research_check': ApplicationCommandTarget('research.check', ()),
    'on_reveal_workspace': ApplicationCommandTarget('file.workspace.reveal', ()),
    'on_save': ApplicationCommandTarget('file.save', ()),
    'on_save_as': ApplicationCommandTarget('file.save-as', ()),
    'on_save_as_template': ApplicationCommandTarget('file.template.save', ()),
    'on_select_all': ApplicationCommandTarget('edit.select-all', ()),
    'on_select_workspace_folder': ApplicationCommandTarget('file.workspace.select-folder', ()),
    'on_sentence_case': ApplicationCommandTarget('writing.sentence-case', ()),
    'on_show_scratchpad_for_current_section': ApplicationCommandTarget('research.show-scratchpad-section', ()),
    'on_smart_typography': ApplicationCommandTarget('writing.smart-typography', ()),
    'on_sort_lines_ascending': ApplicationCommandTarget('writing.sort-lines', (('reverse', False),)),
    'on_sort_lines_descending': ApplicationCommandTarget('writing.sort-lines', (('reverse', True),)),
    'on_system_info': ApplicationCommandTarget('tools.system-info', ()),
    'on_tag_integrity': ApplicationCommandTarget('research.tag-integrity', ()),
    'on_title_case': ApplicationCommandTarget('writing.title-case', ()),
    'on_undo': ApplicationCommandTarget('edit.undo', ()),
    'on_uppercase': ApplicationCommandTarget('edit.uppercase', ()),
    'on_user_guide': ApplicationCommandTarget('help.user-guide', ()),
    'previous_bookmark': ApplicationCommandTarget('navigate.bookmark.previous', ()),
    'show_authoring_bridge': ApplicationCommandTarget('research.authoring-bridge', ()),
    'show_clip_collection': ApplicationCommandTarget('research.clips', ()),
    'show_reference_sets': ApplicationCommandTarget('research.reference-sets', ()),
    'show_references': ApplicationCommandTarget('research.bibliography', ()),
    'show_scratchpad': ApplicationCommandTarget('research.scratchpad', ()),
    'show_source_notes': ApplicationCommandTarget('research.source-notes', ()),
    'show_tags': ApplicationCommandTarget('research.tags', ()),
    'show_workspace_panel': ApplicationCommandTarget('file.workspace.show-panel', ()),
    'toggle_always_on_top': ApplicationCommandTarget('options.always-on-top', ()),
    'toggle_bookmark': ApplicationCommandTarget('navigate.bookmark.toggle', ()),
    'toggle_current_line_highlight': ApplicationCommandTarget('view.current-line-highlight', ()),
    'toggle_distraction_free': ApplicationCommandTarget('view.distraction-free', ()),
    'toggle_focus_mode': ApplicationCommandTarget('view.focus-mode', ()),
    'toggle_line_numbers': ApplicationCommandTarget('options.line-numbers', ()),
    'toggle_navigator_panel': ApplicationCommandTarget('navigate.navigator-panel', ()),
    'toggle_research_panel': ApplicationCommandTarget('research.panel', ()),
    'toggle_transparent_mode': ApplicationCommandTarget('options.transparent-mode', ()),
    'toggle_typewriter_mode': ApplicationCommandTarget('writing.typewriter-mode', ()),
    'toggle_word_wrap': ApplicationCommandTarget('options.word-wrap', ()),
}

CHECK_COMMAND_IDS = {
    'on_dark_mode': 'options.appearance.dark',
    'on_line_numbers': 'options.line-numbers',
    'on_navigator_item_toggled': 'navigate.navigator-panel',
    'on_research_item_toggled': 'research.panel',
    'on_top': 'options.always-on-top',
    'on_transparent_mode': 'options.transparent-mode',
    'on_typewriter_item_toggled': 'writing.typewriter-mode',
    'on_white_background': 'options.appearance.light',
    'on_word_wrap': 'options.word-wrap',
    'on_workspace_item_toggled': 'navigate.workspace-panel',
}


def invoke_check_command(invoke_command, command_id: str, active: bool, *, source: str = "menu"):
    if not callable(invoke_command):
        raise TypeError("invoke_command must be callable")
    return invoke_command(command_id, source=source, data={"active": bool(active)})


def build_application_command_layer(ports: ApplicationCommandPorts) -> CommandLayer:
    if not isinstance(ports, ApplicationCommandPorts):
        raise TypeError("ports must be ApplicationCommandPorts")
    layer = CommandLayer(build_command_registry())
    def bind(command_id, callback):
        layer.bind_callable(command_id, callback)

    bind('edit.copy', lambda _ctx, fn=ports.edit.on_copy: fn())
    bind('edit.cut', lambda _ctx, fn=ports.edit.on_cut: fn())
    bind('edit.duplicate-line-selection', lambda _ctx, fn=ports.edit.on_duplicate_line_or_selection: fn())
    bind('edit.find-all', lambda _ctx, fn=ports.edit.on_find_all: fn())
    bind('edit.find-next', lambda _ctx, fn=ports.edit.on_find_next: fn())
    bind('edit.find-previous', lambda _ctx, fn=ports.edit.on_find_previous: fn())
    bind('edit.find-replace', lambda _ctx, fn=ports.edit.on_find_replace: fn())
    bind('edit.lowercase', lambda _ctx, fn=ports.edit.on_lowercase: fn())
    bind('edit.paste', lambda _ctx, fn=ports.edit.on_paste: fn())
    bind('edit.paste-clean-pdf', lambda _ctx, fn=ports.edit.on_paste_clean_pdf: fn())
    bind('edit.paste-plain', lambda _ctx, fn=ports.edit.on_paste_plain_text: fn())
    bind('edit.redo', lambda _ctx, fn=ports.edit.on_redo: fn())
    bind('edit.replace-all', lambda _ctx, fn=ports.edit.on_replace_all_dialog: fn())
    bind('edit.select-all', lambda _ctx, fn=ports.edit.on_select_all: fn())
    bind('edit.undo', lambda _ctx, fn=ports.edit.on_undo: fn())
    bind('edit.uppercase', lambda _ctx, fn=ports.edit.on_uppercase: fn())
    bind('file.favourite.add', lambda _ctx, fn=ports.file.on_add_favourite: fn())
    bind('file.favourite.edit', lambda _ctx, fn=ports.file.on_edit_favourites: fn())
    bind('file.favourite.reload', lambda _ctx, fn=ports.file.on_reload_favourites: fn())
    bind('file.new', lambda _ctx, fn=ports.file.on_new: fn())
    bind('file.open', lambda _ctx, fn=ports.file.on_open: fn())
    bind('file.print', lambda _ctx, fn=ports.file.on_print: fn())
    bind('file.print-preview', lambda _ctx, fn=ports.file.on_print_preview: fn())
    bind('file.quit', lambda _ctx, fn=ports.file.on_quit: fn())
    bind('file.save', lambda _ctx, fn=ports.file.on_save: fn())
    bind('file.save-as', lambda _ctx, fn=ports.file.on_save_as: fn())
    bind('file.template.manage', lambda _ctx, fn=ports.file.on_manage_templates: fn())
    bind('file.template.save', lambda _ctx, fn=ports.file.on_save_as_template: fn())
    bind('file.workspace.close', lambda _ctx, fn=ports.file.on_close_workspace: fn())
    bind('file.workspace.duplicate', lambda _ctx, fn=ports.file.on_duplicate_workspace_file: fn())
    bind('file.workspace.new-folder', lambda _ctx, fn=ports.file.on_new_workspace_folder: fn())
    bind('file.workspace.new-text-file', lambda _ctx, fn=ports.file.on_new_workspace_text_file: fn())
    bind('file.workspace.refresh', lambda _ctx, fn=ports.file.on_refresh_workspace: fn())
    bind('file.workspace.rename', lambda _ctx, fn=ports.file.on_rename_workspace_item: fn())
    bind('file.workspace.reveal', lambda _ctx, fn=ports.file.on_reveal_workspace: fn())
    bind('file.workspace.select-folder', lambda _ctx, fn=ports.file.on_select_workspace_folder: fn())
    bind('file.workspace.show-panel', lambda _ctx, fn=ports.file.show_workspace_panel: fn())
    bind('file.workspace.trash', lambda _ctx, fn=ports.file.on_move_workspace_item_to_trash: fn())
    bind('help.about', lambda _ctx, fn=ports.help.on_about: fn())
    bind('help.keyboard-shortcuts', lambda _ctx, fn=ports.help.on_keyboard_shortcuts: fn())
    bind('help.user-guide', lambda _ctx, fn=ports.help.on_user_guide: fn())
    bind('navigate.bookmark.manage', lambda _ctx, fn=ports.navigate.on_manage_bookmarks: fn())
    bind('navigate.bookmark.next', lambda _ctx, fn=ports.navigate.next_bookmark: fn())
    bind('navigate.bookmark.previous', lambda _ctx, fn=ports.navigate.previous_bookmark: fn())
    bind('navigate.bookmark.toggle', lambda _ctx, fn=ports.navigate.toggle_bookmark: fn())
    bind('navigate.document-overview', lambda _ctx, fn=ports.navigate.on_document_overview: fn())
    bind('navigate.go-line', lambda _ctx, fn=ports.navigate.on_go_to_line: fn())
    bind('navigate.go-section', lambda _ctx, fn=ports.navigate.on_go_to_section: fn())
    bind('navigate.heading.next', lambda _ctx, fn=ports.navigate.on_next_heading: fn())
    bind('navigate.heading.previous', lambda _ctx, fn=ports.navigate.on_previous_heading: fn())
    bind('options.font', lambda _ctx, fn=ports.options.on_font: fn())
    bind('options.opacity.select', lambda _ctx, fn=ports.options.on_opacity_selection: fn())
    bind('research.authoring-bridge', lambda _ctx, fn=ports.research.show_authoring_bridge: fn())
    bind('research.bibliography', lambda _ctx, fn=ports.research.show_references: fn())
    bind('research.capture-scratchpad', lambda _ctx, fn=ports.research.on_capture_selection_in_scratchpad: fn())
    bind('research.check', lambda _ctx, fn=ports.research.on_research_check: fn())
    bind('research.clips', lambda _ctx, fn=ports.research.show_clip_collection: fn())
    bind('research.create-source-note', lambda _ctx, fn=ports.research.on_create_source_note_from_selection: fn())
    bind('research.export-apparatus', lambda _ctx, fn=ports.research.on_export_research_apparatus: fn())
    bind('research.export-bib', lambda _ctx, fn=ports.research.on_export_references_bibtex_biblatex: fn())
    bind('research.export-bibliography-markdown', lambda _ctx, fn=ports.research.on_export_bibliography_markdown: fn())
    bind('research.export-bibliography-text', lambda _ctx, fn=ports.research.on_export_bibliography_text: fn())
    bind('research.export-pandoc', lambda _ctx, fn=ports.research.on_export_with_pandoc: fn())
    bind('research.import-bib', lambda _ctx, fn=ports.research.on_import_bibtex_biblatex: fn())
    bind('research.insert-clip', lambda _ctx, fn=ports.research.on_insert_clip: fn())
    bind('research.insert-heading-link', lambda _ctx, fn=ports.research.on_insert_link_to_heading: fn())
    bind('research.new-scratchpad-section', lambda _ctx, fn=ports.research.on_new_scratchpad_for_current_section: fn())
    bind('research.open-bibliography', lambda _ctx, fn=ports.research.on_open_bibliography_file: fn())
    bind('research.open-citation', lambda _ctx, fn=ports.research.on_open_citation_in_references: fn())
    bind('research.quick-cite', lambda _ctx, fn=ports.research.on_quick_cite: fn())
    bind('research.reference-sets', lambda _ctx, fn=ports.research.show_reference_sets: fn())
    bind('research.rename-reference-key', lambda _ctx, fn=ports.research.on_rename_reference_key: fn())
    bind('research.scratchpad', lambda _ctx, fn=ports.research.show_scratchpad: fn())
    bind('research.show-scratchpad-section', lambda _ctx, fn=ports.research.on_show_scratchpad_for_current_section: fn())
    bind('research.source-notes', lambda _ctx, fn=ports.research.show_source_notes: fn())
    bind('research.tag-integrity', lambda _ctx, fn=ports.research.on_tag_integrity: fn())
    bind('research.tags', lambda _ctx, fn=ports.research.show_tags: fn())
    bind('tools.language', lambda _ctx, fn=ports.tools.on_language_selection: fn())
    bind('tools.spellcheck', lambda _ctx, fn=ports.tools.on_check: fn())
    bind('tools.system-info', lambda _ctx, fn=ports.tools.on_system_info: fn())
    bind('view.character-map', lambda _ctx, fn=ports.view.on_character_map: fn())
    bind('view.current-line-highlight', lambda _ctx, fn=ports.view.toggle_current_line_highlight: fn())
    bind('view.distraction-free', lambda _ctx, fn=ports.view.toggle_distraction_free: fn())
    bind('view.focus-mode', lambda _ctx, fn=ports.view.toggle_focus_mode: fn())
    bind('writing.clean-pdf', lambda _ctx, fn=ports.writing.on_clean_selected_pdf: fn())
    bind('writing.insert-date', lambda _ctx, fn=ports.writing.on_insert_date: fn())
    bind('writing.insert-date-time', lambda _ctx, fn=ports.writing.on_insert_datetime: fn())
    bind('writing.insert-time', lambda _ctx, fn=ports.writing.on_insert_time: fn())
    bind('writing.join-lines', lambda _ctx, fn=ports.writing.on_join_lines: fn())
    bind('writing.reflow-paragraph', lambda _ctx, fn=ports.writing.on_reflow_paragraph: fn())
    bind('writing.remove-extra-spaces', lambda _ctx, fn=ports.writing.on_remove_extra_spaces: fn())
    bind('writing.remove-trailing-spaces', lambda _ctx, fn=ports.writing.on_remove_trailing_spaces: fn())
    bind('writing.sentence-case', lambda _ctx, fn=ports.writing.on_sentence_case: fn())
    bind('writing.smart-typography', lambda _ctx, fn=ports.writing.on_smart_typography: fn())
    bind('writing.statistics', lambda _ctx, fn=ports.writing.on_document_statistics: fn())
    bind('writing.title-case', lambda _ctx, fn=ports.writing.on_title_case: fn())
    bind("writing.sort-lines", lambda ctx: ports.writing.on_sort_lines_descending() if bool(ctx.get("reverse", False)) else ports.writing.on_sort_lines_ascending())
    bind("edit.move-line", lambda ctx: ports.edit.on_move_line(_int_in(ctx, "direction", {-1, 1})))
    bind("options.font-size.adjust", lambda ctx: ports.options.change_font(_int_in(ctx, "delta", {-1, 1})))
    bind("options.opacity.set", lambda ctx: ports.options.set_opacity_value(_int_in(ctx, "percent", {30, 40, 50, 60, 70, 80, 88, 90, 100})))
    bind("research.insert-clip-slot", lambda ctx: ports.research.insert_clip_number(_int_in(ctx, "number", set(range(1, 10)))))
    bind("file.template.open", lambda ctx: ports.file.on_new_from_template(_required(ctx, "path", str)))
    bind("file.recent.open", lambda ctx: ports.file.open_recent_path(_required(ctx, "path", str)))
    bind("file.favourite.open", lambda ctx: ports.file.open_favourite_path(_required(ctx, "path", str)))
    bind("file.workspace.recent.open", lambda ctx: ports.file.activate_workspace_path(_required(ctx, "path", str)))
    bind("file.open-drop", lambda ctx: ports.file.open_path(_required(ctx, "path", str)) if ports.file.may_continue() else False)
    bind("file.recent.clear", lambda _ctx: ports.file.on_clear_recent())

    def bind_toggle(command_id, menu_handler, shortcut_toggle):
        def execute(ctx):
            if "active" in ctx.data:
                active = ctx.get("active")
                if not isinstance(active, bool):
                    raise CommandInputError("active must be bool")
                return menu_handler(_ActiveValue(active))
            return shortcut_toggle()
        bind(command_id, execute)

    bind_toggle("research.panel", ports.research.on_research_item_toggled, ports.research.toggle_research_panel)
    bind_toggle("navigate.navigator-panel", ports.navigate.on_navigator_item_toggled, ports.navigate.toggle_navigator_panel)
    bind_toggle("navigate.workspace-panel", ports.navigate.on_workspace_item_toggled, ports.navigate.toggle_workspace_panel)
    bind_toggle("writing.typewriter-mode", ports.writing.on_typewriter_item_toggled, ports.writing.toggle_typewriter_mode)
    bind_toggle("options.word-wrap", ports.options.on_word_wrap, ports.options.toggle_word_wrap)
    bind_toggle("options.transparent-mode", ports.options.on_transparent_mode, ports.options.toggle_transparent_mode)
    bind_toggle("options.always-on-top", ports.options.on_top, ports.options.toggle_always_on_top)
    bind_toggle("options.line-numbers", ports.options.on_line_numbers, ports.options.toggle_line_numbers)
    bind("options.appearance.light", lambda ctx: ports.options.on_white_background(_ActiveValue(_required(ctx, "active", bool))))
    bind("options.appearance.dark", lambda ctx: ports.options.on_dark_mode(_ActiveValue(_required(ctx, "active", bool))))
    return layer
