# Calamus W9 — Pure Low-risk Command Handlers

Status: implemented  
Risk: low  
Behaviour change: none in GUI/application runtime

## Scope

W9 adds pure handlers for selected low-risk command catalog entries.

Added:

```text
calamus/calamus_command_handlers.py
tests/test_command_handlers.py
docs/canonical/CALAMUS_W9_PURE_LOW_RISK_COMMAND_HANDLERS.md
```

Modified:

```text
calamus/calamus_command_catalog.py
tests/test_command_catalog.py
```

## Handler policy

Handlers added in W9 are:

```text
GTK-free
file-free
session-free
undo-free
dirty-state-free
TextBuffer-free
```

They operate only on explicit text supplied in:

```text
CommandContext.data["text"]
```

They return a structured:

```text
CommandResult
```

## Commands with pure handlers

```text
edit.lowercase
edit.uppercase
writing.clean-pdf
writing.join-lines
writing.reflow-paragraph
writing.remove-extra-spaces
writing.remove-trailing-spaces
writing.sentence-case
writing.smart-typography
writing.sort-lines
writing.statistics
writing.title-case
```

## Command intentionally left metadata-only

```text
writing.insert-date-time
```

Reason: date/time insertion is time-dependent and is therefore not a pure deterministic text transform.

## Non-goals

W9 does not wire the layer into `bin/calamus`.

W9 does not route GUI actions through the layer.

W9 does not move existing App methods.

W9 does not touch:

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
targeted handler tests PASS
full source selftest PASS
bin/calamus unchanged
no runtime CommandLayer wiring from bin/calamus
installed Calamus unchanged
```
