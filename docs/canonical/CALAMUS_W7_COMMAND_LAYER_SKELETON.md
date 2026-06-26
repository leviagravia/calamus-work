# Calamus W7 — Command/Control Layer Skeleton

Status: implemented  
Risk: low  
Behaviour change: none

## Scope

W7 introduces the initial AirPad-like Command/Control Layer skeleton.

Added files:

```text
calamus/calamus_command_context.py
calamus/calamus_command_registry.py
calamus/calamus_command_layer.py
tests/test_command_layer.py
```

## Non-goals

W7 does not wire the layer into `bin/calamus`.

W7 does not move any existing feature.

W7 does not touch:

```text
open/save/save-as
dirty state
close/quit/session
undo/redo
Gtk.TextBuffer lifecycle
printing
search/replace GUI bridge
```

## Purpose

The layer provides the first stable vocabulary for future gradual modularization:

```text
CommandContext
CommandResult
CommandSpec
CommandRegistry
CommandLayer
```

## Migration discipline

A future command may enter the layer only by this order:

```text
1. register command identity and metadata
2. wrap existing App method without changing behaviour
3. prove source provenance
4. run selftests
5. only then consider moving pure logic
```

## AirPad relation

The layer follows AirPad as a model of order: command concerns should become explicit and separated instead of remaining hidden inside the application object.
