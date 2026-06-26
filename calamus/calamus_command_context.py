"""Command context and result primitives for Calamus.

This module is intentionally GTK-free.

It is the first thin AirPad-like control-layer component.  It does not own
file lifecycle, undo/redo, session state, or Gtk.TextBuffer synchronization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CommandContext:
    """Execution context passed to command handlers.

    The context is deliberately small.  At W7 it is only a safe carrier for
    an optional application object plus immutable command metadata/data.
    """

    app: Any | None = None
    source: str = "unknown"
    data: Mapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Return a contextual value without exposing mutation semantics."""

        return self.data.get(key, default)

    def with_data(self, **updates: Any) -> "CommandContext":
        """Return a new context with additional data."""

        merged = dict(self.data)
        merged.update(updates)
        return CommandContext(app=self.app, source=self.source, data=merged)


@dataclass(frozen=True)
class CommandResult:
    """Structured result returned by layer-dispatched commands."""

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
