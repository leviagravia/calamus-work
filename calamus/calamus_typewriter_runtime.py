"""GTK event classifier for Calamus Typewriter Mode.

The runtime owns mode state and event semantics, but never writes a
GtkAdjustment or mutates the document. All projection is delegated to the
single EditorViewportRuntime.
"""
from __future__ import annotations

from typing import Any, Callable

from calamus_typewriter import TypewriterEventKind, TypewriterSettings


class TypewriterRuntime:
    """Classify semantic movement versus pointer/manual viewport ownership."""

    _SEMANTIC_RESUME = {
        TypewriterEventKind.EDIT,
        TypewriterEventKind.KEYBOARD,
        TypewriterEventKind.HISTORY,
        TypewriterEventKind.STRUCTURAL,
    }

    def __init__(
        self,
        text_view: Any,
        viewport_runtime: Any,
        *,
        settings: TypewriterSettings | None = None,
        on_state_changed: Callable[[bool], None] | None = None,
        log_nonfatal: Callable[[str, BaseException], None] | None = None,
    ) -> None:
        self.text_view = text_view
        self.viewport_runtime = viewport_runtime
        self.settings = settings or TypewriterSettings()
        self.on_state_changed = on_state_changed or (lambda _enabled: None)
        self.log_nonfatal = log_nonfatal or (lambda _message, _error: None)

        self.enabled = False
        self.reached = False
        self.pointer_down = False
        self.manual_scroll_suspended = False
        self._semantic_input_depth = 0
        self._keyboard_event_active = False
        self._shutdown = False

        self._adjustment_callback = self.viewport_runtime.connect_external_adjustment(
            self._on_external_adjustment
        )
        self._geometry_callback = self.viewport_runtime.connect_geometry_changed(
            self._on_geometry_changed
        )

    def set_enabled(self, enabled: bool) -> bool:
        enabled = bool(enabled)
        if self._shutdown or enabled == self.enabled:
            return self.enabled
        self.viewport_runtime.cancel_projection()
        self.enabled = enabled
        self.reached = False
        self.pointer_down = False
        self.manual_scroll_suspended = False
        self._semantic_input_depth = 0
        self._keyboard_event_active = False
        if enabled:
            self.viewport_runtime.acquire_runway(self, self.settings)
            self.request(TypewriterEventKind.ACTIVATE, force=True)
        else:
            self.viewport_runtime.release_runway(self)
        self.on_state_changed(self.enabled)
        return self.enabled

    def toggle(self) -> bool:
        return self.set_enabled(not self.enabled)

    def on_document_replaced(self) -> None:
        """Reset the latch when New/Open replaces the document authority."""
        self.reached = False
        self.manual_scroll_suspended = False
        self.pointer_down = False
        if self.enabled:
            self.viewport_runtime.acquire_runway(self, self.settings)
            self.request(TypewriterEventKind.ACTIVATE, force=True)

    def request(
        self,
        kind: TypewriterEventKind,
        *,
        force: bool = False,
        allow_selection: bool = False,
    ) -> bool:
        if self._shutdown or not self.enabled:
            return False

        if self.pointer_down:
            return False
        if self._has_selection() and not allow_selection:
            self.viewport_runtime.cancel_projection()
            return False
        if (
            not force
            and hasattr(self.text_view, "has_focus")
            and not self.text_view.has_focus()
        ):
            return False
        if kind in self._SEMANTIC_RESUME:
            self.manual_scroll_suspended = False
        if self.manual_scroll_suspended and not force:
            return False

        self.viewport_runtime.acquire_runway(self, self.settings)
        self.viewport_runtime.queue_typewriter_to_insert(
            self.settings,
            reached=self.reached,
            on_reached=self._set_reached,
        )
        return True

    def on_begin_user_action(self) -> None:
        if not self.enabled:
            return
        self._semantic_input_depth += 1
        if not self.pointer_down:
            self.manual_scroll_suspended = False

    def on_end_user_action(self) -> None:
        if not self.enabled:
            return
        self._semantic_input_depth = max(0, self._semantic_input_depth - 1)
        if self._semantic_input_depth == 0:
            self.request(TypewriterEventKind.EDIT)

    def on_edit(self) -> bool:
        return self.request(TypewriterEventKind.EDIT)

    def on_key_press(self, *_args: Any) -> bool:
        if self.enabled and not self.pointer_down:
            self._keyboard_event_active = True
            self.manual_scroll_suspended = False
        return False

    def on_key_release(self, *_args: Any) -> bool:
        self._keyboard_event_active = False
        return False

    def on_keyboard(self) -> bool:
        return self.request(TypewriterEventKind.KEYBOARD)

    def on_history(self) -> bool:
        return self.request(
            TypewriterEventKind.HISTORY,
            force=True,
            allow_selection=True,
        )

    def on_structural_navigation(self) -> bool:
        return self.request(TypewriterEventKind.STRUCTURAL)

    def on_button_press(self, *_args: Any) -> bool:
        if self.enabled:
            self.pointer_down = True
            self.manual_scroll_suspended = True
            self.viewport_runtime.cancel_projection()
        return False

    def on_button_release(self, *_args: Any) -> bool:
        self.pointer_down = False
        # The pointer-selected viewport remains authoritative until a subsequent
        # edit, keyboard movement, Undo/Redo or explicit structural navigation.
        return False

    def on_motion(self, *_args: Any) -> bool:
        return False

    def on_scroll(self, *_args: Any) -> bool:
        if self.enabled:
            self.manual_scroll_suspended = True
            self.viewport_runtime.cancel_projection()
        return False

    def on_focus_out(self, *_args: Any) -> bool:
        if self.enabled:
            self.manual_scroll_suspended = True
            self.viewport_runtime.cancel_projection()
        return False

    def _on_external_adjustment(self) -> None:
        if not self.enabled:
            return
        # Native GtkTextView follow-caret scrolling can occur during a semantic
        # key/edit action and before our owned projection runs. Do not mistake it
        # for manual scrolling. Explicit wheel/trackpad events are caught above;
        # scrollbar drags are caught once no semantic projection is pending.
        if (
            self.pointer_down
            or self._semantic_input_depth > 0
            or self._keyboard_event_active
            or self.viewport_runtime.has_pending_projection
        ):
            return
        self.manual_scroll_suspended = True
        self.viewport_runtime.cancel_projection()

    def _on_geometry_changed(self) -> None:
        if (
            self.enabled
            and self.reached
            and not self.pointer_down
            and not self.manual_scroll_suspended
        ):
            self.request(TypewriterEventKind.RESIZE)

    def _has_selection(self) -> bool:
        buffer = self.text_view.get_buffer()
        if hasattr(buffer, "get_has_selection"):
            return bool(buffer.get_has_selection())
        bounds = buffer.get_selection_bounds()
        if not bounds:
            return False
        if isinstance(bounds[0], bool):
            return bool(bounds[0])
        return len(bounds) >= 2 and bounds[0].get_offset() != bounds[1].get_offset()

    def _set_reached(self, reached: bool) -> None:
        self.reached = bool(reached)

    def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        self.viewport_runtime.cancel_projection()
        if self.enabled:
            self.viewport_runtime.release_runway(self)
        self.enabled = False
        self.viewport_runtime.disconnect_callback(self._adjustment_callback)
        self.viewport_runtime.disconnect_callback(self._geometry_callback)
