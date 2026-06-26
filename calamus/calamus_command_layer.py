"""Thin command/control layer skeleton for Calamus.

W7 intentionally does not wire this layer into the application.  It provides
only a safe skeleton for later AirPad-like migration:

  command identity -> command metadata -> context -> result

No existing feature is moved here yet.
"""

from __future__ import annotations

from calamus_command_context import CommandContext, CommandResult
from calamus_command_registry import CommandRegistry, CommandSpec


class CommandLayer:
    """Small dispatcher around a CommandRegistry."""

    def __init__(self, registry: CommandRegistry | None = None) -> None:
        self.registry = registry if registry is not None else CommandRegistry()

    def register(self, spec: CommandSpec) -> CommandSpec:
        return self.registry.register(spec)

    def dispatch(self, command_id: str, context: CommandContext | None = None) -> CommandResult:
        spec = self.registry.get(command_id)
        if spec is None:
            return CommandResult.fail(f"Unknown command: {command_id}")
        if not spec.enabled:
            return CommandResult.fail(f"Command disabled: {command_id}")
        if spec.handler is None:
            return CommandResult.noop(f"Command has no handler yet: {command_id}")

        ctx = context if context is not None else CommandContext()
        try:
            result = spec.handler(ctx)
        except Exception as exc:
            return CommandResult.fail(f"Command failed: {command_id}", error=exc)

        if isinstance(result, CommandResult):
            return result
        return CommandResult.ok(value=result)
