"""Local W101 builder for Writing Workspace ownership."""
from __future__ import annotations

from dataclasses import replace

from calamus_application_components import (
    SetOnceReference,
    WorkspaceComponents,
    WorkspaceCompositionInput,
)
from calamus_workspace_application import WorkspaceApplicationRuntime
from calamus_workspace_controller import WorkspaceController
from calamus_workspace_external import open_external_path, reveal_in_file_manager
from calamus_workspace_gio import WorkspaceGioAdapter
from calamus_workspace_host_runtime import WorkspaceHostPorts, WorkspaceHostRuntime
from calamus_workspace_mutation import WorkspaceMutationController, WorkspaceMutationRuntime
from calamus_workspace_panel import WorkspacePanelRuntime, WorkspacePanelView


def build_workspace_components(
    inputs: WorkspaceCompositionInput,
) -> WorkspaceComponents:
    # W101 permits bounded callback cycles only through named set-once references.
    # The Workspace host is therefore constructed only after its concrete domain
    # collaborators exist; views/runtimes created earlier close over this local
    # reference rather than receiving an aggregate WorkspaceComponents bundle.
    host_reference = SetOnceReference("workspace-host-runtime")
    application_reference = SetOnceReference("workspace-application-runtime")
    panel_reference = SetOnceReference("workspace-panel-runtime")

    controller = WorkspaceController()
    panel_view = WorkspacePanelView(
        on_hide=lambda: panel_reference.require().hide(),
        on_new_text_file=lambda: host_reference.require().on_new_workspace_text_file(),
        on_new_folder=lambda: host_reference.require().on_new_workspace_folder(),
        on_rename_item=lambda: host_reference.require().on_rename_workspace_item(),
        on_duplicate_file=lambda: host_reference.require().on_duplicate_workspace_file(),
        on_move_to_trash=lambda: host_reference.require().on_move_workspace_item_to_trash(),
        on_choose_root=lambda: host_reference.require().on_select_workspace_folder(),
        on_refresh=lambda: host_reference.require().on_refresh_workspace(),
        on_reveal=lambda: host_reference.require().on_reveal_workspace(),
        on_activate_item=lambda item: application_reference.require().activate_item(item),
    )
    application_runtime = WorkspaceApplicationRuntime(
        controller,
        panel_view,
        inputs.recent_workspaces,
        may_continue=inputs.may_continue,
        open_document=inputs.open_document,
        open_external=open_external_path,
        reveal_external=reveal_in_file_manager,
        record_workspace_root=inputs.record_workspace_root,
        report_error=inputs.report_error,
        on_root_changed=lambda root: host_reference.require().on_workspace_root_changed(root),
        on_recent_changed=lambda: host_reference.require().populate_recent_workspaces_menu(),
    )
    application_reference.set(application_runtime)

    mutation_controller = WorkspaceMutationController(
        controller,
        WorkspaceGioAdapter(),
    )
    mutation_runtime = WorkspaceMutationRuntime(
        mutation_controller,
        application_runtime,
        panel_view,
        may_continue=inputs.may_continue,
        open_document=inputs.open_document,
        report_error=inputs.report_error,
        capture_path_references=lambda: host_reference.require().capture_workspace_path_references(),
        reconcile_rename=lambda plan, refs: host_reference.require().reconcile_workspace_rename(plan, refs),
        current_document_path=inputs.document_session.current_path,
        confirm_trash=lambda plan, active: host_reference.require().confirm_workspace_trash(plan, active),
        reconcile_trash=lambda plan, refs: host_reference.require().reconcile_workspace_trash(plan, refs),
    )
    panel_host = inputs.left_panel_host.register("workspace", panel_view.widget)
    panel_runtime = WorkspacePanelRuntime(
        panel_host,
        panel_view,
        inputs.text_view.grab_focus,
        lambda visible: host_reference.require().on_workspace_visibility_changed(visible),
    )
    panel_reference.set(panel_runtime)

    host_runtime = WorkspaceHostRuntime(
        recent_workspaces=inputs.recent_workspaces,
        recent_files=inputs.recent_files,
        favourites=inputs.favourites,
        application_state=inputs.application_state,
        document_session=inputs.document_session,
        application_runtime=application_runtime,
        mutation_controller=mutation_controller,
        mutation_runtime=mutation_runtime,
        panel_view=panel_view,
        panel_runtime=panel_runtime,
        ports=WorkspaceHostPorts(
            render_recent_workspaces=inputs.render_recent_workspaces,
            choose_root=inputs.choose_workspace_root,
            prompt_new_text_file=inputs.prompt_new_text_file,
            prompt_new_folder=inputs.prompt_new_folder,
            prompt_rename_item=inputs.prompt_rename_item,
            confirm_trash=inputs.confirm_trash,
            show_error=inputs.show_workspace_error,
            document_text=inputs.document_text,
            research_context_changed=inputs.research_context_changed,
            update_title=inputs.update_title,
            refresh_overview=inputs.refresh_overview,
            refresh_ui_state=inputs.refresh_ui_state,
        ),
    )
    host_reference.set(host_runtime)

    return WorkspaceComponents(
        controller=controller,
        panel_view=panel_view,
        application_runtime=application_runtime,
        mutation_controller=mutation_controller,
        mutation_runtime=mutation_runtime,
        panel_host=panel_host,
        panel_runtime=panel_runtime,
        host_runtime=host_runtime,
        startup_visible=False,
    )


def bind_workspace_startup(
    components: WorkspaceComponents,
    root: str | None,
    requested_visible: bool,
) -> WorkspaceComponents:
    bound = components.application_runtime.bind_startup_root(root)
    return replace(
        components,
        startup_visible=bool(bound and requested_visible),
    )
