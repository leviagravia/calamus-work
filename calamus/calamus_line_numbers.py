"""Canonical line-number preference and viewport-aligned gutter adapter.

The pure preference helpers own persisted normalization and transition planning.
``LineGutterAdapter`` owns the custom GTK view boundary without importing GTK at
module import time.  It draws only the currently visible logical buffer lines
at the exact y-coordinates reported by ``Gtk.TextView``; no second scrolling
text widget or duplicated line-height model exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from calamus_view_preferences import normalize_boolean

LINE_NUMBERS_KEY = "line_numbers"
DEFAULT_LINE_NUMBERS_ENABLED = True
DEFAULT_GUTTER_HORIZONTAL_PADDING = 12
DEFAULT_GUTTER_TEXT_RIGHT_PADDING = 3


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
    """Load one strict persisted line-number preference."""
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
    """Return deterministic one-based logical line numbers for pure callers."""
    normalized = normalize_line_count(line_count)
    return "\n".join(str(number) for number in range(1, normalized + 1))


def apply_line_gutter_typography(
    gutter: Any,
    font_family: str,
    font_size: int,
    *,
    pango: Any,
) -> Any:
    """Apply the editor font explicitly to the custom gutter drawing widget."""
    if not isinstance(font_family, str) or not font_family.strip():
        raise ValueError("font family must be a non-empty string")
    if isinstance(font_size, bool) or not isinstance(font_size, int):
        raise TypeError("font size must be an integer")
    if font_size <= 0:
        raise ValueError("font size must be positive")
    if not hasattr(gutter, "override_font"):
        raise TypeError("line-number widget must support override_font")
    if not hasattr(pango, "FontDescription"):
        raise TypeError("pango boundary must provide FontDescription")

    description = pango.FontDescription(f"{font_family.strip()} {font_size}")
    gutter.override_font(description)
    if hasattr(gutter, "queue_resize"):
        gutter.queue_resize()
    if hasattr(gutter, "queue_draw"):
        gutter.queue_draw()
    return description


def measure_line_gutter_width(
    gutter: Any,
    line_count: int,
    *,
    minimum_width: int,
    horizontal_padding: int = DEFAULT_GUTTER_HORIZONTAL_PADDING,
) -> int:
    """Measure gutter width from the drawing widget's effective Pango metrics."""
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
    layout = gutter.create_pango_layout("8" * digits)
    text_width, _text_height = layout.get_pixel_size()
    return max(minimum_width, int(text_width) + horizontal_padding)


class LineGutterAdapter:
    """Draw visible logical line numbers from the authoritative ``Gtk.TextView``.

    The adapter deliberately does not maintain a second vertically scrolled
    label.  Every painted number comes from ``GtkTextIter.get_line()`` and every
    y position comes from ``GtkTextView.get_line_yrange()``.  This keeps Search,
    the editor buffer and the gutter on one line-coordinate authority and also
    handles soft-wrapped paragraphs correctly.
    """

    def __init__(
        self,
        gutter: Any,
        text_view: Any,
        *,
        minimum_width: int,
        render_layout: Any,
        horizontal_padding: int = DEFAULT_GUTTER_HORIZONTAL_PADDING,
        text_right_padding: int = DEFAULT_GUTTER_TEXT_RIGHT_PADDING,
    ) -> None:
        if isinstance(minimum_width, bool) or not isinstance(minimum_width, int):
            raise TypeError("minimum gutter width must be an integer")
        if minimum_width <= 0:
            raise ValueError("minimum gutter width must be positive")
        if isinstance(horizontal_padding, bool) or not isinstance(horizontal_padding, int):
            raise TypeError("horizontal padding must be an integer")
        if horizontal_padding < 0:
            raise ValueError("horizontal padding cannot be negative")
        if isinstance(text_right_padding, bool) or not isinstance(text_right_padding, int):
            raise TypeError("text right padding must be an integer")
        if text_right_padding < 0:
            raise ValueError("text right padding cannot be negative")
        if not callable(render_layout):
            raise TypeError("render_layout must be callable")

        for method in (
            "set_visible",
            "set_size_request",
            "create_pango_layout",
            "override_font",
            "queue_resize",
            "queue_draw",
            "get_allocated_width",
            "get_style_context",
        ):
            if not callable(getattr(gutter, method, None)):
                raise TypeError(f"gutter widget must support {method}")
        for method in (
            "get_buffer",
            "get_visible_rect",
            "get_line_at_y",
            "get_line_yrange",
        ):
            if not callable(getattr(text_view, method, None)):
                raise TypeError(f"text view must support {method}")

        self.gutter = gutter
        self.text_view = text_view
        self.minimum_width = minimum_width
        self.horizontal_padding = horizontal_padding
        self.text_right_padding = text_right_padding
        self._render_layout = render_layout
        self._enabled = False
        self._last_line_count: int | None = None
        self._last_width = 0

    def current_line_count(self) -> int:
        buffer = self.text_view.get_buffer()
        get_line_count = getattr(buffer, "get_line_count", None)
        if not callable(get_line_count):
            raise TypeError("text buffer must support get_line_count")
        return normalize_line_count(get_line_count())

    def apply_typography(self, font_family: str, font_size: int, *, pango: Any) -> Any:
        description = apply_line_gutter_typography(
            self.gutter,
            font_family,
            font_size,
            pango=pango,
        )
        self._last_line_count = None
        return description

    def render(
        self,
        enabled: bool,
        line_count: int | None = None,
        *,
        force: bool = False,
    ) -> LineGutterRenderResult:
        preference = LineNumberPreference(enabled)
        if line_count is None:
            normalized_line_count = self.current_line_count()
        else:
            normalized_line_count = normalize_line_count(line_count)
        if not isinstance(force, bool):
            raise TypeError("force must be boolean")

        self._enabled = preference.enabled
        self.gutter.set_visible(preference.enabled)

        if not preference.enabled:
            self._last_line_count = normalized_line_count
            self._last_width = 0
            self.gutter.queue_draw()
            return LineGutterRenderResult(False, normalized_line_count, "", 0)

        if force or self._last_line_count != normalized_line_count or self._last_width <= 0:
            width = measure_line_gutter_width(
                self.gutter,
                normalized_line_count,
                minimum_width=self.minimum_width,
                horizontal_padding=self.horizontal_padding,
            )
            self.gutter.set_size_request(width, 1)
            self.gutter.queue_resize()
            self._last_width = width
            self._last_line_count = normalized_line_count

        self.gutter.queue_draw()
        return LineGutterRenderResult(
            True,
            normalized_line_count,
            "",
            self._last_width,
        )

    def visible_line_rows(self) -> tuple[tuple[int, int], ...]:
        """Return one-based logical line numbers and viewport-relative y values."""
        if not self._enabled:
            return ()

        visible = self.text_view.get_visible_rect()
        top = int(visible.y)
        bottom = top + int(visible.height)
        iterator, _line_top = self.text_view.get_line_at_y(top)
        rows: list[tuple[int, int]] = []
        seen_lines: set[int] = set()

        while True:
            line_number = int(iterator.get_line()) + 1
            line_y, line_height = self.text_view.get_line_yrange(iterator)
            if line_number not in seen_lines:
                rows.append((line_number, int(line_y) - top))
                seen_lines.add(line_number)

            if int(line_y) + int(line_height) >= bottom or iterator.is_end():
                break

            previous_line = int(iterator.get_line())
            moved = iterator.forward_line()
            if not moved and int(iterator.get_line()) == previous_line:
                break

        return tuple(rows)

    def draw(self, _widget: Any, cairo_context: Any) -> bool:
        if not self._enabled:
            return False

        width = self.gutter.get_allocated_width() or self._last_width
        layout = self.gutter.create_pango_layout("")
        style_context = self.gutter.get_style_context()

        for line_number, y in self.visible_line_rows():
            text = str(line_number)
            layout.set_text(text, -1)
            text_width, _text_height = layout.get_pixel_size()
            x = max(0, int(width) - self.text_right_padding - int(text_width) - 1)
            self._render_layout(
                style_context,
                cairo_context,
                x,
                int(y),
                layout,
            )
        return False
