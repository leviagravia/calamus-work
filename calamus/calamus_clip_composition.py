"""Local W101 builders for the right-panel host and Clip Collection."""
from __future__ import annotations

from calamus_application_components import (
    ClipCollectionComponents,
    ClipCollectionCompositionInput,
    RightPanelHostInput,
    SetOnceReference,
)
from calamus_clip_collection import ClipCollectionController
from calamus_clip_panel import build_clip_collection_view
from calamus_clip_runtime import (
    ClipCollectionRuntime,
    copy_clip_body,
    insert_clip_expansion_through_gateway,
    selected_document_text_from_view,
)
from calamus_clips import MarkdownClipStore
from calamus_dialogs import show_error, show_info
from calamus_logging import log_nonfatal
from calamus_right_panel import RightPanelHost


def build_right_panel_host(inputs: RightPanelHostInput) -> RightPanelHost:
    return RightPanelHost(
        inputs.body_paned,
        inputs.queue_wrap_reflow,
    )


def build_clip_collection_components(
    inputs: ClipCollectionCompositionInput,
) -> ClipCollectionComponents:
    runtime_reference = SetOnceReference("clip-collection-runtime")
    view = build_clip_collection_view(
        on_search=lambda query: runtime_reference.require().on_search(query),
        on_new=lambda *_: runtime_reference.require().on_new(),
        on_capture=lambda *_: runtime_reference.require().on_capture(),
        on_insert=lambda *_: runtime_reference.require().on_insert(),
        on_copy=lambda *_: runtime_reference.require().on_copy(),
        on_edit=lambda *_: runtime_reference.require().on_edit(),
        on_duplicate=lambda *_: runtime_reference.require().on_duplicate(),
        on_delete=lambda *_: runtime_reference.require().on_delete(),
        on_refresh=lambda *_: runtime_reference.require().on_refresh(),
        on_open_file=lambda *_: runtime_reference.require().on_open_file(),
        on_activate=lambda: runtime_reference.require().on_insert(),
        show_title=False,
    )
    controller = ClipCollectionController(
        MarkdownClipStore(inputs.config_dir),
        view,
    )
    runtime = ClipCollectionRuntime(
        inputs.dialog_parent,
        controller,
        selected_text_provider=lambda: selected_document_text_from_view(inputs.text_view),
        insert_expansion=lambda text, offset: insert_clip_expansion_through_gateway(
            inputs.text_view,
            text,
            offset,
            execute_command=inputs.execute_command,
            get_cursor_offset=inputs.get_cursor_offset,
            set_cursor_offset=inputs.set_cursor_offset,
            sync_history_view_state=inputs.sync_history_view_state,
            queue_insert_scroll=inputs.queue_insert_scroll,
        ),
        copy_text=copy_clip_body,
        show_error=lambda message: show_error(inputs.dialog_parent, message),
        show_info=lambda message: show_info(inputs.dialog_parent, message),
        on_changed=lambda: inputs.publish_invalidation(inputs.clip_invalidation_reason),
    )
    runtime_reference.set(runtime)
    if not controller.load():
        log_nonfatal(
            "clip-collection-load",
            RuntimeError(controller.last_error or "Clip Collection could not be loaded."),
        )
    return ClipCollectionComponents(
        view=view,
        controller=controller,
        runtime=runtime,
    )
