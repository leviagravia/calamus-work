# CALAMUS W19 — Lowercase Command-Layer Wiring

## Status

Accepted and implemented as the second certified text-transform command routed through the CommandLayer.

## Background

W15 certified `edit.uppercase` through the existing `App.apply_text_transform` pipeline.
W18 audited `edit.lowercase` and found it safe to wire next because it is deterministic and already exists as a pure low-risk CommandLayer handler.

## Decision

Wire only `edit.lowercase` through the same discipline already used by W15.

- CommandLayer computes only.
- `Gtk.TextBuffer` mutation remains inside the existing edit closure.
- `command_transform_range` remains the range/selection transform primitive.
- `execute_command` remains edit-unit owner.
- `finalize_command_edit` remains dirty/status/title owner.
- no-op guard prevents unnecessary mutation.

## Dispatch surface after W19

The only GUI/runtime CommandLayer dispatch IDs in `bin/calamus` are:

- `writing.statistics`
- `edit.uppercase`
- `edit.lowercase`

## Non-goals

W19 does not extract a text-transform bridge module.
W19 does not wire whitespace cleanup, sort, reflow, join, clean-pdf, or smart typography.
W19 does not touch open/save/session/recovery/undo engine.
W19 does not change runtime identity, package, desktop file, icon, executable, or installed `/usr`.

## Next architectural step

After W19 desktop certification, the bridge has two real certified callers: `edit.uppercase` and `edit.lowercase`.
This makes a future module extraction audit appropriate:

- W20: audit extract text-transform bridge module
