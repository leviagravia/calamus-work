"""GTK-free editor transaction authority for Calamus.

W103 centralizes logical edit grouping, rollback, native-edit observation and
Undo/Redo restoration without importing GTK.  Concrete GtkTextBuffer operations
are supplied through an adapter object.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from calamus_history import HistoryState


class EditorChangeKind(str, Enum):
    REPLACEMENT = "replacement"
    PROGRAMMATIC = "programmatic"
    NATIVE = "native"


@dataclass(frozen=True)
class EditorTransactionResult:
    label: str
    before: HistoryState
    after: HistoryState
    changed: bool
    rolled_back: bool = False
    restored_history: bool = False


class EditorTransactionController:
    """Single logical transaction authority for one Calamus editor buffer."""

    __slots__ = (
        "session",
        "session_controller",
        "history_runtime",
        "buffer_adapter",
        "_programmatic_depth",
        "_restoring_depth",
    )

    def __init__(
        self,
        *,
        session: Any,
        session_controller: Any,
        history_runtime: Any,
        buffer_adapter: Any,
    ) -> None:
        for name, value in (
            ("session", session),
            ("session_controller", session_controller),
            ("history_runtime", history_runtime),
            ("buffer_adapter", buffer_adapter),
        ):
            if value is None:
                raise TypeError(f"{name} is required")
        self.session = session
        self.session_controller = session_controller
        self.history_runtime = history_runtime
        self.buffer_adapter = buffer_adapter
        self._programmatic_depth = 0
        self._restoring_depth = 0

    @property
    def programmatic_active(self) -> bool:
        return self._programmatic_depth > 0

    @property
    def restoring(self) -> bool:
        return self._restoring_depth > 0

    def begin_user_action(self, enabled: bool = True) -> bool:
        accepted = bool(enabled) and not self.restoring and not self.session.loading
        self.history_runtime.begin_user_action(accepted)
        return accepted

    def end_user_action(self, enabled: bool = True) -> bool:
        accepted = bool(enabled) and not self.restoring and not self.session.loading
        self.history_runtime.end_user_action(accepted)
        return accepted

    def observe_buffer_change(self) -> EditorChangeKind:
        if self.restoring or self.session.loading:
            return EditorChangeKind.REPLACEMENT
        if self.programmatic_active:
            return EditorChangeKind.PROGRAMMATIC
        if self.session_controller.observe_buffer_change():
            self.history_runtime.observe_changed(True)
            return EditorChangeKind.NATIVE
        return EditorChangeKind.REPLACEMENT

    def sync_current_view_state(self) -> bool:
        return self.history_runtime.sync_current_view_state()

    def cut_clipboard(self, clipboard: Any, editable: bool = True) -> None:
        """Invoke GTK-native Cut through the buffer boundary.

        GtkTextBuffer emits its normal user-action signals; those signals are
        the native transaction boundary and are observed by begin/end hooks.
        """
        self.buffer_adapter.cut_clipboard(clipboard, editable)

    def paste_clipboard(self, clipboard: Any, editable: bool = True) -> None:
        """Invoke GTK-native Paste through the buffer boundary."""
        self.buffer_adapter.paste_clipboard(clipboard, editable)

    def schedule_native_snapshot(self, enabled: bool = True) -> None:
        accepted = bool(enabled) and not self.restoring and not self.programmatic_active and not self.session.loading
        self.history_runtime.observe_changed(accepted)

    def flush(self) -> bool:
        return self.history_runtime.flush()

    def reset(self) -> None:
        self.history_runtime.reset()

    def finalize_prepared_command(
        self,
        label: str,
        *,
        select_range: tuple[int, int] | None = None,
    ) -> EditorTransactionResult:
        before = self.history_runtime.before_state or self.history_runtime.history.current or self.buffer_adapter.capture()
        if select_range is not None:
            self.buffer_adapter.select_range(*select_range)
        after = self.buffer_adapter.capture()
        changed = before.text != after.text
        self.history_runtime.finalize_command()
        if changed:
            self.session.mark_modified(after.text)
        return EditorTransactionResult(label, before, after, changed)

    def execute_command(
        self,
        label: str,
        edit_func: Callable[[Any], Any],
        *,
        select_range: tuple[int, int] | None = None,
    ) -> EditorTransactionResult:
        if self.programmatic_active:
            raise RuntimeError("nested editor transactions are not allowed")
        if not isinstance(label, str) or not label:
            raise ValueError("transaction label must be non-empty")
        if not callable(edit_func):
            raise TypeError("edit_func must be callable")

        checkpoint = self.history_runtime.prepare_command()
        before = self.buffer_adapter.capture()
        self._programmatic_depth += 1
        user_action_started = False
        try:
            self.buffer_adapter.begin_user_action()
            user_action_started = True
            self.buffer_adapter.apply_callback(edit_func)
            self.buffer_adapter.end_user_action()
            user_action_started = False

            after = self.buffer_adapter.capture()
            changed = after.text != before.text
            if not changed:
                self.history_runtime.flush()
                return EditorTransactionResult(label, before, after, False)

            if select_range is not None:
                self.buffer_adapter.select_range(*select_range)
                after = self.buffer_adapter.capture()
            self.history_runtime.finalize_command()
            self.session.mark_modified(after.text)
            return EditorTransactionResult(label, before, after, True)
        except BaseException:
            if user_action_started:
                try:
                    self.buffer_adapter.end_user_action()
                except BaseException:
                    pass
            self._rollback_failed_command(before, checkpoint)
            raise
        finally:
            self._programmatic_depth -= 1
            if self._programmatic_depth < 0:
                self._programmatic_depth = 0
                raise RuntimeError("editor transaction depth underflow")

    def _rollback_failed_command(self, before: HistoryState, checkpoint: Any) -> None:
        self._restoring_depth += 1
        try:
            with self.session.replacement():
                self.buffer_adapter.restore(before)
            self.history_runtime.restore_checkpoint(checkpoint)
        finally:
            self._restoring_depth -= 1

    def restore_history_state(
        self,
        state: HistoryState,
        *,
        label: str,
    ) -> EditorTransactionResult:
        if not isinstance(state, HistoryState):
            raise TypeError("state must be HistoryState")
        before = self.buffer_adapter.capture()
        checkpoint = self.history_runtime.checkpoint()
        self._restoring_depth += 1
        try:
            with self.session.replacement():
                self.buffer_adapter.restore(state)
        except BaseException:
            try:
                with self.session.replacement():
                    self.buffer_adapter.restore(before)
            finally:
                self.history_runtime.restore_checkpoint(checkpoint)
            raise
        finally:
            self._restoring_depth -= 1
        after = self.buffer_adapter.capture()
        self.session.mark_modified(after.text)
        return EditorTransactionResult(
            label,
            before,
            after,
            before.text != after.text or before.insert_offset != after.insert_offset
            or before.selection_bound_offset != after.selection_bound_offset,
            restored_history=True,
        )

    def undo(self) -> EditorTransactionResult | None:
        checkpoint = self.history_runtime.checkpoint()
        before = self.buffer_adapter.capture()
        state = self.history_runtime.undo_target()
        if state is None:
            return None
        try:
            return self.restore_history_state(state, label="Undo")
        except BaseException:
            self.history_runtime.restore_checkpoint(checkpoint)
            self._restore_buffer_after_history_failure(before)
            raise

    def redo(self) -> EditorTransactionResult | None:
        checkpoint = self.history_runtime.checkpoint()
        before = self.buffer_adapter.capture()
        state = self.history_runtime.redo_target()
        if state is None:
            return None
        try:
            return self.restore_history_state(state, label="Redo")
        except BaseException:
            self.history_runtime.restore_checkpoint(checkpoint)
            self._restore_buffer_after_history_failure(before)
            raise

    def _restore_buffer_after_history_failure(self, before: HistoryState) -> None:
        self._restoring_depth += 1
        try:
            with self.session.replacement():
                self.buffer_adapter.restore(before)
        finally:
            self._restoring_depth -= 1
