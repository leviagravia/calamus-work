# Calamus W104 — Command and Action Architecture Contract

Baseline: `ca1a9774085d81d087f7a257dbffbbaa858a3889` (W103 CLOSED/CERTIFIED/PUBLISHED)

W104 is architecture-only and behavior-preserving. It establishes one authoritative stable-ID command catalog, separates immutable command metadata from explicit runtime bindings and runtime availability, removes whole-App command context, parameterizes repeated/dynamic command families, and makes shortcut metadata a projection of the same catalog.

## Mandatory architecture

- One authoritative `CommandRegistry` / catalog for every user-invokable command.
- Existing certified command IDs are preserved.
- `CommandSpec` contains identity/presentation metadata only: no runtime handler and no mutable/static `enabled` authority.
- Runtime execution is an explicit `CommandBinding(command_id, execute)`.
- `CommandContext` contains invocation source and primitive/domain payload only; it must not contain `App`, GTK widgets, or an arbitrary service bag.
- `CommandLayer` resolves exact command IDs, checks separate availability, invokes only explicit bindings, catches only classified `CommandInputError`, and never falls back to `getattr()`.
- Dynamic families use one stable ID plus payload (recent/favourite/template/workspace path, opacity value, font-size delta, line direction, clip slot, sort direction).
- Default accelerators and Keyboard Shortcuts guide rows derive from the authoritative catalog.
- Menu activation may route through IDs while preserving exact menu structure and behavior.

## Ownership boundary

W104 represents user intent; it does not own document/session/editor/preferences/research/workspace business logic. W102 DocumentSession and W103 EditorTransaction remain authoritative. Future W106/W107/W108 owners remain unchanged.

W105 is explicitly out of scope: W104 must not redesign menu composition, GTK sensitivity, check-state projection, or general UI-state architecture.

## Rejected designs

No plugin command framework, service locator, global event bus, dynamic DI, dynamic `getattr()` dispatch, command god-object, user-custom keybinding subsystem, menu reorganization, or new product feature.
