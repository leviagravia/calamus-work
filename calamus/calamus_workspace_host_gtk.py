"""GTK presentation adapter for W107 Workspace host ports."""
from __future__ import annotations

from calamus_dialogs import (
    choose_workspace_folder,
    confirm_move_workspace_item_to_trash,
    prompt_new_workspace_folder,
    prompt_new_workspace_text_file,
    prompt_rename_workspace_item,
    show_error,
)
from calamus_menu_model import recent_workspace_rows


class WorkspaceHostGtkAdapter:
    """Own only Workspace GTK dialog/menu presentation capabilities."""

    __slots__ = ("_parent", "_menu_ui_adapter")

    def __init__(self, parent, menu_ui_adapter=None) -> None:
        self._parent = parent
        self._menu_ui_adapter = menu_ui_adapter

    def render_recent_workspaces(self, paths: tuple[str, ...]):
        if self._menu_ui_adapter is not None:
            return self._menu_ui_adapter.render_dynamic(
                "recent-workspaces", recent_workspace_rows(paths)
            )
        return None

    def choose_root(self, current_root):
        return choose_workspace_folder(self._parent, current_root)

    def prompt_new_text_file(self, destination):
        return prompt_new_workspace_text_file(self._parent, destination)

    def prompt_new_folder(self, destination):
        return prompt_new_workspace_folder(self._parent, destination)

    def prompt_rename_item(self, name: str, is_directory: bool):
        return prompt_rename_workspace_item(
            self._parent, name, is_directory=is_directory
        )

    def confirm_trash(self, source_name: str, is_directory: bool, active_document_affected: bool):
        return confirm_move_workspace_item_to_trash(
            self._parent,
            source_name,
            is_directory=is_directory,
            active_document_affected=active_document_affected,
        )

    def show_error(self, message: str):
        return show_error(self._parent, message)
