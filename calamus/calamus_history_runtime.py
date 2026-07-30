"""GtkTextBuffer boundary for Calamus' caret-aware snapshot history.

The data model remains GTK-free in :mod:`calamus_history`.  This adapter reads
and restores the standard insert/selection-bound marks.  Viewport projection is
separate from history state: one owned reveal request computes the vertical
adjustment from the restored insert mark after GTK geometry is available.
"""
from __future__ import annotations

from typing import Any, Callable

from calamus_history import HistoryState, TextHistory


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
    """Return a clamped adjustment value, or ``None`` when already visible.

    This is the GTK-free projection rule used by the runtime.  It follows the
    mature-editor ordering used by VS Code, Pulsar and GNOME Text Editor:
    restore semantic cursor state first, then reveal it through the view's own
    scroll model.  No text diff and no guessed timeout participate.
    """
    if not 0.0 <= within_margin <= 0.5:
        raise ValueError("within_margin must be between 0.0 and 0.5")
    if visible_height <= 0 or page_size <= 0:
        return None

    caret_height = max(1.0, float(caret_height))
    visible_height = float(visible_height)
    margin_px = visible_height * within_margin
    safe_top = float(visible_y) + margin_px
    safe_bottom = float(visible_y) + visible_height - margin_px
    caret_top = float(caret_y)
    caret_bottom = caret_top + caret_height
    if caret_top >= safe_top and caret_bottom <= safe_bottom:
        return None

    if center_if_outside:
        desired = caret_top + (caret_height / 2.0) - (float(page_size) / 2.0)
    elif caret_top < safe_top:
        desired = caret_top - margin_px
    else:
        desired = caret_bottom - float(page_size) + margin_px
    desired += max(0.0, float(top_margin))

    minimum = float(lower)
    maximum = max(minimum, float(upper) - float(page_size))
    return max(minimum, min(desired, maximum))


class SnapshotHistoryRuntime:
    """Coordinate snapshots and one geometry-aware viewport reveal request."""

    def __init__(
        self,
        history: TextHistory,
        text_view: Any,
        scroller: Any,
        glib: Any,
        log_nonfatal: Callable[[str, BaseException], None],
        *,
        debounce_ms: int = 600,
    ) -> None:
        self.history = history
        self.text_view = text_view
        self.scroller = scroller
        self.glib = glib
        self.log_nonfatal = log_nonfatal
        self.debounce_ms = debounce_ms
        self.snapshot_source: int | None = None
        self.scroll_source: int | None = None
        self.reveal_pending = False
        self.reveal_margin = 0.15
        self.reveal_center = False
        self.before_state: HistoryState | None = None
        self.after_state: HistoryState | None = None
        self._adjustment = self.scroller.get_vadjustment()
        self._adjustment_handler = None
        self._allocation_handler = None
        if hasattr(self._adjustment, "connect"):
            self._adjustment_handler = self._adjustment.connect(
                "changed", self._on_view_geometry_changed
            )
        if hasattr(self.text_view, "connect"):
            self._allocation_handler = self.text_view.connect(
                "size-allocate", self._on_view_geometry_changed
            )

    def capture(self) -> HistoryState:
        return capture_buffer_state(self.text_view)

    def reset(self) -> None:
        self.cancel_snapshot()
        self.before_state = None
        self.after_state = None
        self.history.reset(self.capture())

    def begin_user_action(self, enabled: bool = True) -> None:
        if not enabled:
            return
        if self.before_state is None:
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
            self.debounce_ms, self._commit_scheduled
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
        if self.reveal_pending and self.scroll_source is None:
            self._schedule_reveal_idle()

    def _schedule_reveal_idle(self) -> None:
        try:
            self.scroll_source = self.glib.idle_add(
                self._reveal_insert_once, priority=self.glib.PRIORITY_LOW
            )
        except TypeError:
            self.scroll_source = self.glib.idle_add(self._reveal_insert_once)

    def _reveal_geometry_ready(self, caret_bottom: float, page_size: float) -> bool:
        upper = float(self._adjustment.get_upper())
        return page_size > 1.0 and upper + 1.0 >= caret_bottom

    def _reveal_insert_once(self) -> bool:
        self.scroll_source = None
        if not self.reveal_pending:
            return False
        try:
            buffer = self.text_view.get_buffer()
            iterator = buffer.get_iter_at_mark(buffer.get_insert())
            location = self.text_view.get_iter_location(iterator)
            visible = self.text_view.get_visible_rect()
            page_size = float(self._adjustment.get_page_size())
            caret_bottom = float(location.y) + max(1.0, float(location.height))
            if not self._reveal_geometry_ready(caret_bottom, page_size):
                # Keep the request pending. GtkAdjustment::changed or the next
                # size allocation will schedule the same owned request again.
                return False
            top_margin = (
                float(self.text_view.get_top_margin())
                if hasattr(self.text_view, "get_top_margin")
                else 0.0
            )
            target = compute_vertical_reveal(
                caret_y=location.y,
                caret_height=location.height,
                visible_y=visible.y,
                visible_height=visible.height,
                lower=self._adjustment.get_lower(),
                upper=self._adjustment.get_upper(),
                page_size=page_size,
                top_margin=top_margin,
                within_margin=self.reveal_margin,
                center_if_outside=self.reveal_center,
            )
            if target is not None:
                self._adjustment.set_value(target)
            self.reveal_pending = False
        except Exception as error:
            self.reveal_pending = False
            self.log_nonfatal("history viewport restoration failed", error)
        return False

    def queue_scroll_to_insert(
        self, margin: float = 0.15, *, center_if_outside: bool = False
    ) -> bool:
        """Reveal the insert mark through one replaceable view request.

        The request is resolved only when the vertical adjustment can represent
        the restored caret.  Geometry notifications, not elapsed time, trigger a
        retry if the TextView has not finished relayout after a bulk restore.
        """
        if not 0.0 <= float(margin) <= 0.5:
            raise ValueError("margin must be between 0.0 and 0.5")
        self.cancel_scroll()
        self.reveal_pending = True
        self.reveal_margin = float(margin)
        self.reveal_center = bool(center_if_outside)
        self._schedule_reveal_idle()
        return False

    def cancel_scroll(self) -> None:
        if self.scroll_source is not None:
            try:
                self.glib.source_remove(self.scroll_source)
            except Exception as error:
                self.log_nonfatal("history scroll source removal failed", error)
            self.scroll_source = None
        self.reveal_pending = False

    def shutdown(self) -> None:
        self.cancel_snapshot()
        self.cancel_scroll()
        if self._adjustment_handler is not None and hasattr(self._adjustment, "disconnect"):
            try:
                self._adjustment.disconnect(self._adjustment_handler)
            except Exception as error:
                self.log_nonfatal("history adjustment disconnect failed", error)
            self._adjustment_handler = None
        if self._allocation_handler is not None and hasattr(self.text_view, "disconnect"):
            try:
                self.text_view.disconnect(self._allocation_handler)
            except Exception as error:
                self.log_nonfatal("history allocation disconnect failed", error)
            self._allocation_handler = None
