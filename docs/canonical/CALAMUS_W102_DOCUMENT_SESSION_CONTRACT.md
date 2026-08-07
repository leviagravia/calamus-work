# W102 Document Session Extraction — Candidate R1 Contract

## 1. Identity

- Work item: W102
- Name: Document Session Extraction
- Exact baseline: `17b409a05f356477173b2bdd348a67a4cf01f43c`
- Product mode: Core architectural extraction
- Visible features: none
- Persistence changes: none
- File-format changes: none

## 2. Architectural objective

Create one authoritative GTK-free document-session boundary that owns:
- active document identity;
- document text snapshot;
- modified state;
- guarded bulk-replacement phase;
- commit semantics for New/Open/Save/Save As;
- active-document rebinding after Workspace rename;
- active-document detachment after Workspace trash;
- session readiness for close.

`App`, `Gtk.TextBuffer`, Workspace, Recent Files, title/status, Research, and
Document Overview must consume this authority instead of maintaining parallel
fields.

## 3. Proposed modules

### 3.1 `calamus_document_session.py`

GTK-free domain/runtime module containing:
- `DocumentSessionPhase`: `IDLE`, `REPLACING`, `OPENING`, `SAVING`;
- frozen `DocumentSessionSnapshot`;
- frozen `DocumentSessionTransition`;
- mutable authoritative `DocumentSession` wrapping the existing `Document`;
- nesting-safe replacement guard;
- buffer-change observation;
- New/Open/Save/Save As commit;
- Workspace rebind/detach.

### 3.2 `calamus_document_session_controller.py`

GTK-free orchestration with explicitly injected ports:
- read current buffer text;
- replace buffer text;
- reset undo after committed replacement;
- read file;
- write file;
- large-file query.

The controller may consume existing immutable lifecycle plans. It must not open
dialogs, update menu items, or save application preferences.

### 3.3 `calamus_document_session_composition.py`

Typed W101-style construction boundary:
- builds session and controller;
- binds concrete App/GTK adapters;
- returns a frozen `DocumentSessionComponents` bundle;
- imports no product composition modules from domain modules.

A two-module version is acceptable if controller and domain remain clearly
separated and file sizes stay bounded. Ownership rules are mandatory; exact
file count is secondary.

## 4. Authoritative state rules

1. `DocumentSession.file_path` is the only writable active identity.
2. `DocumentSession.modified` is the only writable dirty state.
3. Session phase/guard is the only authority suppressing ordinary changed
   handling.
4. Source code must contain no assignments to `App.current_file`,
   `App.modified`, or `App.loading`.
5. Temporary App compatibility properties may be read-only delegates.
6. Gtk.TextBuffer remains the live per-keystroke surface in W102.
7. W103, not W102, extracts editor transactions.

## 5. Transition contracts

### Buffer changed
Outside replacement: synchronize text, mark modified, increment revision, then
run existing UI/research/history effects. During replacement: suppress ordinary
dirty transition.

### New
Resolve save decision at UI boundary; replace buffer under guard; commit empty
untitled clean state only after replacement succeeds; then reset undo and run
presentation effects.

### Open
Read first; replace under guard; commit path/text/clean only after replacement
succeeds. Read or replacement failure preserves the previous snapshot.

### Save
Capture text and prepare SavePlan. If normalization changes text, preserve the
historical guarded visible replacement before write. Commit path/clean only
after write success. A failed write may leave normalized text visible, but must
preserve prior identity and modified state.

### Save As
Cancellation is mutation-free. Selected identity commits only after write
success.

### Workspace rename
After filesystem success, rebind active path through session; preserve text and
dirty state.

### Workspace trash
After filesystem success, detach active path, preserve current text, mark
modified.

### Close
Session reports whether confirmation/save is required and whether save
succeeded. App owns dialogs. W99 owns shutdown.

## 6. Composition order

1. document-session seed;
2. editor infrastructure;
3. bind editor-buffer adapter;
4. navigator/left panel;
5. workspace using session ports;
6. right panel;
7. clip collection;
8. workspace startup binding;
9. last-file restore through session controller.

No subsystem receives whole App merely to discover document state.

## 7. Required unchanged behavior

- New/Open/Save/Save As prompts;
- UTF-8 and locale fallback;
- trailing-space preference behavior;
- recent/favourite and last-file behavior;
- title dirty marker;
- large-file behavior;
- Research/Overview invalidation timing;
- Workspace rename/trash result;
- close/cancel/save-failure behavior;
- W99 normal close;
- settings schema.

## 8. Explicit exclusions

No atomic-save feature, external monitor, autosave, drafts, recovery, local
history, encoding redesign, tabs, merge UI, command registry, menu-state
architecture, preferences extraction, editor transaction extraction, or new
build features.

## 9. Completion definition

W102 completes only when the session is single and GTK-free, mutable App mirrors
are gone, Workspace uses typed ports, all hostile transition tests pass,
W101/W100/W99/W98 profiles and full regression pass, desktop behavior remains
unchanged, and publication follows user validation.
