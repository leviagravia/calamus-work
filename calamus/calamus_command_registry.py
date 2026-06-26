"""Command registry skeleton for Calamus.

The registry is intentionally small and deterministic.  It records command
identity, metadata, risk class, optional shortcut, optional menu path, and an
optional handler.  It does not yet replace existing App methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Callable, Iterable

from calamus_command_context import CommandContext, CommandResult


CommandHandler = Callable[[CommandContext], CommandResult | object]

VALID_RISK_CLASSES = ("low", "low-medium", "medium", "medium-high", "high")
_COMMAND_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")


@dataclass(frozen=True)
class CommandSpec:
    """Metadata for a Calamus command controlled by the layer."""

    command_id: str
    label: str
    menu_path: str = ""
    shortcut: str = ""
    risk_class: str = "low"
    flags: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    handler: CommandHandler | None = None
    enabled: bool = True

    def __post_init__(self) -> None:
        command_id = self.command_id.strip()
        label = self.label.strip()
        menu_path = self.menu_path.strip()
        shortcut = self.shortcut.strip()
        risk_class = self.risk_class.strip()

        if not command_id:
            raise ValueError("command_id must not be empty")
        if not _COMMAND_ID_RE.match(command_id):
            raise ValueError(f"invalid command_id: {self.command_id!r}")
        if not label:
            raise ValueError("label must not be empty")
        if risk_class not in VALID_RISK_CLASSES:
            raise ValueError(f"invalid risk_class: {self.risk_class!r}")

        object.__setattr__(self, "command_id", command_id)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "menu_path", menu_path)
        object.__setattr__(self, "shortcut", shortcut)
        object.__setattr__(self, "risk_class", risk_class)
        object.__setattr__(self, "flags", tuple(self.flags))


class CommandRegistry:
    """Deterministic command registry.

    W7 purpose:
      - keep command metadata in one place;
      - reject duplicate command IDs;
      - provide stable listing and lookup;
      - support later dispatch without wiring yet.
    """

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


def shortcut_conflicts(specs: Iterable[CommandSpec]) -> dict[str, list[str]]:
    """Return normalized shortcut conflicts for command specs."""

    seen: dict[str, list[str]] = {}
    for spec in specs:
        shortcut = spec.shortcut.replace("<Ctrl>", "<Control>").strip()
        if not shortcut:
            continue
        seen.setdefault(shortcut, []).append(spec.command_id)
    return {shortcut: ids for shortcut, ids in seen.items() if len(ids) > 1}
