"""Typed editor-font preferences for Calamus."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

FONT_FAMILY_KEY = "font_family"
FONT_SIZE_KEY = "font_size"
DEFAULT_FONT_FAMILY = "Monospace"
DEFAULT_FONT_SIZE = 12
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 32


@dataclass(frozen=True)
class FontPreference:
    family: str
    size: int


@dataclass(frozen=True)
class FontPreferencePlan:
    previous: FontPreference
    requested: FontPreference
    changed: bool


def normalize_font_family(value: Any, default: str = DEFAULT_FONT_FAMILY) -> str:
    if not isinstance(default, str) or not default.strip():
        raise ValueError("default font family must be a non-empty string")
    if isinstance(value, str):
        candidate = value.strip()
        if candidate and "\x00" not in candidate and "\n" not in candidate and "\r" not in candidate:
            return candidate
    return default.strip()


def normalize_font_size(
    value: Any,
    default: int = DEFAULT_FONT_SIZE,
    minimum: int = MIN_FONT_SIZE,
    maximum: int = MAX_FONT_SIZE,
) -> int:
    if isinstance(default, bool) or not isinstance(default, int):
        raise TypeError("default font size must be an integer")
    if isinstance(minimum, bool) or not isinstance(minimum, int):
        raise TypeError("minimum font size must be an integer")
    if isinstance(maximum, bool) or not isinstance(maximum, int):
        raise TypeError("maximum font size must be an integer")
    if minimum > maximum:
        raise ValueError("minimum font size cannot exceed maximum")
    if isinstance(value, bool):
        number = default
    elif isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if text and text.lstrip("+-").isdigit():
            number = int(text)
        else:
            number = default
    else:
        number = default
    return max(minimum, min(maximum, number))


def load_font_preference(settings: Mapping[str, Any] | None) -> FontPreference:
    if settings is None:
        settings = {}
    if not isinstance(settings, Mapping):
        raise TypeError("settings must be a mapping")
    return FontPreference(
        family=normalize_font_family(settings.get(FONT_FAMILY_KEY)),
        size=normalize_font_size(settings.get(FONT_SIZE_KEY)),
    )


def prepare_font_preference_plan(
    previous_family: str,
    previous_size: int,
    requested_family: str,
    requested_size: int,
) -> FontPreferencePlan:
    if not isinstance(previous_family, str) or not previous_family.strip():
        raise ValueError("previous font family must be a non-empty string")
    if isinstance(previous_size, bool) or not isinstance(previous_size, int):
        raise TypeError("previous font size must be an integer")
    if not isinstance(requested_family, str) or not requested_family.strip():
        raise ValueError("requested font family must be a non-empty string")
    if "\x00" in requested_family or "\n" in requested_family or "\r" in requested_family:
        raise ValueError("requested font family contains invalid characters")
    if isinstance(requested_size, bool) or not isinstance(requested_size, int):
        raise TypeError("requested font size must be an integer")
    requested_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, requested_size))
    previous = FontPreference(previous_family.strip(), max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, previous_size)))
    requested = FontPreference(requested_family.strip(), requested_size)
    return FontPreferencePlan(previous=previous, requested=requested, changed=previous != requested)
