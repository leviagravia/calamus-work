# Calamus Memoria Operativa — W103 Editor Transaction Extraction

## Identity

- Work item: `W103`
- Description: `Editor Transaction Extraction`
- Exact published baseline: `c8ee3d5970a0cb1d05e4c4320a2117fe7e493368`
- W102 state: `CLOSED / CERTIFIED / PUBLISHED`
- W103 state in this source: Candidate R1 implementation line; publication not yet authorized.

## Architectural decision

W103 extracts the logical editor-transaction authority from `App` without
changing Calamus' visible editing model. `Gtk.TextBuffer` remains the live
editor surface and W102 `DocumentSession` remains the only document text/dirty
state authority.

The new boundary is:

1. `calamus_editor_transaction.py` — GTK-free transaction controller;
2. `calamus_editor_buffer_adapter.py` — concrete buffer mutation/capture/restore boundary;
3. `calamus_editor_transaction_composition.py` — typed composition;
4. existing `TextHistory` / `SnapshotHistoryRuntime` retained and adapted.

The controller owns programmatic transaction begin/apply/commit/rollback,
native edit observation, history preparation/finalization, Undo/Redo
restoration, and synchronization with `DocumentSession`.

## Preserved invariants

- one logical programmatic command produces at most one Undo entry;
- native Gtk user actions retain the existing 600 ms snapshot coalescing;
- caret and selection direction are stored/restored exactly;
- Open/New/session replacement is not ordinary editor history;
- large-document history limits remain unchanged;
- `EditorViewportRuntime` remains the sole viewport writer;
- W104 retains command/action architecture ownership.

## New failure barrier

A programmatic edit that raises after partially mutating the visible buffer is
rolled back byte-for-byte to its captured pre-transaction state, including
caret, selection direction, history checkpoint, and unchanged
`DocumentSession` authority.

Nested programmatic transactions are rejected fail-closed.

## App compatibility

`App.execute_command`, `on_undo`, `on_redo`, `set_text_from_history` and the GTK
user-action/change callbacks remain named compatibility gateways but delegate
to the W103 controller. `App.restoring_undo` is read-only projection, not
mutable state.

Native Cut/Paste also cross the transaction/buffer boundary; their actual
transaction grouping remains the standard Gtk begin/end-user-action signal
sequence.

## Verification status before desktop candidate freeze

- W103 focused: PASS;
- W102/W101/W100/W99/W98 focused historical barriers: PASS;
- headless-core 1545 tests: PASS, zero skip, verified in four independent slices;
- filesystem capability profile: PASS;
- Pandoc real profile: PASS;
- source provenance: PASS, with GTK import checks deferred only because
  PyGObject is unavailable in the build container;
- GIO/GTK release profiles require the T480 desktop lane.

## Desktop validation rule

Desktop validation authority is Candidate/launcher cryptographic identity plus
`EXIT=0`, `ERR=NONE`, `FINAL_PHASE=RUNNER_RETURNED_PASS`, and the explicit human
manual PASS. Manual instructions must print concrete generated paths and never
use timestamp placeholders.
