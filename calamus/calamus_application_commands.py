"""Application-bound W104 command execution adapters.

This is the explicit composition boundary where stable GTK-free command IDs are
bound to existing application callbacks.  The command core never receives App.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

from calamus_command_catalog import build_command_registry
from calamus_command_context import CommandContext, CommandInputError
from calamus_command_layer import CommandLayer


@dataclass(frozen=True)
class ApplicationCommandTarget:
    command_id: str
    payload: tuple[tuple[str, object], ...] = ()

    def data(self):
        return dict(self.payload)


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

def command_target_for_callback(callback):
    """Resolve a known bound App callback to stable command identity for GTK menu wiring."""
    name = getattr(callback, "__name__", "")
    return APPLICATION_METHOD_TARGETS.get(name)


def invoke_check_command(app, command_id: str, active: bool, *, source: str = "menu"):
    return app.invoke_command(command_id, source=source, data={"active": bool(active)})


def build_application_command_layer(app) -> CommandLayer:
    layer = CommandLayer(build_command_registry())
    def bind(command_id, callback):
        layer.bind_callable(command_id, callback)

    bind('edit.copy', lambda _ctx, fn=app.on_copy: fn())
    bind('edit.cut', lambda _ctx, fn=app.on_cut: fn())
    bind('edit.duplicate-line-selection', lambda _ctx, fn=app.on_duplicate_line_or_selection: fn())
    bind('edit.find-all', lambda _ctx, fn=app.on_find_all: fn())
    bind('edit.find-next', lambda _ctx, fn=app.on_find_next: fn())
    bind('edit.find-previous', lambda _ctx, fn=app.on_find_previous: fn())
    bind('edit.find-replace', lambda _ctx, fn=app.on_find_replace: fn())
    bind('edit.lowercase', lambda _ctx, fn=app.on_lowercase: fn())
    bind('edit.paste', lambda _ctx, fn=app.on_paste: fn())
    bind('edit.paste-clean-pdf', lambda _ctx, fn=app.on_paste_clean_pdf: fn())
    bind('edit.paste-plain', lambda _ctx, fn=app.on_paste_plain_text: fn())
    bind('edit.redo', lambda _ctx, fn=app.on_redo: fn())
    bind('edit.replace-all', lambda _ctx, fn=app.on_replace_all_dialog: fn())
    bind('edit.select-all', lambda _ctx, fn=app.on_select_all: fn())
    bind('edit.undo', lambda _ctx, fn=app.on_undo: fn())
    bind('edit.uppercase', lambda _ctx, fn=app.on_uppercase: fn())
    bind('file.favourite.add', lambda _ctx, fn=app.on_add_favourite: fn())
    bind('file.favourite.edit', lambda _ctx, fn=app.on_edit_favourites: fn())
    bind('file.favourite.reload', lambda _ctx, fn=app.on_reload_favourites: fn())
    bind('file.new', lambda _ctx, fn=app.on_new: fn())
    bind('file.open', lambda _ctx, fn=app.on_open: fn())
    bind('file.print', lambda _ctx, fn=app.on_print: fn())
    bind('file.print-preview', lambda _ctx, fn=app.on_print_preview: fn())
    bind('file.quit', lambda _ctx, fn=app.on_quit: fn())
    bind('file.save', lambda _ctx, fn=app.on_save: fn())
    bind('file.save-as', lambda _ctx, fn=app.on_save_as: fn())
    bind('file.template.manage', lambda _ctx, fn=app.on_manage_templates: fn())
    bind('file.template.save', lambda _ctx, fn=app.on_save_as_template: fn())
    bind('file.workspace.close', lambda _ctx, fn=app.on_close_workspace: fn())
    bind('file.workspace.duplicate', lambda _ctx, fn=app.on_duplicate_workspace_file: fn())
    bind('file.workspace.new-folder', lambda _ctx, fn=app.on_new_workspace_folder: fn())
    bind('file.workspace.new-text-file', lambda _ctx, fn=app.on_new_workspace_text_file: fn())
    bind('file.workspace.refresh', lambda _ctx, fn=app.on_refresh_workspace: fn())
    bind('file.workspace.rename', lambda _ctx, fn=app.on_rename_workspace_item: fn())
    bind('file.workspace.reveal', lambda _ctx, fn=app.on_reveal_workspace: fn())
    bind('file.workspace.select-folder', lambda _ctx, fn=app.on_select_workspace_folder: fn())
    bind('file.workspace.show-panel', lambda _ctx, fn=app.show_workspace_panel: fn())
    bind('file.workspace.trash', lambda _ctx, fn=app.on_move_workspace_item_to_trash: fn())
    bind('help.about', lambda _ctx, fn=app.on_about: fn())
    bind('help.keyboard-shortcuts', lambda _ctx, fn=app.on_keyboard_shortcuts: fn())
    bind('help.user-guide', lambda _ctx, fn=app.on_user_guide: fn())
    bind('navigate.bookmark.manage', lambda _ctx, fn=app.on_manage_bookmarks: fn())
    bind('navigate.bookmark.next', lambda _ctx, fn=app.next_bookmark: fn())
    bind('navigate.bookmark.previous', lambda _ctx, fn=app.previous_bookmark: fn())
    bind('navigate.bookmark.toggle', lambda _ctx, fn=app.toggle_bookmark: fn())
    bind('navigate.document-overview', lambda _ctx, fn=app.on_document_overview: fn())
    bind('navigate.go-line', lambda _ctx, fn=app.on_go_to_line: fn())
    bind('navigate.go-section', lambda _ctx, fn=app.on_go_to_section: fn())
    bind('navigate.heading.next', lambda _ctx, fn=app.on_next_heading: fn())
    bind('navigate.heading.previous', lambda _ctx, fn=app.on_previous_heading: fn())
    bind('options.font', lambda _ctx, fn=app.on_font: fn())
    bind('options.opacity.select', lambda _ctx, fn=app.on_opacity_selection: fn())
    bind('research.authoring-bridge', lambda _ctx, fn=app.show_authoring_bridge: fn())
    bind('research.bibliography', lambda _ctx, fn=app.show_references: fn())
    bind('research.capture-scratchpad', lambda _ctx, fn=app.on_capture_selection_in_scratchpad: fn())
    bind('research.check', lambda _ctx, fn=app.on_research_check: fn())
    bind('research.clips', lambda _ctx, fn=app.show_clip_collection: fn())
    bind('research.create-source-note', lambda _ctx, fn=app.on_create_source_note_from_selection: fn())
    bind('research.export-apparatus', lambda _ctx, fn=app.on_export_research_apparatus: fn())
    bind('research.export-bib', lambda _ctx, fn=app.on_export_references_bibtex_biblatex: fn())
    bind('research.export-bibliography-markdown', lambda _ctx, fn=app.on_export_bibliography_markdown: fn())
    bind('research.export-bibliography-text', lambda _ctx, fn=app.on_export_bibliography_text: fn())
    bind('research.export-pandoc', lambda _ctx, fn=app.on_export_with_pandoc: fn())
    bind('research.import-bib', lambda _ctx, fn=app.on_import_bibtex_biblatex: fn())
    bind('research.insert-clip', lambda _ctx, fn=app.on_insert_clip: fn())
    bind('research.insert-heading-link', lambda _ctx, fn=app.on_insert_link_to_heading: fn())
    bind('research.new-scratchpad-section', lambda _ctx, fn=app.on_new_scratchpad_for_current_section: fn())
    bind('research.open-bibliography', lambda _ctx, fn=app.on_open_bibliography_file: fn())
    bind('research.open-citation', lambda _ctx, fn=app.on_open_citation_in_references: fn())
    bind('research.quick-cite', lambda _ctx, fn=app.on_quick_cite: fn())
    bind('research.reference-sets', lambda _ctx, fn=app.show_reference_sets: fn())
    bind('research.rename-reference-key', lambda _ctx, fn=app.on_rename_reference_key: fn())
    bind('research.scratchpad', lambda _ctx, fn=app.show_scratchpad: fn())
    bind('research.show-scratchpad-section', lambda _ctx, fn=app.on_show_scratchpad_for_current_section: fn())
    bind('research.source-notes', lambda _ctx, fn=app.show_source_notes: fn())
    bind('research.tag-integrity', lambda _ctx, fn=app.on_tag_integrity: fn())
    bind('research.tags', lambda _ctx, fn=app.show_tags: fn())
    bind('tools.language', lambda _ctx, fn=app.on_language_selection: fn())
    bind('tools.spellcheck', lambda _ctx, fn=app.on_check: fn())
    bind('tools.system-info', lambda _ctx, fn=app.on_system_info: fn())
    bind('view.character-map', lambda _ctx, fn=app.on_character_map: fn())
    bind('view.current-line-highlight', lambda _ctx, fn=app.toggle_current_line_highlight: fn())
    bind('view.distraction-free', lambda _ctx, fn=app.toggle_distraction_free: fn())
    bind('view.focus-mode', lambda _ctx, fn=app.toggle_focus_mode: fn())
    bind('writing.clean-pdf', lambda _ctx, fn=app.on_clean_selected_pdf: fn())
    bind('writing.insert-date', lambda _ctx, fn=app.on_insert_date: fn())
    bind('writing.insert-date-time', lambda _ctx, fn=app.on_insert_datetime: fn())
    bind('writing.insert-time', lambda _ctx, fn=app.on_insert_time: fn())
    bind('writing.join-lines', lambda _ctx, fn=app.on_join_lines: fn())
    bind('writing.reflow-paragraph', lambda _ctx, fn=app.on_reflow_paragraph: fn())
    bind('writing.remove-extra-spaces', lambda _ctx, fn=app.on_remove_extra_spaces: fn())
    bind('writing.remove-trailing-spaces', lambda _ctx, fn=app.on_remove_trailing_spaces: fn())
    bind('writing.sentence-case', lambda _ctx, fn=app.on_sentence_case: fn())
    bind('writing.smart-typography', lambda _ctx, fn=app.on_smart_typography: fn())
    bind('writing.statistics', lambda _ctx, fn=app.on_document_statistics: fn())
    bind('writing.title-case', lambda _ctx, fn=app.on_title_case: fn())
    bind("writing.sort-lines", lambda ctx: app.on_sort_lines_descending() if bool(ctx.get("reverse", False)) else app.on_sort_lines_ascending())
    bind("edit.move-line", lambda ctx: app.on_move_line(_int_in(ctx, "direction", {-1, 1})))
    bind("options.font-size.adjust", lambda ctx: app.change_font(_int_in(ctx, "delta", {-1, 1})))
    bind("options.opacity.set", lambda ctx: app.set_opacity_value(_int_in(ctx, "percent", {30, 40, 50, 60, 70, 80, 88, 90, 100})))
    bind("research.insert-clip-slot", lambda ctx: app.insert_clip_number(_int_in(ctx, "number", set(range(1, 10)))))
    bind("file.template.open", lambda ctx: app.on_new_from_template(_required(ctx, "path", str)))
    bind("file.recent.open", lambda ctx: app.open_recent_path(_required(ctx, "path", str)))
    bind("file.favourite.open", lambda ctx: app.open_favourite_path(_required(ctx, "path", str)))
    bind("file.workspace.recent.open", lambda ctx: app.activate_workspace_path(_required(ctx, "path", str)))
    bind("file.open-drop", lambda ctx: app.open_path(_required(ctx, "path", str)) if app.may_continue() else False)
    bind("file.recent.clear", lambda _ctx: app.on_clear_recent())

    def bind_toggle(command_id, menu_handler, shortcut_toggle):
        def execute(ctx):
            if "active" in ctx.data:
                active = ctx.get("active")
                if not isinstance(active, bool):
                    raise CommandInputError("active must be bool")
                return menu_handler(_ActiveValue(active))
            return shortcut_toggle()
        bind(command_id, execute)

    bind_toggle("research.panel", app.on_research_item_toggled, app.toggle_research_panel)
    bind_toggle("navigate.navigator-panel", app.on_navigator_item_toggled, app.toggle_navigator_panel)
    bind_toggle("navigate.workspace-panel", app.on_workspace_item_toggled, app.toggle_workspace_panel)
    bind_toggle("writing.typewriter-mode", app.on_typewriter_item_toggled, app.toggle_typewriter_mode)
    bind_toggle("options.word-wrap", app.on_word_wrap, app.toggle_word_wrap)
    bind_toggle("options.transparent-mode", app.on_transparent_mode, app.toggle_transparent_mode)
    bind_toggle("options.always-on-top", app.on_top, app.toggle_always_on_top)
    bind_toggle("options.line-numbers", app.on_line_numbers, app.toggle_line_numbers)
    bind("options.appearance.light", lambda ctx: app.on_white_background(_ActiveValue(_required(ctx, "active", bool))))
    bind("options.appearance.dark", lambda ctx: app.on_dark_mode(_ActiveValue(_required(ctx, "active", bool))))
    return layer
