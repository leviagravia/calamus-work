"""W107 GTK-free Workspace application host orchestration.

The runtime never receives the application/window object.  GTK dialog and menu
projection are represented only by narrow capabilities in :class:`WorkspaceHostPorts`.
Existing Workspace controller/application/mutation runtimes remain the domain owners.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from calamus_workspace_identity import (
    WorkspacePathReferenceSnapshot,
    plan_workspace_rename_identity,
    plan_workspace_trash_identity,
)


@dataclass(frozen=True)
class WorkspaceHostPorts:
    render_recent_workspaces: Callable[[tuple[str, ...]], Any]
    choose_root: Callable[[str | None], str | None]
    prompt_new_text_file: Callable[[Any], tuple[str, str] | None]
    prompt_new_folder: Callable[[Any], str | None]
    prompt_rename_item: Callable[[str, bool], str | None]
    confirm_trash: Callable[[str, bool, bool], bool]
    show_error: Callable[[str], Any]
    document_text: Callable[[], str]
    research_context_changed: Callable[[], Any]
    update_title: Callable[[], Any]
    refresh_overview: Callable[[], Any]
    refresh_ui_state: Callable[[], Any]

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if not callable(value):
                raise TypeError(f"{name} must be callable")


class WorkspaceHostRuntime:
    """Own application-facing Workspace command flow through narrow ports."""

    __slots__ = (
        "_recent_workspaces",
        "_recent_files",
        "_favourites",
        "_application_state",
        "_document_session",
        "_ports",
        "_application_runtime",
        "_mutation_controller",
        "_mutation_runtime",
        "_panel_view",
        "_panel_runtime",
    )

    def __init__(
        self,
        *,
        recent_workspaces,
        recent_files,
        favourites,
        application_state,
        document_session,
        application_runtime,
        mutation_controller,
        mutation_runtime,
        panel_view,
        panel_runtime,
        ports: WorkspaceHostPorts,
    ) -> None:
        if not isinstance(ports, WorkspaceHostPorts):
            raise TypeError("ports must be WorkspaceHostPorts")
        self._recent_workspaces = recent_workspaces
        self._recent_files = recent_files
        self._favourites = favourites
        for name, value in (
            ("application_runtime", application_runtime),
            ("mutation_controller", mutation_controller),
            ("mutation_runtime", mutation_runtime),
            ("panel_view", panel_view),
            ("panel_runtime", panel_runtime),
        ):
            if value is None:
                raise TypeError(f"{name} is required")
        self._application_state = application_state
        self._document_session = document_session
        self._ports = ports
        self._application_runtime = application_runtime
        self._mutation_controller = mutation_controller
        self._mutation_runtime = mutation_runtime
        self._panel_view = panel_view
        self._panel_runtime = panel_runtime

    @property
    def root(self):
        return self._application_runtime.root

    def populate_recent_workspaces_menu(self):
        paths = tuple(self._recent_workspaces.visible())
        self._ports.render_recent_workspaces(paths)
        return paths

    def show_workspace_panel(self, *_):
        if not self.root:
            return self.on_select_workspace_folder()
        return self._panel_runtime.set_visible(True)

    def on_new_workspace_text_file(self, *_):
        selected = self._panel_view.selected_item()
        try:
            destination = self._mutation_controller.destination_for_selection(selected)
        except (OSError, TypeError, ValueError) as error:
            self._ports.show_error(str(error))
            return False
        request = self._ports.prompt_new_text_file(destination)
        if request is None:
            return False
        name, suffix = request
        return self.create_workspace_text_file(name, suffix)

    def create_workspace_text_file(self, name, suffix=".txt"):
        return self._mutation_runtime.create_new_text_file(
            self._panel_view.selected_item(),
            name,
            suffix=suffix,
        )

    def on_new_workspace_folder(self, *_):
        selected = self._panel_view.selected_item()
        try:
            destination = self._mutation_controller.destination_for_selection(selected)
        except (OSError, TypeError, ValueError) as error:
            self._ports.show_error(str(error))
            return False
        name = self._ports.prompt_new_folder(destination)
        if name is None:
            return False
        return self.create_workspace_folder(name)

    def create_workspace_folder(self, name):
        return self._mutation_runtime.create_new_folder(
            self._panel_view.selected_item(),
            name,
        )

    def on_duplicate_workspace_file(self, *_):
        return self._mutation_runtime.duplicate_text_file(
            self._panel_view.selected_item()
        )

    def on_move_workspace_item_to_trash(self, *_):
        return self._mutation_runtime.move_to_trash(
            self._panel_view.selected_item()
        )

    def confirm_workspace_trash(self, trash_plan, active_document_affected):
        return self._ports.confirm_trash(
            trash_plan.source_name,
            bool(trash_plan.source_is_directory),
            bool(active_document_affected),
        )

    def on_rename_workspace_item(self, *_):
        selected = self._panel_view.selected_item()
        if selected is None:
            self._ports.show_error("Select one Workspace file or folder to rename.")
            return False
        name = self._ports.prompt_rename_item(selected.name, bool(selected.is_directory))
        if name is None:
            return False
        return self.rename_workspace_item(name)

    def rename_workspace_item(self, name):
        return self._mutation_runtime.rename_item(
            self._panel_view.selected_item(), name
        )

    def capture_workspace_path_references(self):
        return WorkspacePathReferenceSnapshot(
            recent_files=tuple(self._recent_files.canonical()),
            favourites=tuple(self._favourites.canonical()),
        )

    def reconcile_workspace_rename(self, rename_plan, references):
        current_file = self._document_session.file_path
        identity = plan_workspace_rename_identity(
            current_file,
            references,
            rename_plan.source_path,
            rename_plan.target_path,
            source_is_directory=rename_plan.source_is_directory,
        )
        if identity.document_identity_changed:
            self._document_session.rebind_path(identity.current_file_after)
            self._ports.research_context_changed()
            self._ports.update_title()
            self._ports.refresh_overview()
        recent_saved = self._recent_files.save(list(identity.recent_files_after))
        favourites_saved = self._favourites.save(list(identity.favourites_after))
        state_saved = self._application_state.record_last_file(self._document_session.file_path)
        return bool(recent_saved and favourites_saved and state_saved)

    def reconcile_workspace_trash(self, trash_plan, references):
        current_file = self._document_session.file_path
        identity = plan_workspace_trash_identity(
            current_file,
            references,
            trash_plan.source_path,
            source_is_directory=trash_plan.source_is_directory,
        )
        if identity.active_document_detached:
            self._document_session.detach(self._ports.document_text())
            self._ports.research_context_changed()
            self._ports.update_title()
            self._ports.refresh_overview()
        recent_saved = self._recent_files.save(list(identity.recent_files_after))
        favourites_saved = self._favourites.save(list(identity.favourites_after))
        state_saved = self._application_state.record_last_file(self._document_session.file_path)
        return bool(recent_saved and favourites_saved and state_saved)

    def on_select_workspace_folder(self, *_):
        selected = self._ports.choose_root(self.root)
        if not selected:
            return False
        return self.activate_workspace_path(selected)

    def open_workspace_path(self, path):
        return self._application_runtime.open_root(path)

    def activate_workspace_path(self, path):
        if not self.open_workspace_path(path):
            return False
        self._panel_runtime.set_visible(True)
        self._panel_view.focus_tree()
        return True

    def on_close_workspace(self, *_):
        self._panel_runtime.hide()
        return self._application_runtime.close_root()

    def on_refresh_workspace(self, *_):
        return self._application_runtime.refresh()

    def on_reveal_workspace(self, *_):
        return self._application_runtime.reveal()

    def on_workspace_item_toggled(self, item):
        return self._panel_runtime.set_visible(bool(item.get_active()))

    def toggle_workspace_panel(self, *_):
        return self._panel_runtime.toggle()

    def on_workspace_root_changed(self, _root):
        self._ports.refresh_ui_state()

    def on_workspace_visibility_changed(self, visible):
        self._application_state.record_workspace_visible(bool(visible))
        self._ports.refresh_ui_state()
