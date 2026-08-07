"""Typed W105 composition boundary for GTK-free application UI state."""
from __future__ import annotations

from calamus_application_components import UiStateComponents, UiStateCompositionInput
from calamus_ui_state import UiStateController


def build_ui_state_components(inputs: UiStateCompositionInput) -> UiStateComponents:
    if not isinstance(inputs, UiStateCompositionInput):
        raise TypeError("inputs must be UiStateCompositionInput")
    return UiStateComponents(
        controller=UiStateController(inputs.command_availability),
    )
