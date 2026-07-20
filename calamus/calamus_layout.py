"""Stable UI layout constants for Calamus GTK shell."""
from __future__ import annotations

# Keep the canonical right panel compact: wide enough for Clip Collection
# controls and future bounded research sections, but never wide enough to
# steal editor space or change wrapping aggressively.
RIGHT_PANEL_DEFAULT_WIDTH = 190
RIGHT_PANEL_MIN_WIDTH = 184
RIGHT_PANEL_MAX_FRACTION = 0.22

# Compatibility aliases for pre-W69 callers. New code must use RIGHT_PANEL_*.
CLIP_PANEL_DEFAULT_WIDTH = RIGHT_PANEL_DEFAULT_WIDTH
CLIP_PANEL_MIN_WIDTH = RIGHT_PANEL_MIN_WIDTH
CLIP_PANEL_MAX_FRACTION = RIGHT_PANEL_MAX_FRACTION

# Line number gutter must be compact and must never drive top-level window
# geometry. Dynamic width is computed from the current line count.
LINE_GUTTER_MIN_WIDTH = 30
LINE_GUTTER_MAX_WIDTH = 54

# Editor scrollers own document growth. These values are minimum viewport
# floors only; they must never become natural-size requests driven by content.
EDITOR_MIN_CONTENT_WIDTH = 360
EDITOR_MIN_CONTENT_HEIGHT = 220
LINE_GUTTER_MIN_CONTENT_HEIGHT = 120
