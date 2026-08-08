"""Local W101 builder for editor infrastructure and Search ownership."""
from __future__ import annotations

from gi.repository import GLib, Pango

from calamus_application_components import (
    EditorCompositionInput,
    EditorInfrastructureComponents,
    WidgetSignalConnection,
)
from calamus_history import TextHistory
from calamus_history_runtime import SnapshotHistoryRuntime
from calamus_logging import log_nonfatal
from calamus_search_gateway import SearchController
from calamus_search_view import SearchViewAdapter
from calamus_typewriter_runtime import TypewriterRuntime
from calamus_viewport_runtime import EditorViewportRuntime


def _connect(owner, signal_name, callback, *, after=False) -> WidgetSignalConnection:
    handler_id = (
        owner.connect_after(signal_name, callback)
        if after
        else owner.connect(signal_name, callback)
    )
    return WidgetSignalConnection(
        owner=owner,
        handler_id=int(handler_id),
        signal_name=signal_name,
        connected_after=bool(after),
    )


def build_editor_infrastructure(
    inputs: EditorCompositionInput,
) -> EditorInfrastructureComponents:
    history = TextHistory(max_steps=100)
    viewport_runtime = EditorViewportRuntime(
        inputs.text_view,
        inputs.scroller,
        GLib,
        log_nonfatal,
    )
    history_runtime = SnapshotHistoryRuntime(
        history,
        inputs.text_view,
        inputs.scroller,
        GLib,
        log_nonfatal,
        viewport_runtime=viewport_runtime,
    )
    typewriter_runtime = TypewriterRuntime(
        inputs.text_view,
        viewport_runtime,
        on_state_changed=inputs.on_typewriter_state_changed,
        log_nonfatal=log_nonfatal,
    )

    buffer = inputs.text_view.get_buffer()
    signal_connections = (
        _connect(buffer, "changed", inputs.on_buffer_changed),
        _connect(buffer, "begin-user-action", inputs.on_buffer_begin_user_action),
        _connect(buffer, "end-user-action", inputs.on_buffer_end_user_action),
        _connect(buffer, "notify::cursor-position", inputs.on_cursor_position_notify),
        _connect(inputs.text_view, "key-press-event", inputs.on_text_key_press),
        _connect(inputs.text_view, "key-release-event", inputs.on_text_key_release, after=True),
        _connect(inputs.text_view, "move-cursor", inputs.on_text_move_cursor, after=True),
        _connect(inputs.text_view, "button-press-event", inputs.on_text_button_press),
        _connect(inputs.text_view, "motion-notify-event", inputs.on_text_motion_notify, after=True),
        _connect(inputs.text_view, "button-release-event", inputs.on_text_button_release, after=True),
        _connect(inputs.text_view, "scroll-event", inputs.on_text_scroll),
        _connect(inputs.text_view, "focus-out-event", inputs.on_text_focus_out),
    )
    inputs.apply_wrap_policy()

    misspelling_tag = buffer.create_tag(
        "misspelled",
        underline=Pango.Underline.ERROR,
    )
    search_tag = buffer.create_tag(
        "search_highlight",
        background="#fff59d",
        foreground="#000000",
    )
    search_controller = SearchController(
        SearchViewAdapter(inputs.text_view, search_tag)
    )
    # The live shell projects an appearance-aware paragraph background onto
    # this tag.  Keep tag construction palette-free so Light/Dark/System can
    # be resolved by the active editor presentation context.
    current_line_tag = buffer.create_tag("current_line")

    return EditorInfrastructureComponents(
        history=history,
        viewport_runtime=viewport_runtime,
        history_runtime=history_runtime,
        typewriter_runtime=typewriter_runtime,
        search_controller=search_controller,
        misspelling_tag=misspelling_tag,
        search_tag=search_tag,
        current_line_tag=current_line_tag,
        signal_connections=signal_connections,
    )
