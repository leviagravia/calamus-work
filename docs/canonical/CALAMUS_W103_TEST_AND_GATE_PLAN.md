# W103 Test and Gate Plan

GTK-free:
- no-op => no history/no dirty;
- one replacement => one Undo;
- multi-replacement => one Undo;
- exception before mutation => exact identity;
- exception after partial mutation => byte/caret/selection/history/session exact rollback;
- redo clearing unchanged;
- Undo/Redo do not create history;
- selection direction survives round trip;
- native typing keeps 600 ms coalescing;
- large-document limits unchanged;
- Open/New replacement never enters edit history.

GTK adapter:
- exact capture/restore;
- begin/end pairing under success/failure;
- replace range/whole text;
- native cut/paste through transaction gateway.

Static:
- transaction controller imports no GTK;
- no direct editor insert/delete/set_text in App outside a narrow approved raw adapter;
- no mutable App.restoring_undo;
- no whole-App transaction dependency;
- no W104 command/action redesign;
- no settings/persistence changes;
- W102 session is sole dirty-state authority.

Desktop:
1. native typing + Undo/Redo;
2. selected transform + one Undo;
3. Paste Plain over selection + one Undo;
4. Duplicate Line + one Undo;
5. Replace All + one Undo;
6. Quick Cite + one Undo;
7. Open/New add no Undo;
8. normal close, no residual process, real config unchanged.

All desktop paths must be printed as exact concrete paths. No placeholders.
