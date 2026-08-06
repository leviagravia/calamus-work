"""Stateless W101 orchestration for the non-Research application graph."""
from __future__ import annotations

from calamus_application_components import (
    ClipCollectionCompositionInput,
    CoreApplicationComponents,
    EditorCompositionInput,
    NavigatorCompositionInput,
    RightPanelHostInput,
    WorkspaceCompositionInput,
)
from calamus_clip_composition import (
    build_clip_collection_components,
    build_right_panel_host,
)
from calamus_editor_composition import build_editor_infrastructure
from calamus_navigator_composition import build_navigator_components
from calamus_workspace_composition import (
    bind_workspace_startup,
    build_workspace_components,
)


CORE_BUILD_ORDER = (
    "editor-infrastructure",
    "navigator-and-left-panel-host",
    "workspace",
    "right-panel-host",
    "clip-collection",
    "workspace-startup-binding",
)


def compose_core_application_components(
    app,
    *,
    clip_invalidation_reason,
) -> CoreApplicationComponents:
    editor = build_editor_infrastructure(
        EditorCompositionInput(
            text_view=app.text,
            scroller=app.scroller,
            on_typewriter_state_changed=app.on_typewriter_state_changed,
            on_buffer_changed=app.on_changed,
            on_buffer_begin_user_action=app.on_buffer_begin_user_action,
            on_buffer_end_user_action=app.on_buffer_end_user_action,
            on_cursor_position_notify=app.on_cursor_position_notify,
            on_text_key_press=app.on_text_key_press,
            on_text_key_release=app.on_text_key_release,
            on_text_move_cursor=app.on_text_move_cursor,
            on_text_button_press=app.on_text_button_press,
            on_text_motion_notify=app.on_text_motion_notify,
            on_text_button_release=app.on_text_button_release,
            on_text_scroll=app.on_text_scroll,
            on_text_focus_out=app.on_text_focus_out,
            apply_wrap_policy=app.apply_wrap_policy,
        )
    )
    navigator = build_navigator_components(
        NavigatorCompositionInput(
            text_view=app.text,
            workspace_paned=app.workspace_paned,
            queue_wrap_reflow=app.queue_wrap_reflow,
            navigator_menu_item=app.navigator_item,
        )
    )
    workspace_input = WorkspaceCompositionInput(
        left_panel_host=navigator.left_panel_host,
        state=app.state,
        workspace_menu_item=app.workspace_item,
        text_view=app.text,
        workspace_root=app.workspace_root,
        workspace_visible=app.workspace_visible,
        may_continue=app.may_continue,
        open_document=app.open_path,
        save_settings=app.save_settings,
        report_error=app.error,
        on_root_changed=app.on_workspace_root_changed,
        on_recent_changed=app.populate_recent_workspaces_menu,
        on_visibility_changed=app.on_workspace_visibility_changed,
        on_new_text_file=app.on_new_workspace_text_file,
        on_new_folder=app.on_new_workspace_folder,
        on_rename_item=app.on_rename_workspace_item,
        on_duplicate_file=app.on_duplicate_workspace_file,
        on_move_to_trash=app.on_move_workspace_item_to_trash,
        on_choose_root=app.on_select_workspace_folder,
        on_refresh=app.on_refresh_workspace,
        on_reveal=app.on_reveal_workspace,
        capture_path_references=app.capture_workspace_path_references,
        reconcile_rename=app.reconcile_workspace_rename,
        current_document_path=lambda: app.current_file,
        confirm_trash=app.confirm_workspace_trash,
        reconcile_trash=app.reconcile_workspace_trash,
    )
    workspace = build_workspace_components(workspace_input)
    right_panel_host = build_right_panel_host(
        RightPanelHostInput(
            body_paned=app.body_paned,
            queue_wrap_reflow=app.queue_wrap_reflow,
        )
    )
    clips = build_clip_collection_components(
        ClipCollectionCompositionInput(
            dialog_parent=app,
            config_dir=app.state.config_dir,
            text_view=app.text,
            execute_command=app.execute_command,
            get_cursor_offset=app.get_cursor_offset,
            set_cursor_offset=app.set_cursor_offset,
            sync_history_view_state=app.sync_current_history_view_state,
            queue_insert_scroll=app.queue_insert_scroll,
            publish_invalidation=app.publish_research_invalidation,
            clip_invalidation_reason=clip_invalidation_reason,
        )
    )
    # Static compatibility projections. The typed bundles are authoritative;
    # these exact aliases preserve the published App surface until W111.
    app.history = editor.history
    app.viewport_runtime = editor.viewport_runtime
    app.history_runtime = editor.history_runtime
    app.typewriter_runtime = editor.typewriter_runtime
    app.search_controller = editor.search_controller
    app.tag = editor.misspelling_tag
    app.search_tag = editor.search_tag
    app.current_line_tag = editor.current_line_tag

    app.navigation_controller = navigator.navigation_controller
    app.left_panel_host = navigator.left_panel_host
    app.navigator_panel_view = navigator.panel_view
    app.navigator_panel_host = navigator.panel_host
    app.navigator_panel_runtime = navigator.panel_runtime

    app.workspace_controller = workspace.controller
    app.workspace_panel_view = workspace.panel_view
    app.workspace_application_runtime = workspace.application_runtime
    app.workspace_mutation_controller = workspace.mutation_controller
    app.workspace_mutation_runtime = workspace.mutation_runtime
    app.workspace_panel_host = workspace.panel_host
    app.workspace_panel_runtime = workspace.panel_runtime

    app.right_panel_host = right_panel_host
    app.clip_collection_view = clips.view
    app.clip_collection = clips.controller
    app.clip_collection_runtime = clips.runtime

    # Startup-root binding is deliberately delayed until every core owner and
    # compatibility projection exists. This is the W101 composition-complete
    # barrier; visible panel activation remains in App after full construction.
    workspace = bind_workspace_startup(
        workspace,
        workspace_input.workspace_root,
        workspace_input.workspace_visible,
    )
    return CoreApplicationComponents(
        editor=editor,
        navigator=navigator,
        workspace=workspace,
        right_panel_host=right_panel_host,
        clips=clips,
        build_order=CORE_BUILD_ORDER,
        composition_complete=True,
    )
