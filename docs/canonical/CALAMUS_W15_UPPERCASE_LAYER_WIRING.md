# Calamus W15 — Uppercase CommandLayer Wiring

Status: Accepted / implemented pending desktop validation.

## Scope

W15 wires only:

- `edit.uppercase`

through the AirPad-like `CommandLayer`.

The insertion point is:

- `App.apply_text_transform`

## Corrected W15R repair

The first W15 attempt correctly patched the intended area but failed tests before commit.

W15R repaired the implementation by replacing the generic helper:

```text
command_layer_transform_text(command_id, text)
```

with a literal, uppercase-only helper:

```text
command_layer_uppercase_text(text)
```

This makes the dispatch surface statically auditable:

```text
writing.statistics
edit.uppercase
```

The helper is compute-only. It does not call:

- `Gtk.TextBuffer.delete`
- `Gtk.TextBuffer.insert`
- `set_text`
- `execute_command`
- `finalize_command_edit`
- `mark_modified`
- `begin_user_action`
- `end_user_action`

## Architecture

W15 follows the W14R4 source-first audit decision.

The CommandLayer computes transformed text only. It does not own:

- `Gtk.TextBuffer`
- buffer deletion/insertion
- file lifecycle
- undo history
- dirty-state
- session lifecycle
- status/title refresh

The existing Calamus edit pipeline remains authoritative:

```text
apply_text_transform
-> command_transform_range / transform_range
-> execute_command
-> finalize_command_edit
```

## No-op guard

W14R4 found that no-op ownership was missing or not obvious.

W15 therefore adds an explicit bridge-level guard for uppercase:

```python
if not changed:
    return False
```

This prevents an already-uppercase selection/range from reaching the mutation pipeline.

## Non-goals

W15 deliberately does not wire:

- `edit.lowercase`
- whitespace cleanup
- sort lines
- reflow paragraph
- join lines
- smart typography
- clean PDF
- open/save/session commands
- undo/redo internals

## Desktop validation required

After tests pass and commit/push complete:

1. Run from source.
2. Type lowercase/mixed text.
3. Select a range.
4. Run Uppercase.
5. Verify only the selected range changes.
6. Verify Undo restores.
7. Verify Redo reapplies if available.
8. Run Uppercase on already-uppercase text and verify no visible regression.
