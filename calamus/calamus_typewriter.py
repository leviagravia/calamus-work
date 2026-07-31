"""GTK-free state and geometry policy for Calamus Typewriter Mode."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from calamus_viewport import ViewportGeometry


class TypewriterEventKind(str, Enum):
    ACTIVATE = "activate"
    EDIT = "edit"
    KEYBOARD = "keyboard"
    HISTORY = "history"
    STRUCTURAL = "structural"
    RESIZE = "resize"


@dataclass(frozen=True)
class TypewriterSettings:
    """Stable first-release policy.

    No animation and no configurable controls are exposed in W95extra.  The
    small runway surplus compensates for the final visual row height and GTK
    rounding while preserving a midpoint working line.
    """

    target_fraction: float = 0.50
    runway_fraction: float = 0.55
    tolerance_px: float = 2.0

    def __post_init__(self) -> None:
        if not 0.20 <= float(self.target_fraction) <= 0.80:
            raise ValueError("target_fraction must be between 0.20 and 0.80")
        if not 0.0 <= float(self.runway_fraction) <= 1.0:
            raise ValueError("runway_fraction must be between 0.0 and 1.0")
        if float(self.tolerance_px) < 0.0:
            raise ValueError("tolerance_px must be non-negative")


@dataclass(frozen=True)
class TypewriterDecision:
    target: float | None
    reached: bool
    geometry_ready: bool


def compute_typewriter_target(
    geometry: ViewportGeometry,
    settings: TypewriterSettings = TypewriterSettings(),
    *,
    reached: bool = False,
) -> TypewriterDecision:
    """Return a midpoint projection only when that line is attainable.

    At the beginning of a document Calamus keeps the natural top position.  As
    soon as the caret naturally reaches an attainable working line, the policy
    latches and maintains it.  A view-only bottom runway makes the same line
    attainable at the end of the document.
    """
    if not geometry.ready:
        return TypewriterDecision(None, bool(reached), False)

    desired = (
        geometry.caret_center
        - float(geometry.page_size) * float(settings.target_fraction)
        + max(0.0, float(geometry.top_margin))
    )
    clamped = geometry.clamp(desired)
    attainable = abs(clamped - desired) <= float(settings.tolerance_px)
    now_reached = bool(reached or attainable)
    if not now_reached:
        return TypewriterDecision(None, False, True)

    target_buffer_y = float(geometry.visible_y) + (
        float(geometry.visible_height) * float(settings.target_fraction)
    )
    if abs(geometry.caret_center - target_buffer_y) <= float(settings.tolerance_px):
        return TypewriterDecision(None, True, True)
    return TypewriterDecision(clamped, True, True)


def runway_margin(
    page_size: float,
    settings: TypewriterSettings = TypewriterSettings(),
    *,
    base_margin: int = 0,
) -> int:
    page = max(0.0, float(page_size))
    base = max(0, int(base_margin))
    return base + int(round(page * float(settings.runway_fraction)))
