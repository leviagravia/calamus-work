"""Typed application appearance preference for Calamus.

This module owns the canonical light/dark/system state and compatibility with
Calamus' historical ``white_background`` / ``dark_mode`` booleans.  It has no
GTK, filesystem, document, or Undo dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

APPEARANCE_SYSTEM = "system"
APPEARANCE_LIGHT = "light"
APPEARANCE_DARK = "dark"
APPEARANCE_MODES = frozenset({APPEARANCE_SYSTEM, APPEARANCE_LIGHT, APPEARANCE_DARK})
DEFAULT_APPEARANCE_MODE = APPEARANCE_LIGHT


@dataclass(frozen=True)
class AppearancePreference:
    mode: str

    def __post_init__(self) -> None:
        if self.mode not in APPEARANCE_MODES:
            raise ValueError(f"unsupported appearance mode: {self.mode!r}")

    @property
    def white_background(self) -> bool:
        return self.mode == APPEARANCE_LIGHT

    @property
    def dark_mode(self) -> bool:
        return self.mode == APPEARANCE_DARK


@dataclass(frozen=True)
class AppearancePreferencePlan:
    previous: AppearancePreference
    requested: AppearancePreference

    @property
    def changed(self) -> bool:
        return self.previous != self.requested


def normalize_appearance_mode(value: Any, *, default: str = DEFAULT_APPEARANCE_MODE) -> str:
    """Return a canonical appearance mode for persisted input.

    Persisted values are deliberately strict: only a string matching one of
    the three canonical modes is accepted.  Truthy strings such as ``"dark"``
    are not interpreted as booleans for legacy keys.
    """
    if default not in APPEARANCE_MODES:
        raise ValueError("default appearance mode is invalid")
    if isinstance(value, str):
        candidate = value.strip().lower()
        if candidate in APPEARANCE_MODES:
            return candidate
    return default


def _legacy_boolean(settings: Mapping[str, Any], key: str) -> bool | None:
    if key not in settings:
        return None
    value = settings[key]
    return value if isinstance(value, bool) else None


def load_appearance_preference(settings: Mapping[str, Any] | None) -> AppearancePreference:
    """Load canonical state, accepting the historical two-boolean format.

    A valid ``appearance_mode`` is authoritative.  Otherwise explicit legacy
    booleans are migrated deterministically: light wins the impossible old
    ``True/True`` state because the W64 launcher normalized that state to
    white mode at startup.  With no usable appearance keys Calamus retains its
    historical light default.
    """
    if settings is None:
        settings = {}
    if not isinstance(settings, Mapping):
        raise TypeError("appearance settings must be a mapping")

    raw_mode = settings.get("appearance_mode")
    if isinstance(raw_mode, str) and raw_mode.strip().lower() in APPEARANCE_MODES:
        return AppearancePreference(raw_mode.strip().lower())

    white = _legacy_boolean(settings, "white_background")
    dark = _legacy_boolean(settings, "dark_mode")
    if white is True:
        return AppearancePreference(APPEARANCE_LIGHT)
    if dark is True:
        return AppearancePreference(APPEARANCE_DARK)
    if white is False or dark is False:
        return AppearancePreference(APPEARANCE_SYSTEM)
    return AppearancePreference(DEFAULT_APPEARANCE_MODE)


def prepare_appearance_preference_plan(
    current_mode: str,
    requested_mode: str,
) -> AppearancePreferencePlan:
    """Validate an explicit UI request and return an immutable transition."""
    if not isinstance(current_mode, str) or current_mode not in APPEARANCE_MODES:
        raise ValueError("current appearance mode is invalid")
    if not isinstance(requested_mode, str) or requested_mode not in APPEARANCE_MODES:
        raise ValueError("requested appearance mode is invalid")
    return AppearancePreferencePlan(
        previous=AppearancePreference(current_mode),
        requested=AppearancePreference(requested_mode),
    )


def appearance_settings_overrides(mode: str) -> dict[str, Any]:
    """Return canonical persistence plus backward-compatible legacy keys."""
    preference = AppearancePreference(mode)
    return {
        "appearance_mode": preference.mode,
        "white_background": preference.white_background,
        "dark_mode": preference.dark_mode,
    }
