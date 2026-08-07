"""GTK-free global application UI-state projection for Calamus W105.

Logical authorities remain in their existing W102/W103/W106-future owners.
This module receives explicit immutable facts, derives application-menu state,
updates W104 dispatch availability from the same snapshot, and delegates visual
projection through one narrow port.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol

from calamus_menu_model import (
    CHECK_COMMAND_IDS,
    WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS,
)


@dataclass(frozen=True)
class ActionUiState:
    enabled: bool = True
    checked: bool | None = None
    visible: bool = True


@dataclass(frozen=True)
class UiStateFacts:
    research_panel_visible: bool = False
    navigator_panel_visible: bool = False
    workspace_panel_visible: bool = False
    typewriter_enabled: bool = False
    word_wrap: bool = True
    opacity_percent: int = 100
    always_on_top: bool = False
    appearance_mode: str = "system"
    line_numbers_enabled: bool = False
    workspace_root_present: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.opacity_percent, bool) or not isinstance(self.opacity_percent, int):
            raise TypeError("opacity_percent must be int")
        if not 0 <= self.opacity_percent <= 100:
            raise ValueError("opacity_percent out of range")
        if self.appearance_mode not in {"system", "light", "dark"}:
            raise ValueError(f"invalid appearance_mode: {self.appearance_mode!r}")


@dataclass(frozen=True)
class UiStateSnapshot:
    states: Mapping[str, ActionUiState]

    def __post_init__(self) -> None:
        normalized: dict[str, ActionUiState] = {}
        for command_id, state in self.states.items():
            key = str(command_id)
            if not key:
                raise ValueError("UI-state command ID must not be empty")
            if not isinstance(state, ActionUiState):
                raise TypeError("UI-state values must be ActionUiState")
            normalized[key] = state
        object.__setattr__(self, "states", MappingProxyType(normalized))

    def state_for(self, command_id: str) -> ActionUiState:
        return self.states.get(str(command_id), ActionUiState())

    def checked(self, command_id: str) -> bool | None:
        return self.state_for(command_id).checked

    def enabled(self, command_id: str) -> bool:
        return self.state_for(command_id).enabled


class UiStateProjectorPort(Protocol):
    def project(self, snapshot: UiStateSnapshot) -> None: ...


def derive_ui_state(facts: UiStateFacts) -> UiStateSnapshot:
    if not isinstance(facts, UiStateFacts):
        raise TypeError("facts must be UiStateFacts")

    states: dict[str, ActionUiState] = {
        "research.panel": ActionUiState(checked=facts.research_panel_visible),
        "navigate.navigator-panel": ActionUiState(checked=facts.navigator_panel_visible),
        "navigate.workspace-panel": ActionUiState(checked=facts.workspace_panel_visible),
        "writing.typewriter-mode": ActionUiState(checked=facts.typewriter_enabled),
        "options.word-wrap": ActionUiState(checked=facts.word_wrap),
        "options.transparent-mode": ActionUiState(checked=facts.opacity_percent < 100),
        "options.always-on-top": ActionUiState(checked=facts.always_on_top),
        "options.appearance.light": ActionUiState(checked=facts.appearance_mode == "light"),
        "options.appearance.dark": ActionUiState(checked=facts.appearance_mode == "dark"),
        "options.line-numbers": ActionUiState(checked=facts.line_numbers_enabled),
    }
    workspace_enabled = bool(facts.workspace_root_present)
    for command_id in WORKSPACE_ROOT_SENSITIVE_COMMAND_IDS:
        states[command_id] = ActionUiState(enabled=workspace_enabled)
    return UiStateSnapshot(states)


class UiStateController:
    """Own one logical snapshot and synchronize dispatch + projection exactly once."""

    def __init__(self, availability, projector: UiStateProjectorPort | None = None) -> None:
        if availability is None or not callable(getattr(availability, "set_enabled", None)):
            raise TypeError("availability must implement set_enabled")
        self._availability = availability
        self._projector = projector
        self._snapshot = UiStateSnapshot({})

    @property
    def snapshot(self) -> UiStateSnapshot:
        return self._snapshot

    def bind_projector(self, projector: UiStateProjectorPort) -> None:
        if projector is None or not callable(getattr(projector, "project", None)):
            raise TypeError("projector must implement project(snapshot)")
        self._projector = projector
        if self._snapshot.states:
            projector.project(self._snapshot)

    def refresh(self, facts: UiStateFacts) -> UiStateSnapshot:
        snapshot = derive_ui_state(facts)
        for command_id, state in snapshot.states.items():
            self._availability.set_enabled(command_id, state.enabled)
        self._snapshot = snapshot
        if self._projector is not None:
            self._projector.project(snapshot)
        return snapshot

    def requested_toggle(self, command_id: str) -> bool:
        checked = self._snapshot.checked(command_id)
        if checked is None:
            raise ValueError(f"command has no checked state: {command_id}")
        return not checked


if set(CHECK_COMMAND_IDS) != {
    "research.panel", "navigate.navigator-panel", "navigate.workspace-panel",
    "writing.typewriter-mode", "options.word-wrap", "options.transparent-mode",
    "options.always-on-top", "options.appearance.light", "options.appearance.dark",
    "options.line-numbers",
}:
    raise RuntimeError("W105 check-command contract drift")
