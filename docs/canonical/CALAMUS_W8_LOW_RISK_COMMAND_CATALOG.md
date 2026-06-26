# Calamus W8 — Low-risk Command Catalog

Status: implemented  
Risk: low  
Behaviour change: none

## Scope

W8 registers low-risk Calamus commands inside the Command/Control Layer.

Added files:

```text
calamus/calamus_command_catalog.py
tests/test_command_catalog.py
docs/canonical/CALAMUS_W8_LOW_RISK_COMMAND_CATALOG.md
```

## What W8 does

W8 adds metadata-only command specifications for selected low-risk commands.

The layer now knows these command identities:

```text
writing.statistics
writing.insert-date-time
writing.sort-lines
writing.clean-pdf
writing.remove-extra-spaces
writing.remove-trailing-spaces
writing.smart-typography
writing.reflow-paragraph
writing.join-lines
writing.title-case
writing.sentence-case
edit.uppercase
edit.lowercase
```

## What W8 does not do

W8 does not add handlers.

W8 does not wire the layer into `bin/calamus`.

W8 does not move existing features.

W8 does not touch:

```text
open/save/save-as
dirty state
close/quit/session
undo/redo
Gtk.TextBuffer lifecycle
printing
search/replace GUI bridge
```

## Why this is useful

This creates a controlled command catalog before migration.  Future steps can wrap existing App methods one by one without inventing command identity during the patch that changes behaviour.

## Acceptance

```text
source provenance PASS
targeted command catalog tests PASS
full source selftest PASS
bin/calamus unchanged
installed Calamus unchanged
```
