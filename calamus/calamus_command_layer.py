"""GTK-free stable-ID command dispatcher for W104."""
from __future__ import annotations

from calamus_command_context import CommandContext, CommandInputError, CommandResult
from calamus_command_registry import CommandAvailability, CommandBinding, CommandRegistry, CommandSpec


class CommandLayer:
    """Resolve stable command ID -> explicit binding; metadata is not execution."""
    def __init__(self, registry: CommandRegistry | None = None, *, availability: CommandAvailability | None = None) -> None:
        self.registry = registry if registry is not None else CommandRegistry()
        self.availability = availability if availability is not None else CommandAvailability()
        self._bindings: dict[str, CommandBinding] = {}

    def register(self, spec: CommandSpec) -> CommandSpec:
        return self.registry.register(spec)

    def bind(self, binding: CommandBinding) -> CommandBinding:
        if binding.command_id not in self.registry:
            raise KeyError(binding.command_id)
        if binding.command_id in self._bindings:
            raise ValueError(f"duplicate command binding: {binding.command_id}")
        self._bindings[binding.command_id] = binding
        return binding

    def bind_callable(self, command_id: str, execute) -> CommandBinding:
        return self.bind(CommandBinding(command_id, execute))

    def binding_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._bindings))

    def dispatch(self, command_id: str, context: CommandContext | None = None) -> CommandResult:
        spec = self.registry.get(command_id)
        if spec is None:
            return CommandResult.fail(f"Unknown command: {command_id}")
        if not self.availability.is_enabled(command_id):
            return CommandResult.fail(f"Command disabled: {command_id}")
        binding = self._bindings.get(command_id)
        if binding is None:
            return CommandResult.noop(f"Command has no binding yet: {command_id}")
        ctx = context if context is not None else CommandContext()
        try:
            result = binding.execute(ctx)
        except CommandInputError as exc:
            return CommandResult.fail(f"Command input rejected: {command_id}", error=exc)
        if isinstance(result, CommandResult):
            return result
        return CommandResult.ok(value=result)
