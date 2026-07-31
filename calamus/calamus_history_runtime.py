"""GtkTextBuffer boundary for Calamus' caret-aware snapshot history.

The history model remains GTK-free.  Viewport projection is delegated to the
single :class:`EditorViewportRuntime`, so Undo/Redo, navigation and Typewriter
Mode cannot race independent vertical-adjustment writers.
"""
from __future__ import annotations

from typing import Any, Callable

from calamus_history import HistoryState, TextHistory
from calamus_viewport import compute_vertical_reveal as _compute_vertical_reveal
from calamus_viewport_runtime import EditorViewportRuntime


def compute_vertical_reveal(
    *,
    caret_y: float,
    caret_height: float,
    visible_y: float,
    visible_height: float,
    lower: float,
    upper: float,
    page_size: float,
    top_margin: float = 0.0,
    within_margin: float = 0.15,
    center_if_outside: bool = True,
) -> float | None:
    """W95-compatible public projection function, now GTK-free."""
    return _compute_vertical_reveal(
        caret_y=caret_y,
        caret_height=caret_height,
        visible_y=visible_y,
        visible_height=visible_height,
        lower=lower,
        upper=upper,
        page_size=page_size,
        top_margin=top_margin,
        within_margin=within_margin,
        center_if_outside=center_if_outside,
    )


def capture_buffer_state(text_view: Any) -> HistoryState:
    buffer = text_view.get_buffer()
    start, end = buffer.get_bounds()
    text = buffer.get_text(start, end, True)
    insert = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()
    bound = buffer.get_iter_at_mark(buffer.get_selection_bound()).get_offset()
    return HistoryState(text, insert, bound)


def restore_buffer_state(text_view: Any, state: HistoryState) -> None:
    buffer = text_view.get_buffer()
    buffer.set_text(state.text)
    insert = buffer.get_iter_at_offset(state.insert_offset)
    bound = buffer.get_iter_at_offset(state.selection_bound_offset)
    # Preserve mark identity and selection direction. get_selection_bounds()
    # would sort the endpoints and lose this information.
    buffer.select_range(insert, bound)


class SnapshotHistoryRuntime:
    """Coordinate exact snapshots and delegate presentation to one viewport."""

    def __init__(
        self,
        history: TextHistory,
        text_view: Any,
        scroller: Any,
        glib: Any,
        log_nonfatal: Callable[[str, BaseException], None],
        *,
        debounce_ms: int = 600,
        viewport_runtime: EditorViewportRuntime | None = None,
    ) -> None:
        self.history = history
        self.text_view = text_view
        self.scroller = scroller
        self.glib = glib
        self.log_nonfatal = log_nonfatal
        self.debounce_ms = debounce_ms
        self.snapshot_source: int | None = None
        self.before_state: HistoryState | None = None
        self.after_state: HistoryState | None = None
        self.reveal_margin = 0.15
        self.center_if_outside = False
        self._owns_viewport = viewport_runtime is None
        self.viewport_runtime = viewport_runtime or EditorViewportRuntime(
            text_view,
            scroller,
            glib,
            log_nonfatal,
        )

    # Compatibility properties retained for the published W95 gates and tests.
    @property
    def scroll_source(self) -> int | None:
        return self.viewport_runtime.scroll_source

    @property
    def reveal_pending(self) -> bool:
        return self.viewport_runtime.reveal_pending

    @property
    def applying_adjustment(self) -> bool:
        return self.viewport_runtime.applying_adjustment

    def capture(self) -> HistoryState:
        return capture_buffer_state(self.text_view)

    def reset(self) -> None:
        self.cancel_snapshot()
        self.before_state = None
        self.after_state = None
        self.history.reset(self.capture())

    def begin_user_action(self, enabled: bool = True) -> None:
        if enabled and self.before_state is None:
            self.before_state = self.capture()

    def end_user_action(self, enabled: bool = True) -> None:
        if not enabled:
            return
        if self.before_state is None:
            self.before_state = self.history.current or self.capture()
        self.after_state = self.capture()
        self._schedule_snapshot()

    def observe_changed(self, enabled: bool = True) -> None:
        """Fallback for a producer that changes text outside a user action."""
        if not enabled:
            return
        if self.before_state is None:
            self.before_state = self.history.current or self.capture()
        self.after_state = self.capture()
        self._schedule_snapshot()

    def _schedule_snapshot(self) -> None:
        self.cancel_snapshot()
        self.snapshot_source = self.glib.timeout_add(
            self.debounce_ms,
            self._commit_scheduled,
        )

    def _commit_scheduled(self) -> bool:
        self.snapshot_source = None
        self.flush()
        return False

    def flush(self) -> bool:
        self.cancel_snapshot()
        before = self.before_state
        after = self.after_state
        self.before_state = None
        self.after_state = None
        if before is not None:
            self.history.replace_current_view_state(before)
        if after is None:
            return False
        return self.history.commit(after)

    def prepare_command(self) -> None:
        self.flush()
        self.history.replace_current_view_state(self.capture())
        self.before_state = self.capture()

    def finalize_command(self) -> bool:
        self.after_state = self.capture()
        return self.flush()

    def sync_current_view_state(self) -> bool:
        return self.history.replace_current_view_state(self.capture())

    def undo_target(self) -> HistoryState | None:
        self.flush()
        return self.history.undo(self.capture())

    def redo_target(self) -> HistoryState | None:
        self.flush()
        return self.history.redo()

    def cancel_snapshot(self) -> None:
        if self.snapshot_source is not None:
            try:
                self.glib.source_remove(self.snapshot_source)
            except Exception as error:
                self.log_nonfatal("history snapshot source removal failed", error)
            self.snapshot_source = None


    def _on_view_geometry_changed(self, *_args: Any) -> None:
        """Compatibility gateway retained for the published W95 contract."""
        if self.viewport_runtime.reveal_pending:
            self.viewport_runtime._schedule_idle()

    def queue_scroll_to_insert(
        self,
        margin: float = 0.15,
        *,
        center_if_outside: bool = False,
    ) -> bool:
        self.reveal_margin = float(margin)
        self.center_if_outside = bool(center_if_outside)
        return self.viewport_runtime.queue_visible_to_insert(
            margin,
            center_if_outside=center_if_outside,
        )

    def cancel_scroll(self) -> None:
        self.viewport_runtime.cancel()

    def shutdown(self) -> None:
        self.cancel_snapshot()
        self.cancel_scroll()
        if self._owns_viewport:
            self.viewport_runtime.shutdown()
