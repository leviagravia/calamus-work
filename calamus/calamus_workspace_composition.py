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
from calamus_workspace_mutation import WorkspaceMutationController, WorkspaceMutationRuntime
from calamus_workspace_panel import WorkspacePanelRuntime, WorkspacePanelView


def build_workspace_components(
    inputs: WorkspaceCompositionInput,
) -> WorkspaceComponents:
    application_reference = SetOnceReference("workspace-application-runtime")
    panel_reference = SetOnceReference("workspace-panel-runtime")

    controller = WorkspaceController()
    panel_view = WorkspacePanelView(
        on_hide=lambda: panel_reference.require().hide(),
        on_new_text_file=inputs.on_new_text_file,
        on_new_folder=inputs.on_new_folder,
        on_rename_item=inputs.on_rename_item,
        on_duplicate_file=inputs.on_duplicate_file,
        on_move_to_trash=inputs.on_move_to_trash,
        on_choose_root=inputs.on_choose_root,
        on_refresh=inputs.on_refresh,
        on_reveal=inputs.on_reveal,
        on_activate_item=lambda item: application_reference.require().activate_item(item),
    )
    application_runtime = WorkspaceApplicationRuntime(
        controller,
        panel_view,
        inputs.state,
        may_continue=inputs.may_continue,
        open_document=inputs.open_document,
        open_external=open_external_path,
        reveal_external=reveal_in_file_manager,
        save_settings=inputs.save_settings,
        report_error=inputs.report_error,
        on_root_changed=inputs.on_root_changed,
        on_recent_changed=inputs.on_recent_changed,
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
        capture_path_references=inputs.capture_path_references,
        reconcile_rename=inputs.reconcile_rename,
        current_document_path=inputs.current_document_path,
        confirm_trash=inputs.confirm_trash,
        reconcile_trash=inputs.reconcile_trash,
    )
    panel_host = inputs.left_panel_host.register("workspace", panel_view.widget)
    panel_runtime = WorkspacePanelRuntime(
        panel_host,
        panel_view,
        inputs.workspace_menu_item,
        inputs.text_view.grab_focus,
        inputs.on_visibility_changed,
    )
    panel_reference.set(panel_runtime)

    return WorkspaceComponents(
        controller=controller,
        panel_view=panel_view,
        application_runtime=application_runtime,
        mutation_controller=mutation_controller,
        mutation_runtime=mutation_runtime,
        panel_host=panel_host,
        panel_runtime=panel_runtime,
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
