"""Single GTK owner for Calamus editor viewport projection.

History, navigation and Typewriter Mode submit semantic intents to this object.
It alone writes the vertical adjustment and owns temporary editor runway.
Requests are replaceable and resolved from measured GTK geometry after layout;
there are no retry timers, line-height guesses or competing scrollers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from calamus_typewriter import TypewriterSettings, compute_typewriter_target, runway_margin
from calamus_viewport import ViewportGeometry, compute_vertical_reveal


@dataclass
class _ViewportRequest:
    mode: str
    margin: float = 0.15
    center_if_outside: bool = False
    typewriter_settings: TypewriterSettings | None = None
    typewriter_reached: bool = False
    on_typewriter_reached: Callable[[bool], None] | None = None


class EditorViewportRuntime:
    """Own one coalesced projection request and all vertical writes."""

    def __init__(
        self,
        text_view: Any,
        scroller: Any,
        glib: Any,
        log_nonfatal: Callable[[str, BaseException], None],
    ) -> None:
        self.text_view = text_view
        self.scroller = scroller
        self.glib = glib
        self.log_nonfatal = log_nonfatal
        self._adjustment = self.scroller.get_vadjustment()
        self.scroll_source: int | None = None
        self.reveal_pending = False
        self.applying_adjustment = False
        self._request: _ViewportRequest | None = None
        self._shutdown = False

        self._base_bottom_margin = int(self.text_view.get_bottom_margin()) if hasattr(self.text_view, "get_bottom_margin") else 0
        self._runway_owner: object | None = None
        self._runway_settings: TypewriterSettings | None = None

        # A bottom-margin change can make GTK clamp the adjustment during the
        # following relayout.  Such a value change belongs to this runtime and
        # must not be misclassified as user scrolling.  The guard is cleared by
        # the next low-priority idle; it is not a retry loop.
        self._layout_adjustment_guard = False
        self._layout_guard_source: int | None = None

        self._external_adjustment_callbacks: dict[int, Callable[[], None]] = {}
        self._geometry_callbacks: dict[int, Callable[[], None]] = {}
        self._next_callback_id = 1
        self._handlers: list[tuple[Any, int]] = []

        if hasattr(self._adjustment, "connect"):
            self._handlers.append(
                (self._adjustment, self._adjustment.connect("changed", self._on_geometry_changed))
            )
            self._handlers.append(
                (
                    self._adjustment,
                    self._adjustment.connect("value-changed", self._on_adjustment_value_changed),
                )
            )
        if hasattr(self.text_view, "connect"):
            self._handlers.append(
                (self.text_view, self.text_view.connect("size-allocate", self._on_geometry_changed))
            )

    @property
    def base_bottom_margin(self) -> int:
        return self._base_bottom_margin

    @property
    def has_pending_projection(self) -> bool:
        return bool(self.reveal_pending or self.applying_adjustment)

    def connect_external_adjustment(self, callback: Callable[[], None]) -> int:
        if not callable(callback):
            raise TypeError("callback must be callable")
        callback_id = self._next_callback_id
        self._next_callback_id += 1
        self._external_adjustment_callbacks[callback_id] = callback
        return callback_id

    def connect_geometry_changed(self, callback: Callable[[], None]) -> int:
        if not callable(callback):
            raise TypeError("callback must be callable")
        callback_id = self._next_callback_id
        self._next_callback_id += 1
        self._geometry_callbacks[callback_id] = callback
        return callback_id

    def disconnect_callback(self, callback_id: int) -> None:
        self._external_adjustment_callbacks.pop(int(callback_id), None)
        self._geometry_callbacks.pop(int(callback_id), None)

    def set_base_bottom_margin(self, margin: int) -> None:
        self._base_bottom_margin = max(0, int(margin))
        if self._runway_owner is None:
            self._set_bottom_margin(self._base_bottom_margin)
        else:
            self._apply_runway()

    def acquire_runway(self, owner: object, settings: TypewriterSettings) -> None:
        if owner is None:
            raise TypeError("runway owner is required")
        if not isinstance(settings, TypewriterSettings):
            raise TypeError("settings must be TypewriterSettings")
        if self._runway_owner is not None and self._runway_owner is not owner:
            raise RuntimeError("editor viewport runway already has an owner")
        self._runway_owner = owner
        self._runway_settings = settings
        self._apply_runway()

    def release_runway(self, owner: object) -> None:
        if self._runway_owner is not owner:
            return
        self._runway_owner = None
        self._runway_settings = None
        self._set_bottom_margin(self._base_bottom_margin)

    def _mark_layout_owned_adjustment(self) -> None:
        self._layout_adjustment_guard = True
        if self._layout_guard_source is not None or self._shutdown:
            return
        try:
            self._layout_guard_source = self.glib.idle_add(
                self._clear_layout_adjustment_guard,
                priority=self.glib.PRIORITY_LOW,
            )
        except TypeError:
            self._layout_guard_source = self.glib.idle_add(
                self._clear_layout_adjustment_guard
            )

    def _clear_layout_adjustment_guard(self) -> bool:
        self._layout_guard_source = None
        self._layout_adjustment_guard = False
        return False

    def _set_bottom_margin(self, margin: int) -> None:
        desired = max(0, int(margin))
        current = int(self.text_view.get_bottom_margin()) if hasattr(self.text_view, "get_bottom_margin") else self._base_bottom_margin
        if current == desired:
            return
        if not hasattr(self.text_view, "set_bottom_margin"):
            return
        try:
            self._mark_layout_owned_adjustment()
            self.text_view.set_bottom_margin(desired)
            self.text_view.queue_resize()
        except Exception as error:
            self.log_nonfatal("viewport bottom-margin update failed", error)

    def _apply_runway(self) -> None:
        if self._runway_owner is None or self._runway_settings is None:
            return
        try:
            desired = runway_margin(
                self._adjustment.get_page_size(),
                self._runway_settings,
                base_margin=self._base_bottom_margin,
            )
            self._set_bottom_margin(desired)
        except Exception as error:
            self.log_nonfatal("viewport runway update failed", error)

    def queue_visible_to_insert(
        self,
        margin: float = 0.15,
        *,
        center_if_outside: bool = False,
    ) -> bool:
        if not 0.0 <= float(margin) <= 0.5:
            raise ValueError("margin must be between 0.0 and 0.5")
        self._replace_request(
            _ViewportRequest(
                mode="visible",
                margin=float(margin),
                center_if_outside=bool(center_if_outside),
            )
        )
        return False

    def queue_typewriter_to_insert(
        self,
        settings: TypewriterSettings,
        *,
        reached: bool = False,
        on_reached: Callable[[bool], None] | None = None,
    ) -> bool:
        if not isinstance(settings, TypewriterSettings):
            raise TypeError("settings must be TypewriterSettings")
        self._replace_request(
            _ViewportRequest(
                mode="typewriter",
                typewriter_settings=settings,
                typewriter_reached=bool(reached),
                on_typewriter_reached=on_reached,
            )
        )
        return False

    def _replace_request(self, request: _ViewportRequest) -> None:
        self.cancel_projection()
        if self._shutdown:
            return
        self._request = request
        self.reveal_pending = True
        # Measure once at low priority. If geometry is not ready, the request
        # remains pending and a real adjustment::changed/size-allocate signal
        # reschedules it. Do not queue a resize here: doing so would turn every
        # Typewriter projection into a self-induced layout loop.
        self._schedule_idle()

    def _schedule_idle(self) -> None:
        if self.scroll_source is not None or not self.reveal_pending or self._shutdown:
            return
        try:
            self.scroll_source = self.glib.idle_add(
                self._apply_once,
                priority=self.glib.PRIORITY_LOW,
            )
        except TypeError:
            self.scroll_source = self.glib.idle_add(self._apply_once)

    def _on_geometry_changed(self, *_args: Any) -> None:
        if self._shutdown:
            return
        self._apply_runway()
        if self.reveal_pending:
            self._schedule_idle()
        for callback in tuple(self._geometry_callbacks.values()):
            try:
                callback()
            except Exception as error:
                self.log_nonfatal("viewport geometry callback failed", error)

    def _on_adjustment_value_changed(self, *_args: Any) -> None:
        if (
            self._shutdown
            or self.applying_adjustment
            or self._layout_adjustment_guard
        ):
            return
        for callback in tuple(self._external_adjustment_callbacks.values()):
            try:
                callback()
            except Exception as error:
                self.log_nonfatal("viewport adjustment callback failed", error)

    def _measure(self) -> ViewportGeometry | None:
        buffer = self.text_view.get_buffer()
        iterator = buffer.get_iter_at_mark(buffer.get_insert())
        location = self.text_view.get_iter_location(iterator)
        visible = self.text_view.get_visible_rect()
        page_size = float(self._adjustment.get_page_size())
        geometry = ViewportGeometry(
            caret_y=location.y,
            caret_height=location.height,
            visible_y=visible.y,
            visible_height=visible.height,
            lower=self._adjustment.get_lower(),
            upper=self._adjustment.get_upper(),
            page_size=page_size,
            top_margin=(
                float(self.text_view.get_top_margin())
                if hasattr(self.text_view, "get_top_margin")
                else 0.0
            ),
        )
        caret_bottom = float(location.y) + max(1.0, float(location.height))
        if not geometry.ready:
            return None
        # Bulk text replacement can expose the new iter before the scroller's
        # upper bound includes it. Keep the one request pending for real layout.
        if float(self._adjustment.get_upper()) + 1.0 < caret_bottom:
            return None
        return geometry

    def _apply_once(self) -> bool:
        self.scroll_source = None
        request = self._request
        if self._shutdown or not self.reveal_pending or request is None:
            return False
        try:
            geometry = self._measure()
            if geometry is None:
                return False
            if request.mode == "typewriter":
                settings = request.typewriter_settings or TypewriterSettings()
                decision = compute_typewriter_target(
                    geometry,
                    settings,
                    reached=request.typewriter_reached,
                )
                target = decision.target
                if request.on_typewriter_reached is not None:
                    request.on_typewriter_reached(decision.reached)
            else:
                target = compute_vertical_reveal(
                    caret_y=geometry.caret_y,
                    caret_height=geometry.caret_height,
                    visible_y=geometry.visible_y,
                    visible_height=geometry.visible_height,
                    lower=geometry.lower,
                    upper=geometry.upper,
                    page_size=geometry.page_size,
                    top_margin=geometry.top_margin,
                    within_margin=request.margin,
                    center_if_outside=request.center_if_outside,
                )
            if target is not None:
                current = float(self._adjustment.get_value()) if hasattr(self._adjustment, "get_value") else float(geometry.visible_y)
                if abs(current - float(target)) > 0.5:
                    self.applying_adjustment = True
                    try:
                        self._adjustment.set_value(target)
                    finally:
                        self.applying_adjustment = False
            self._request = None
            self.reveal_pending = False
        except Exception as error:
            self._request = None
            self.reveal_pending = False
            self.log_nonfatal("editor viewport projection failed", error)
        return False

    def cancel_projection(self) -> None:
        if self.scroll_source is not None:
            try:
                self.glib.source_remove(self.scroll_source)
            except Exception as error:
                self.log_nonfatal("viewport source removal failed", error)
            self.scroll_source = None
        self._request = None
        self.reveal_pending = False

    # W95 compatibility name.
    cancel = cancel_projection

    def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        self.cancel_projection()
        if self._layout_guard_source is not None:
            try:
                self.glib.source_remove(self._layout_guard_source)
            except Exception as error:
                self.log_nonfatal("viewport layout-guard source removal failed", error)
            self._layout_guard_source = None
        if self._runway_owner is not None:
            owner = self._runway_owner
            self.release_runway(owner)
        for owner, handler in reversed(self._handlers):
            if hasattr(owner, "disconnect"):
                try:
                    owner.disconnect(handler)
                except Exception as error:
                    self.log_nonfatal("viewport signal disconnect failed", error)
        self._handlers.clear()
        self._external_adjustment_callbacks.clear()
        self._geometry_callbacks.clear()
