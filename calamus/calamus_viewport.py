"""GTK-free viewport projection rules for Calamus.

The editor view owns presentation.  History, navigation and Typewriter Mode
supply semantic intents; this module converts measured caret/viewport geometry
into a clamped vertical-adjustment target without importing GTK.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ViewportGeometry:
    caret_y: float
    caret_height: float
    visible_y: float
    visible_height: float
    lower: float
    upper: float
    page_size: float
    top_margin: float = 0.0

    @property
    def caret_center(self) -> float:
        return float(self.caret_y) + max(1.0, float(self.caret_height)) / 2.0

    @property
    def maximum(self) -> float:
        lower = float(self.lower)
        return max(lower, float(self.upper) - float(self.page_size))

    @property
    def ready(self) -> bool:
        return float(self.visible_height) > 1.0 and float(self.page_size) > 1.0

    def clamp(self, value: float) -> float:
        return max(float(self.lower), min(float(value), self.maximum))


def compute_vertical_reveal(
    *,
    caret_y: float,
    caret_height: float,
    visible_y: float,
    visible_height: float,
    lower: float,
    upper: float,
    page_size: float,
    top_margin: float = 0.0,
    within_margin: float = 0.15,
    center_if_outside: bool = True,
) -> float | None:
    """Return one ordinary ensure-visible adjustment target.

    The function preserves the W95 ordering: restore semantic caret/selection
    state first, then reveal the insert mark through measured view geometry.
    """
    if not 0.0 <= float(within_margin) <= 0.5:
        raise ValueError("within_margin must be between 0.0 and 0.5")
    geometry = ViewportGeometry(
        caret_y=caret_y,
        caret_height=caret_height,
        visible_y=visible_y,
        visible_height=visible_height,
        lower=lower,
        upper=upper,
        page_size=page_size,
        top_margin=top_margin,
    )
    if not geometry.ready:
        return None

    height = max(1.0, float(caret_height))
    margin_px = float(visible_height) * float(within_margin)
    safe_top = float(visible_y) + margin_px
    safe_bottom = float(visible_y) + float(visible_height) - margin_px
    caret_top = float(caret_y)
    caret_bottom = caret_top + height
    if caret_top >= safe_top and caret_bottom <= safe_bottom:
        return None

    if center_if_outside:
        desired = geometry.caret_center - float(page_size) / 2.0
    elif caret_top < safe_top:
        desired = caret_top - margin_px
    else:
        desired = caret_bottom - float(page_size) + margin_px
    desired += max(0.0, float(top_margin))
    return geometry.clamp(desired)
