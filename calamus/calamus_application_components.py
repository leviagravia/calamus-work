"""Typed ownership records for the W101 core application composition boundary.

These frozen bundles record construction ownership. They are not an application
context, dependency lookup mechanism, plugin API, or service container.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class SetOnceReference:
    """One local, named late reference for a bounded construction cycle."""

    __slots__ = ("_name", "_is_set", "_value")

    def __init__(self, name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("set-once reference name must be non-empty")
        self._name = name.strip()
        self._is_set = False
        self._value: Any = None

    def set(self, value: Any) -> None:
        if self._is_set:
            raise RuntimeError(f"set-once reference already assigned: {self._name}")
        if value is None:
            raise TypeError(f"set-once reference cannot own None: {self._name}")
        self._value = value
        self._is_set = True

    def require(self) -> Any:
        if not self._is_set:
            raise RuntimeError(f"set-once reference used before assignment: {self._name}")
        return self._value


@dataclass(frozen=True)
class WidgetSignalConnection:
    owner: Any
    handler_id: int
    signal_name: str
    connected_after: bool = False
    lifetime_authority: str = "gtk-widget-destruction"


@dataclass(frozen=True)
class EditorCompositionInput:
    text_view: Any
    scroller: Any
    on_typewriter_state_changed: Callable[..., Any]
    on_buffer_changed: Callable[..., Any]
    on_buffer_begin_user_action: Callable[..., Any]
    on_buffer_end_user_action: Callable[..., Any]
    on_cursor_position_notify: Callable[..., Any]
    on_text_key_press: Callable[..., Any]
    on_text_key_release: Callable[..., Any]
    on_text_move_cursor: Callable[..., Any]
    on_text_button_press: Callable[..., Any]
    on_text_motion_notify: Callable[..., Any]
    on_text_button_release: Callable[..., Any]
    on_text_scroll: Callable[..., Any]
    on_text_focus_out: Callable[..., Any]
    apply_wrap_policy: Callable[[], Any]


@dataclass(frozen=True)
class NavigatorCompositionInput:
    text_view: Any
    workspace_paned: Any
    queue_wrap_reflow: Callable[[], Any]
    navigator_menu_item: Any


@dataclass(frozen=True)
class WorkspaceCompositionInput:
    left_panel_host: Any
    state: Any
    workspace_menu_item: Any
    text_view: Any
    workspace_root: str | None
    workspace_visible: bool
    may_continue: Callable[[], bool]
    open_document: Callable[[str], bool]
    save_settings: Callable[..., bool]
    report_error: Callable[[str], None]
    on_root_changed: Callable[[str | None], None]
    on_recent_changed: Callable[[], None]
    on_visibility_changed: Callable[[bool], None]
    on_new_text_file: Callable[..., Any]
    on_new_folder: Callable[..., Any]
    on_rename_item: Callable[..., Any]
    on_duplicate_file: Callable[..., Any]
    on_move_to_trash: Callable[..., Any]
    on_choose_root: Callable[..., Any]
    on_refresh: Callable[..., Any]
    on_reveal: Callable[..., Any]
    capture_path_references: Callable[..., Any]
    reconcile_rename: Callable[..., bool]
    current_document_path: Callable[[], str | None]
    confirm_trash: Callable[..., bool]
    reconcile_trash: Callable[..., bool]


@dataclass(frozen=True)
class RightPanelHostInput:
    body_paned: Any
    queue_wrap_reflow: Callable[[], Any]


@dataclass(frozen=True)
class ClipCollectionCompositionInput:
    dialog_parent: Any
    config_dir: str
    text_view: Any
    execute_command: Callable[..., bool]
    get_cursor_offset: Callable[[], int]
    set_cursor_offset: Callable[[int], Any]
    sync_history_view_state: Callable[[], Any]
    queue_insert_scroll: Callable[..., Any]
    publish_invalidation: Callable[[Any], Any]
    clip_invalidation_reason: Any


@dataclass(frozen=True)
class EditorInfrastructureComponents:
    history: Any
    viewport_runtime: Any
    history_runtime: Any
    typewriter_runtime: Any
    search_controller: Any
    misspelling_tag: Any
    search_tag: Any
    current_line_tag: Any
    signal_connections: tuple[WidgetSignalConnection, ...]


@dataclass(frozen=True)
class NavigatorComponents:
    navigation_controller: Any
    left_panel_host: Any
    panel_view: Any
    panel_host: Any
    panel_runtime: Any


@dataclass(frozen=True)
class WorkspaceComponents:
    controller: Any
    panel_view: Any
    application_runtime: Any
    mutation_controller: Any
    mutation_runtime: Any
    panel_host: Any
    panel_runtime: Any
    startup_visible: bool


@dataclass(frozen=True)
class ClipCollectionComponents:
    view: Any
    controller: Any
    runtime: Any


@dataclass(frozen=True)
class CoreApplicationComponents:
    editor: EditorInfrastructureComponents
    navigator: NavigatorComponents
    workspace: WorkspaceComponents
    right_panel_host: Any
    clips: ClipCollectionComponents
    build_order: tuple[str, ...]
    composition_complete: bool
