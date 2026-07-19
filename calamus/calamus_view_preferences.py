"""Typed view-preference plans for Calamus.

The module owns deterministic normalization and change planning for visual
editor preferences.  Gtk widgets, persistence and error dialogs remain App
boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


TEXT_WRAP_KEY = "word_wrap"
DEFAULT_TEXT_WRAP = True


@dataclass(frozen=True)
class TextWrapPlan:
    """One requested text-wrap state transition."""

    previous_enabled: bool
    enabled: bool
    changed: bool


def normalize_boolean(value: Any, default: bool) -> bool:
    """Return a strict persisted boolean without truthifying arbitrary values.

    Legacy JSON booleans and integer 0/1 are accepted.  Strings such as
    ``"false"`` are rejected rather than becoming truthy through ``bool()``.
    """
    if not isinstance(default, bool):
        raise TypeError("default must be boolean")
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    return default


def load_text_wrap_preference(settings: Mapping[str, Any] | None) -> bool:
    """Load the canonical text-wrap preference from a settings mapping."""
    if settings is None:
        return DEFAULT_TEXT_WRAP
    if not isinstance(settings, Mapping):
        raise TypeError("settings must be a mapping")
    return normalize_boolean(settings.get(TEXT_WRAP_KEY), DEFAULT_TEXT_WRAP)


def prepare_text_wrap_plan(previous_enabled: bool, requested_enabled: bool) -> TextWrapPlan:
    """Validate and describe a text-wrap transition without touching Gtk."""
    if not isinstance(previous_enabled, bool):
        raise TypeError("previous text-wrap state must be boolean")
    if not isinstance(requested_enabled, bool):
        raise TypeError("requested text-wrap state must be boolean")
    return TextWrapPlan(
        previous_enabled=previous_enabled,
        enabled=requested_enabled,
        changed=previous_enabled != requested_enabled,
    )
