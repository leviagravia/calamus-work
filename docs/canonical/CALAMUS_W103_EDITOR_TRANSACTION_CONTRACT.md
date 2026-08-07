# W103 Editor Transaction Extraction — Candidate R1 Contract

## Identity

- Work item: W103
- Name: Editor Transaction Extraction
- Exact baseline: `c8ee3d5970a0cb1d05e4c4320a2117fe7e493368`
- Visible feature changes: none
- Persistence/file-format changes: none

## Objective

Extract one editor-transaction authority from `App` while preserving W102
`DocumentSession` as the sole document text/dirty authority and retaining the
GtkTextBuffer as the live editing surface.

## Ownership

`calamus_editor_transaction.py` is GTK-free and owns logical edit grouping,
programmatic rollback, native-edit history observation, Undo/Redo restoration,
and DocumentSession synchronization.

`calamus_editor_buffer_adapter.py` is the narrow GtkTextBuffer mutation/capture
boundary. It owns no command, history, document, menu, or presentation policy.

`calamus_editor_transaction_composition.py` constructs the typed W103 boundary.

## Transaction invariants

1. One programmatic command creates at most one Undo level.
2. A no-op creates no Undo level and no dirty transition.
3. A command that fails after partial mutation restores exact visible text,
   caret, selection direction, history stacks, and pre-command session state.
4. Nested programmatic transactions fail closed.
5. Native typing retains the published 600 ms history coalescing semantics.
6. Open/New/document replacement never enters edit history.
7. Undo/Redo restoration does not create a new history entry.
8. W102 DocumentSession remains the only writable text/dirty authority.
9. EditorViewportRuntime remains the single scroll writer.

## W104 boundary

W103 does not redesign command IDs, command registry/catalog, action
availability, menu/shortcut binding, or general command dispatch. Those remain
W104 Command and Action Architecture.
