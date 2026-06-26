# Calamus W11 — Wire `writing.statistics` through CommandLayer

Status: implemented  
Risk: low-medium  
Runtime behaviour change: intended to be none

## Scope

W11 wires only this command through the Command/Control Layer:

```text
writing.statistics -> App.on_document_statistics
```

## Why this command first

W10 selected `writing.statistics` as the first safe wiring target because it is read-only.

It does not need:

```text
Gtk editor buffer mutation
undo grouping
dirty-state changes
file lifecycle
session lifecycle
close/quit handling
save/open
```

## What changed

`bin/calamus` now imports:

```text
CommandContext
CommandLayer
build_low_risk_registry
```

`App.__init__` creates:

```text
self.command_layer = CommandLayer(build_low_risk_registry())
```

`App.on_document_statistics` dispatches:

```text
writing.statistics
```

through the layer and then keeps the existing statistics dialog behavior.

## What did not change

W11 does not wire:

```text
edit.uppercase
edit.lowercase
writing.sort-lines
writing.clean-pdf
writing.remove-extra-spaces
writing.remove-trailing-spaces
writing.smart-typography
writing.reflow-paragraph
writing.join-lines
```

W11 does not touch:

```text
open/save/save-as
dirty state
close/quit/session
undo/redo
Gtk.TextBuffer lifecycle
printing
search/replace GUI bridge
```

## Acceptance

```text
source provenance PASS
targeted static wiring tests PASS
full source selftest PASS
only one dispatch in bin/calamus
dispatch target is writing.statistics
installed Calamus unchanged
```

## Required desktop validation after script PASS

Run Calamus from source, type sample text, run Document Statistics, then verify:

```text
dialog appears
statistics look correct
document text unchanged
modified state unchanged
no crash
```
