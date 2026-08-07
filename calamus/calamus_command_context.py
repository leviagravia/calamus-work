"""GTK-free command invocation and result primitives."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping


class CommandInputError(ValueError):
    """Expected invalid command payload/input; safe to report as a command failure."""


@dataclass(frozen=True)
class CommandContext:
    """Immutable command invocation data.  It deliberately contains no App/widget."""
    source: str = "unknown"
    data: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def with_data(self, **updates: Any) -> "CommandContext":
        merged = dict(self.data)
        merged.update(updates)
        return CommandContext(source=self.source, data=merged)


@dataclass(frozen=True)
class CommandResult:
    success: bool
    message: str = ""
    changed: bool = False
    value: Any | None = None
    error: BaseException | None = None

    @classmethod
    def ok(cls, message: str = "", *, changed: bool = False, value: Any | None = None) -> "CommandResult":
        return cls(True, message=message, changed=changed, value=value)

    @classmethod
    def noop(cls, message: str = "No action taken.") -> "CommandResult":
        return cls(True, message=message, changed=False)

    @classmethod
    def fail(cls, message: str, *, error: BaseException | None = None) -> "CommandResult":
        return cls(False, message=message, changed=False, error=error)
