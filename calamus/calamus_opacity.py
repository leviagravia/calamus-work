"""Typed top-level opacity preference and GTK adapter for Calamus.

The pure preference functions own persisted normalization, bounds, immutable
transition planning, and Transparent Mode semantics.  The GTK adapter imports
no toolkit at module import time and uses ``Gtk.Widget`` explicitly so Calamus
does not call the deprecated ``Gtk.Window.set_opacity/get_opacity`` API.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

OPACITY_KEY = "opacity"
MIN_OPACITY_PERCENT = 30
MAX_OPACITY_PERCENT = 100
DEFAULT_OPACITY_PERCENT = 88


@dataclass(frozen=True)
class OpacityPreference:
    percent: int

    def __post_init__(self) -> None:
        if isinstance(self.percent, bool) or not isinstance(self.percent, int):
            raise TypeError("opacity percent must be an integer")
        if not MIN_OPACITY_PERCENT <= self.percent <= MAX_OPACITY_PERCENT:
            raise ValueError("opacity percent is outside the supported range")

    @property
    def fraction(self) -> float:
        return self.percent / 100.0

    @property
    def transparent_mode(self) -> bool:
        return self.percent < MAX_OPACITY_PERCENT


@dataclass(frozen=True)
class OpacityPreferencePlan:
    previous: OpacityPreference
    requested: OpacityPreference

    @property
    def changed(self) -> bool:
        return self.previous != self.requested


def normalize_opacity_percent(
    value: Any,
    *,
    default: int = DEFAULT_OPACITY_PERCENT,
) -> int:
    """Normalize persisted legacy input while retaining the historical clamp.

    Calamus previously used ``clamp_int`` at startup, so numeric strings and
    integral/float JSON numbers remain accepted.  Booleans are rejected rather
    than silently becoming 0 or 1.
    """
    if isinstance(default, bool) or not isinstance(default, int):
        raise TypeError("default opacity must be an integer")
    if not MIN_OPACITY_PERCENT <= default <= MAX_OPACITY_PERCENT:
        raise ValueError("default opacity is outside the supported range")
    if isinstance(value, bool):
        return default
    try:
        normalized = int(value)
    except (TypeError, ValueError, OverflowError):
        normalized = default
    return max(MIN_OPACITY_PERCENT, min(MAX_OPACITY_PERCENT, normalized))


def load_opacity_preference(settings: Mapping[str, Any] | None) -> OpacityPreference:
    if settings is None:
        settings = {}
    if not isinstance(settings, Mapping):
        raise TypeError("opacity settings must be a mapping")
    return OpacityPreference(normalize_opacity_percent(settings.get(OPACITY_KEY)))


def prepare_opacity_preference_plan(
    current_percent: int,
    requested_percent: int,
) -> OpacityPreferencePlan:
    """Validate an explicit request and return an immutable transition."""
    return OpacityPreferencePlan(
        previous=OpacityPreference(current_percent),
        requested=OpacityPreference(requested_percent),
    )


def transparent_mode_requested_percent(current_percent: int, enabled: bool) -> int:
    """Map the legacy checkbox request to the canonical opacity percentage.

    Existing behavior is preserved: enabling from full opacity selects the
    historical 88% default; disabling always selects 100%.  Calamus does not
    remember the last custom translucent percentage in this work item.
    """
    current = OpacityPreference(current_percent)
    if not isinstance(enabled, bool):
        raise TypeError("Transparent Mode state must be boolean")
    if enabled:
        return current.percent if current.transparent_mode else DEFAULT_OPACITY_PERCENT
    return MAX_OPACITY_PERCENT


def opacity_settings_overrides(percent: int) -> dict[str, int]:
    return {OPACITY_KEY: OpacityPreference(percent).percent}


def apply_widget_opacity(widget: Any, percent: int, *, widget_api: Any = None) -> None:
    """Apply opacity through the non-deprecated Gtk.Widget API.

    ``widget_api`` is injectable so the adapter can be tested without opening a
    display.  Production callers omit it and receive ``Gtk.Widget`` lazily.
    """
    preference = OpacityPreference(percent)
    if widget_api is None:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        widget_api = Gtk.Widget
    setter = getattr(widget_api, "set_opacity", None)
    if not callable(setter):
        raise TypeError("widget opacity API does not provide set_opacity")
    setter(widget, preference.fraction)
