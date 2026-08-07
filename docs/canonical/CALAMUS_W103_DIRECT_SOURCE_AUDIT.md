# W103 Direct Calamus Source Audit

## Frozen ownership evidence

The W100 responsibility inventories assigned **51 App methods**
and **5 App attributes** to W103/editor-transaction ownership.

The five frozen attributes are:
`command_layer`, `history`, `history_runtime`, `restoring_undo`,
`viewport_runtime`.

The later binding roadmap makes W104 the command/action work item, so W103 must
not redesign CommandLayer identity/dispatch even though the older coarse
inventory grouped `command_layer` under editor transaction state.

## Strong foundations already present

- `calamus_history.py` is GTK-free.
- `HistoryState` preserves text, caret and selection direction.
- `TextHistory` prevents navigation-only Undo levels and bounds large-document
  history.
- `calamus_commands.py` already computes pure replacement/insertion/paste plans.
- W102 `DocumentSession` is authoritative for text snapshot and modified state.
- `execute_command()` already wraps one programmatic edit in one GTK
  begin/end-user-action pair.
- `SnapshotHistoryRuntime` already coalesces native edits and preserves
  before/after view state.

W103 should ADAPT these foundations, not replace them wholesale.

## Authority still concentrated in App

`execute_command()` currently owns:
history prepare, before capture, begin/end user action, arbitrary edit callback,
before/after comparison, finalize and no-op handling.

`finalize_command_edit()` owns:
selection placement, history finalization, DocumentSession dirty commit,
command label, status/search/gutter/title projection.

`on_changed()` owns:
DocumentSession observation, history scheduling, overview/navigator invalidation,
line-number refresh, search refresh, Typewriter/viewport behavior, Research
invalidation and title refresh.

`set_text_from_history()` owns:
restoring guard, session replacement guard, Gtk restore, viewport projection,
dirty commit and post-restore presentation.

This is the W103 extraction seam.

## Programmatic mutation surface

The machine inventory attached to this audit finds 44
functions that call recognized mutation/grouping primitives. Some are
presentation `set_text()` calls and are not editor writes, but the true editor
mutation entry points include:
selection transforms; Paste Clean/Plain; duplicate/move line; Character Map;
heading-link insertion; Quick Cite; reference-key migration; search replace;
spell replacement; native Cut/Paste; and history restore.

## Failure gap

`execute_command()` pairs `end_user_action()` in a `finally`, but if `edit_func`
raises after partially changing the buffer, there is no byte-exact rollback.
That can leave visible text different from the history/session state because
finalization never completes.

W103 should capture the exact before-state and restore it under an explicit
rollback/restoring guard when a programmatic edit fails after mutation.

## Native typing

Native typing is currently driven by Gtk `begin-user-action`, `changed`,
`end-user-action` plus a 600 ms snapshot debounce. This behavior is mature and
must remain unchanged: W103 must not create an Undo level per keystroke.

## Viewport

`EditorViewportRuntime` is already the sole scroll writer. W103 should depend on
a narrow reveal/projection port after Undo/Redo; it should not create a second
viewport owner.

## Decision

ADOPT:
- TextHistory/HistoryState;
- DocumentSession;
- pure edit plans;
- existing native typing coalescing;
- single viewport writer.

EXTRACT:
- transaction begin/apply/commit/rollback;
- history preparation/finalization;
- restoring state;
- Undo/Redo orchestration;
- caret/selection capture/restore;
- dirty-state synchronization;
- post-commit result classification.

DEFER W104:
- command IDs and registry;
- command availability/actions;
- menus and shortcuts;
- general command dispatch.

REJECT:
- second document model;
- second rich editor;
- whole-App transaction dependency;
- global event bus/service locator;
- silent change to Undo/coalescing semantics.
