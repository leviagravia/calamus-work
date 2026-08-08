"""Stateless W101 orchestration for the non-Research application graph.

W108 rule: this reusable composition boundary receives only one immutable,
exactly-named input record.  It never receives or mutates the concrete App.
"""
from __future__ import annotations

from dataclasses import replace

from calamus_application_components import (
    ClipCollectionCompositionInput,
    CoreApplicationComponents,
    CoreApplicationCompositionInput,
    DocumentSessionCompositionInput,
    EditorCompositionInput,
    EditorTransactionCompositionInput,
    NavigatorCompositionInput,
    RightPanelHostInput,
    WorkspaceCompositionInput,
)
from calamus_document import is_large_text_file, read_text_file, write_text_file
from calamus_clip_composition import build_clip_collection_components, build_right_panel_host
from calamus_document_session_composition import build_document_session_components
from calamus_editor_composition import build_editor_infrastructure
from calamus_editor_transaction_composition import build_editor_transaction_components
from calamus_navigator_composition import build_navigator_components
from calamus_workspace_host_gtk import WorkspaceHostGtkAdapter
from calamus_workspace_composition import bind_workspace_startup, build_workspace_components


CORE_BUILD_ORDER = (
    "document-session",
    "editor-infrastructure",
    "editor-transaction",
    "navigator-and-left-panel-host",
    "workspace",
    "right-panel-host",
    "clip-collection",
    "workspace-startup-binding",
)


def compose_core_application_components(
    inputs: CoreApplicationCompositionInput,
) -> CoreApplicationComponents:
    if not isinstance(inputs, CoreApplicationCompositionInput):
        raise TypeError("inputs must be CoreApplicationCompositionInput")

    document_session = build_document_session_components(
        DocumentSessionCompositionInput(
            initial_file_path=inputs.initial_file_path,
            read_buffer_text=inputs.read_buffer_text,
            replace_buffer_text=inputs.replace_buffer_text,
            reset_undo_history=inputs.reset_undo_history,
            read_text_file=read_text_file,
            write_text_file=write_text_file,
            is_large_text_file=is_large_text_file,
        )
    )
    editor = build_editor_infrastructure(
        EditorCompositionInput(
            text_view=inputs.text_view,
            scroller=inputs.scroller,
            on_typewriter_state_changed=inputs.on_typewriter_state_changed,
            on_buffer_changed=inputs.on_buffer_changed,
            on_buffer_begin_user_action=inputs.on_buffer_begin_user_action,
            on_buffer_end_user_action=inputs.on_buffer_end_user_action,
            on_cursor_position_notify=inputs.on_cursor_position_notify,
            on_text_key_press=inputs.on_text_key_press,
            on_text_key_release=inputs.on_text_key_release,
            on_text_move_cursor=inputs.on_text_move_cursor,
            on_text_button_press=inputs.on_text_button_press,
            on_text_motion_notify=inputs.on_text_motion_notify,
            on_text_button_release=inputs.on_text_button_release,
            on_text_scroll=inputs.on_text_scroll,
            on_text_focus_out=inputs.on_text_focus_out,
            apply_wrap_policy=inputs.apply_wrap_policy,
        )
    )
    editor_transaction = build_editor_transaction_components(
        EditorTransactionCompositionInput(
            text_view=inputs.text_view,
            document_session=document_session.session,
            document_session_controller=document_session.controller,
            history_runtime=editor.history_runtime,
        )
    )
    navigator = build_navigator_components(
        NavigatorCompositionInput(
            text_view=inputs.text_view,
            workspace_paned=inputs.workspace_paned,
            queue_wrap_reflow=inputs.queue_wrap_reflow,
            on_visibility_changed=inputs.on_navigator_visibility_changed,
        )
    )
    workspace_gtk = WorkspaceHostGtkAdapter(inputs.dialog_parent, inputs.menu_ui_adapter)
    workspace_input = WorkspaceCompositionInput(
        left_panel_host=navigator.left_panel_host,
        recent_workspaces=inputs.recent_workspaces,
        recent_files=inputs.recent_files,
        favourites=inputs.favourites,
        application_state=inputs.application_state,
        document_session=document_session.session,
        text_view=inputs.text_view,
        workspace_root=inputs.workspace_root,
        workspace_visible=inputs.workspace_visible,
        may_continue=inputs.may_continue,
        open_document=inputs.open_document,
        record_workspace_root=inputs.application_state.record_workspace_root,
        report_error=inputs.report_error,
        render_recent_workspaces=workspace_gtk.render_recent_workspaces,
        choose_workspace_root=workspace_gtk.choose_root,
        prompt_new_text_file=workspace_gtk.prompt_new_text_file,
        prompt_new_folder=workspace_gtk.prompt_new_folder,
        prompt_rename_item=workspace_gtk.prompt_rename_item,
        confirm_trash=workspace_gtk.confirm_trash,
        show_workspace_error=workspace_gtk.show_error,
        document_text=inputs.document_text,
        research_context_changed=inputs.research_context_changed,
        update_title=inputs.update_title,
        refresh_overview=inputs.refresh_overview,
        refresh_ui_state=inputs.refresh_ui_state,
    )
    workspace = build_workspace_components(workspace_input)
    right_panel_host = build_right_panel_host(
        RightPanelHostInput(body_paned=inputs.body_paned, queue_wrap_reflow=inputs.queue_wrap_reflow)
    )
    clips = build_clip_collection_components(
        ClipCollectionCompositionInput(
            dialog_parent=inputs.dialog_parent,
            config_dir=inputs.config_dir,
            text_view=inputs.text_view,
            execute_command=inputs.execute_command,
            get_cursor_offset=inputs.get_cursor_offset,
            set_cursor_offset=inputs.set_cursor_offset,
            sync_history_view_state=inputs.sync_history_view_state,
            queue_insert_scroll=inputs.queue_insert_scroll,
            publish_invalidation=inputs.publish_invalidation,
            clip_invalidation_reason=inputs.clip_invalidation_reason,
        )
    )
    return CoreApplicationComponents(
        document_session=document_session,
        editor=editor,
        editor_transaction=editor_transaction,
        navigator=navigator,
        workspace=workspace,
        right_panel_host=right_panel_host,
        clips=clips,
        build_order=CORE_BUILD_ORDER,
        composition_complete=False,
    )


def complete_core_application_components(
    components: CoreApplicationComponents,
    workspace_root: str | None,
    workspace_visible: bool,
) -> CoreApplicationComponents:
    """Apply the delayed Workspace startup binding after shell alias projection."""
    if not isinstance(components, CoreApplicationComponents):
        raise TypeError("components must be CoreApplicationComponents")
    if components.composition_complete:
        raise RuntimeError("core application components already completed")
    workspace = bind_workspace_startup(components.workspace, workspace_root, workspace_visible)
    return replace(components, workspace=workspace, composition_complete=True)
