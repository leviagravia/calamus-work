"""Authoritative GTK-free command metadata and runtime binding primitives.

W104 separates immutable command identity/metadata from execution bindings and
runtime availability.  No application object or GTK widget belongs here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Callable, Iterable, Mapping

from calamus_command_context import CommandContext, CommandResult

VALID_RISK_CLASSES = ("low", "low-medium", "medium", "medium-high", "high")
_COMMAND_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")


def _freeze_payload(value: Mapping[str, object] | Iterable[tuple[str, object]] | None = None) -> tuple[tuple[str, object], ...]:
    if value is None:
        return ()
    items = value.items() if isinstance(value, Mapping) else value
    return tuple(sorted((str(key), item) for key, item in items))


@dataclass(frozen=True)
class CommandShortcut:
    accelerator: str
    display: str = ""
    payload: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        accelerator = self.accelerator.strip()
        if not accelerator:
            raise ValueError("shortcut accelerator must not be empty")
        object.__setattr__(self, "accelerator", accelerator)
        object.__setattr__(self, "display", (self.display or accelerator).strip())
        object.__setattr__(self, "payload", _freeze_payload(self.payload))

    def data(self) -> dict[str, object]:
        return dict(self.payload)


@dataclass(frozen=True)
class CommandGuideEntry:
    menu: str
    command: str
    access: str
    note: str = ""


@dataclass(frozen=True)
class CommandSpec:
    """Immutable command identity and presentation metadata only."""

    command_id: str
    label: str
    menu_path: str = ""
    shortcuts: tuple[CommandShortcut, ...] = field(default_factory=tuple)
    risk_class: str = "low"
    flags: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    parameter_kind: str = ""
    guide_entries: tuple[CommandGuideEntry, ...] = field(default_factory=tuple)
    owner: str = ""
    effect: str = ""
    invalidations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        command_id = self.command_id.strip()
        label = self.label.strip()
        menu_path = self.menu_path.strip()
        risk_class = self.risk_class.strip()
        if not command_id or not _COMMAND_ID_RE.match(command_id):
            raise ValueError(f"invalid command_id: {self.command_id!r}")
        if not label:
            raise ValueError("label must not be empty")
        if risk_class not in VALID_RISK_CLASSES:
            raise ValueError(f"invalid risk_class: {self.risk_class!r}")
        object.__setattr__(self, "command_id", command_id)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "menu_path", menu_path)
        object.__setattr__(self, "risk_class", risk_class)
        object.__setattr__(self, "shortcuts", tuple(self.shortcuts))
        object.__setattr__(self, "flags", tuple(self.flags))
        object.__setattr__(self, "guide_entries", tuple(self.guide_entries))
        object.__setattr__(self, "invalidations", tuple(self.invalidations))

    @property
    def shortcut(self) -> str:
        """Compatibility projection: first accelerator, never authoritative."""
        return self.shortcuts[0].accelerator if self.shortcuts else ""


class CommandRegistry:
    def __init__(self, specs: Iterable[CommandSpec] = ()) -> None:
        self._commands: dict[str, CommandSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: CommandSpec) -> CommandSpec:
        if spec.command_id in self._commands:
            raise ValueError(f"duplicate command_id: {spec.command_id}")
        self._commands[spec.command_id] = spec
        return spec

    def get(self, command_id: str) -> CommandSpec | None:
        return self._commands.get(command_id)

    def require(self, command_id: str) -> CommandSpec:
        spec = self.get(command_id)
        if spec is None:
            raise KeyError(command_id)
        return spec

    def command_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._commands))

    def list_commands(self) -> tuple[CommandSpec, ...]:
        return tuple(self._commands[key] for key in self.command_ids())

    def __contains__(self, command_id: str) -> bool:
        return command_id in self._commands

    def __len__(self) -> int:
        return len(self._commands)


CommandExecutor = Callable[[CommandContext], CommandResult | object]


@dataclass(frozen=True)
class CommandBinding:
    command_id: str
    execute: CommandExecutor


class CommandAvailability:
    """Runtime logical availability, deliberately separate from CommandSpec."""
    def __init__(self) -> None:
        self._enabled: dict[str, bool] = {}

    def set_enabled(self, command_id: str, enabled: bool) -> None:
        self._enabled[str(command_id)] = bool(enabled)

    def is_enabled(self, command_id: str) -> bool:
        return self._enabled.get(str(command_id), True)


def shortcut_conflicts(specs: Iterable[CommandSpec]) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for spec in specs:
        for binding in spec.shortcuts:
            shortcut = binding.accelerator.replace("<Ctrl>", "<Control>").strip()
            seen.setdefault(shortcut, []).append(spec.command_id)
    return {shortcut: ids for shortcut, ids in seen.items() if len(ids) > 1}
