"""Canonical line-number preference and custom gutter adapter for Calamus.

The pure preference functions own persisted normalization and immutable
transition planning.  ``LineGutterAdapter`` owns Calamus' custom Gtk.Label
presentation without importing GTK at module import time, so the App launcher
no longer renders line numbers or calculates gutter geometry itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from calamus_view_preferences import normalize_boolean

LINE_NUMBERS_KEY = "line_numbers"
DEFAULT_LINE_NUMBERS_ENABLED = True
DEFAULT_GUTTER_HORIZONTAL_PADDING = 12
DEFAULT_GUTTER_LABEL_WIDTH_OFFSET = 5


@dataclass(frozen=True)
class LineNumberPreference:
    enabled: bool

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise TypeError("line-number preference must be boolean")


@dataclass(frozen=True)
class LineNumberPreferencePlan:
    previous: LineNumberPreference
    requested: LineNumberPreference

    @property
    def changed(self) -> bool:
        return self.previous != self.requested


@dataclass(frozen=True)
class LineGutterRenderResult:
    visible: bool
    line_count: int
    text: str
    width: int


def load_line_number_preference(
    settings: Mapping[str, Any] | None,
) -> LineNumberPreference:
    """Load one strict persisted line-number preference.

    Historical JSON booleans and integer 0/1 values remain accepted.  Arbitrary
    truthy strings are rejected instead of becoming enabled through ``bool()``.
    """
    if settings is None:
        settings = {}
    if not isinstance(settings, Mapping):
        raise TypeError("line-number settings must be a mapping")
    enabled = normalize_boolean(
        settings.get(LINE_NUMBERS_KEY),
        DEFAULT_LINE_NUMBERS_ENABLED,
    )
    return LineNumberPreference(enabled)


def prepare_line_number_preference_plan(
    current_enabled: bool,
    requested_enabled: bool,
) -> LineNumberPreferencePlan:
    return LineNumberPreferencePlan(
        previous=LineNumberPreference(current_enabled),
        requested=LineNumberPreference(requested_enabled),
    )


def line_number_settings_overrides(enabled: bool) -> dict[str, bool]:
    return {LINE_NUMBERS_KEY: LineNumberPreference(enabled).enabled}


def normalize_line_count(line_count: int) -> int:
    if isinstance(line_count, bool) or not isinstance(line_count, int):
        raise TypeError("line count must be an integer")
    if line_count < 0:
        raise ValueError("line count cannot be negative")
    return max(1, line_count)


def build_line_number_text(line_count: int) -> str:
    """Return deterministic one-based logical line numbers.

    Calamus intentionally numbers logical buffer lines, not soft-wrapped visual
    rows.  An empty document still displays line 1, matching GtkTextBuffer.
    """
    normalized = normalize_line_count(line_count)
    return "\n".join(str(number) for number in range(1, normalized + 1))


def apply_line_gutter_typography(
    line_numbers: Any,
    font_family: str,
    font_size: int,
    *,
    pango: Any,
) -> Any:
    """Apply the editor font explicitly to Calamus' custom Gtk.Label gutter."""
    if not isinstance(font_family, str) or not font_family.strip():
        raise ValueError("font family must be a non-empty string")
    if isinstance(font_size, bool) or not isinstance(font_size, int):
        raise TypeError("font size must be an integer")
    if font_size <= 0:
        raise ValueError("font size must be positive")
    if not hasattr(line_numbers, "override_font"):
        raise TypeError("line number widget must support override_font")
    if not hasattr(pango, "FontDescription"):
        raise TypeError("pango boundary must provide FontDescription")

    description = pango.FontDescription(f"{font_family.strip()} {font_size}")
    line_numbers.override_font(description)
    if hasattr(line_numbers, "queue_resize"):
        line_numbers.queue_resize()
    return description


def measure_line_gutter_width(
    line_numbers: Any,
    line_count: int,
    *,
    minimum_width: int,
    horizontal_padding: int = DEFAULT_GUTTER_HORIZONTAL_PADDING,
) -> int:
    """Measure gutter width from the label's effective Pango metrics."""
    normalized_line_count = normalize_line_count(line_count)
    if isinstance(minimum_width, bool) or not isinstance(minimum_width, int):
        raise TypeError("minimum_width must be an integer")
    if isinstance(horizontal_padding, bool) or not isinstance(horizontal_padding, int):
        raise TypeError("horizontal_padding must be an integer")
    if minimum_width <= 0:
        raise ValueError("minimum_width must be positive")
    if horizontal_padding < 0:
        raise ValueError("horizontal_padding cannot be negative")

    digits = len(str(normalized_line_count))
    layout = line_numbers.create_pango_layout("8" * digits)
    text_width, _text_height = layout.get_pixel_size()
    return max(minimum_width, int(text_width) + horizontal_padding)


class LineGutterAdapter:
    """Explicit view adapter for Calamus' separate line-number widgets."""

    def __init__(
        self,
        container: Any,
        label: Any,
        *,
        minimum_width: int,
        horizontal_padding: int = DEFAULT_GUTTER_HORIZONTAL_PADDING,
        label_width_offset: int = DEFAULT_GUTTER_LABEL_WIDTH_OFFSET,
    ) -> None:
        if isinstance(minimum_width, bool) or not isinstance(minimum_width, int):
            raise TypeError("minimum gutter width must be an integer")
        if minimum_width <= 0:
            raise ValueError("minimum gutter width must be positive")
        if isinstance(horizontal_padding, bool) or not isinstance(horizontal_padding, int):
            raise TypeError("horizontal padding must be an integer")
        if horizontal_padding < 0:
            raise ValueError("horizontal padding cannot be negative")
        if isinstance(label_width_offset, bool) or not isinstance(label_width_offset, int):
            raise TypeError("label width offset must be an integer")
        if label_width_offset < 0:
            raise ValueError("label width offset cannot be negative")

        for method in ("set_visible", "set_size_request"):
            if not callable(getattr(container, method, None)):
                raise TypeError(f"gutter container must support {method}")
        for method in (
            "set_visible",
            "set_text",
            "set_size_request",
            "create_pango_layout",
            "override_font",
        ):
            if not callable(getattr(label, method, None)):
                raise TypeError(f"gutter label must support {method}")

        self.container = container
        self.label = label
        self.minimum_width = minimum_width
        self.horizontal_padding = horizontal_padding
        self.label_width_offset = label_width_offset
        self._last_visible: bool | None = None
        self._last_line_count: int | None = None
        self._last_text = ""
        self._last_width = 0

    def apply_typography(self, font_family: str, font_size: int, *, pango: Any) -> Any:
        description = apply_line_gutter_typography(
            self.label,
            font_family,
            font_size,
            pango=pango,
        )
        # Font metrics changed, so the next refresh must remeasure geometry even
        # when the document has the same number of logical lines.
        self._last_line_count = None
        return description

    def render(
        self,
        enabled: bool,
        line_count: int,
        *,
        force: bool = False,
    ) -> LineGutterRenderResult:
        preference = LineNumberPreference(enabled)
        normalized_line_count = normalize_line_count(line_count)
        if not isinstance(force, bool):
            raise TypeError("force must be boolean")

        self.container.set_visible(preference.enabled)
        self.label.set_visible(preference.enabled)

        if not preference.enabled:
            if self._last_visible is not False or self._last_text:
                self.label.set_text("")
            self._last_visible = False
            self._last_line_count = normalized_line_count
            self._last_text = ""
            self._last_width = 0
            return LineGutterRenderResult(False, normalized_line_count, "", 0)

        if (
            not force
            and self._last_visible is True
            and self._last_line_count == normalized_line_count
        ):
            return LineGutterRenderResult(
                True,
                normalized_line_count,
                self._last_text,
                self._last_width,
            )

        text = build_line_number_text(normalized_line_count)
        self.label.set_text(text)
        width = measure_line_gutter_width(
            self.label,
            normalized_line_count,
            minimum_width=self.minimum_width,
            horizontal_padding=self.horizontal_padding,
        )
        self.container.set_size_request(width, 1)
        self.label.set_size_request(max(1, width - self.label_width_offset), 1)
        if hasattr(self.container, "queue_resize"):
            self.container.queue_resize()
        if hasattr(self.label, "queue_resize"):
            self.label.queue_resize()
        self._last_visible = True
        self._last_line_count = normalized_line_count
        self._last_text = text
        self._last_width = width
        return LineGutterRenderResult(True, normalized_line_count, text, width)
