# W102 Direct Calamus Source Audit

## 1. Scope and baseline

The audit reads the published W101 source corresponding to commit
`17b409a05f356477173b2bdd348a67a4cf01f43c`. The source tree contains 557 files.
The principal monolith remains `bin/calamus`; W101 extracted construction and
ownership boundaries but deliberately left document-session semantics for W102.

The current canonical roadmap is the final W101 handover:
`W102 — Document Session Extraction`. A stale source roadmap assigning W102 to
Research Composition is superseded and is documented separately.

## 2. Existing positive foundations

### 2.1 GTK-free Document model

`calamus/calamus_model.py` defines `Document` with:
- `text`;
- `file_path`;
- `modified`;
- `set_text()`;
- `mark_modified()`;
- `mark_saved()`;
- `clear()`;
- `load()`;
- `save()`;
- `is_large()`.

This is a valid seed for W102. It already expresses the desired co-location of
identity, text snapshot, and dirty state without importing GTK.

### 2.2 Pure file-lifecycle plans

`calamus/calamus_file_lifecycle.py` defines immutable:
- `NewPlan`;
- `OpenPlan`;
- `SavePlan`;
- `prepare_new_plan()`;
- `prepare_open_plan()`;
- `prepare_save_plan()`;
- `prepare_save_as_plan()`.

These plans protect several important ordering rules:
- do not clear the previous identity before buffer replacement succeeds;
- do not change identity before a selected file has been read;
- represent Save As cancellation as no plan;
- preserve optional trailing-space normalization.

They are useful and should initially be retained, not discarded.

### 2.3 W101 typed composition boundary

W101 introduced frozen component records and a deterministic build order.
This gives W102 a proper insertion point for a typed document-session bundle.

## 3. Fragmented authority in App

### 3.1 Four session fields at construction

`App.__init__` creates:
- `self.document = Document(...)`;
- `self.current_file = self.document.file_path`;
- `self.modified = self.document.modified`;
- `self.loading = False`.

`Document.file_path` and `App.current_file` represent the same identity.
`Document.modified` and `App.modified` represent the same dirty state.
`App.loading` represents an operational phase that belongs with the session
transition authority.

### 3.2 Gtk.TextBuffer and Document.text

`App.buffer_text()` reads the GTK buffer and copies its text directly into
`Document.text`. The comment explicitly says that `Document` is not the owner
of per-keystroke `Gtk.TextBuffer` state.

That distinction is correct for W102: the GTK buffer may remain the live editing
surface. The defect is that synchronization and transition ownership are
scattered across App methods.

### 3.3 Unguarded bulk replacement

`App.set_buffer()` performs:
1. `loading = True`;
2. `Gtk.TextBuffer.set_text()`;
3. `loading = False`;
4. `Document.set_text()`;
5. duplicate `current_file` and `modified` assignments.

The first three steps do not use `try/finally`. An exception during GTK
replacement can strand the application in `loading=True`.

`execute_save_plan()` has the same unguarded pattern when save-time trailing
space normalization replaces the visible buffer.

Other paths, such as Open, New, template creation, and history restoration,
already use `try/finally`. W102 must make the safe guard universal through one
session-owned context manager or depth guard.

## 4. Dirty-state fragmentation

`on_changed()`, `finalize_command_edit()`, and history restoration each:
- assign `self.modified = True`;
- update `Document` separately;
- trigger title/status/search/research/UI invalidations.

The dirty transition is therefore not an event emitted by one owner. It is a
manual convention repeated in multiple edit paths.

W102 should centralize the state transition but must not absorb the edit
transaction grouping itself; that belongs to W103.

## 5. File transition orchestration

### 5.1 New

`execute_new_plan()` replaces the buffer, updates Document, mirrors path/dirty,
resets undo, changes document context, refreshes overview, and updates title.

Invariant to preserve:
- a failed replacement must leave previous document identity, text snapshot,
  and dirty state intact.

### 5.2 Open

`open_path()` reads the file before preparing `OpenPlan`.
`execute_open_plan()` bulk-replaces the buffer and only then commits identity.

Positive invariant:
- failed read or failed buffer replacement must not commit the new path.

The new session should own this invariant instead of relying on App ordering.

### 5.3 Save and Save As

`execute_save_plan()` may normalize trailing spaces in the GTK buffer before
writing. It then calls `Document.save()` and mirrors path/dirty state.

Critical current behavior:
- path and clean state are committed only after `write_text_file()` succeeds;
- if write fails after normalization, the visible buffer can remain normalized
  while the document remains modified and retains its prior identity.

W102 must preserve this historical behavior unless a separately authorized
product change explicitly alters it. The behavior must become a hostile test,
not an accidental side effect.

### 5.4 I/O implementation

`calamus_document.py`:
- prefers UTF-8 on read;
- falls back to locale decoding;
- writes UTF-8 directly with `open(..., "w")`;
- does not use atomic replacement.

W102 is an ownership extraction, not an atomic-save feature. Atomic save,
encoding UI, backup, and external-change handling remain deferred.

## 6. Close and application lifecycle

`ask_save()` and `may_continue()` are App-owned UI decisions.
`request_application_close()` first resolves save/discard/cancel and then
delegates shutdown ownership to the W99 `ApplicationLifecycleCoordinator`.

W102 may expose:
- whether save confirmation is required;
- save result;
- session close readiness.

W102 must not absorb:
- runtime source shutdown;
- window destruction;
- process exit;
- W99 lifecycle preflight.

This boundary is mandatory.

## 7. Workspace identity reconciliation

`reconcile_workspace_rename()` directly writes both:
- `Document.file_path`;
- `App.current_file`.

`reconcile_workspace_trash()` directly:
- detaches `Document.file_path`;
- copies current GTK text into Document;
- assigns `App.current_file = None`;
- assigns `App.modified = True`.

These paths prove that W102 is wider than File menu callbacks. Rename and trash
must call authoritative session methods:
- rebind active path after a committed rename;
- detach active identity after trash while preserving text and making the
  session modified.

Recent-file, favourite, settings, title, Research context, and Overview refresh
remain post-commit effects.

## 8. W101 composition coupling

`calamus_application_composition.py` injects Workspace callbacks directly from
App:
- `may_continue=app.may_continue`;
- `open_document=app.open_path`;
- `current_document_path=lambda: app.current_file`;
- `reconcile_rename=app.reconcile_workspace_rename`;
- `reconcile_trash=app.reconcile_workspace_trash`.

W102 must replace these with typed document-session ports. Workspace should not
know App and should not derive document identity from a lambda over an App field.

## 9. Existing test coupling

Current tests cover:
- Document model load/save/clear/modified;
- pure New/Open/Save plans;
- App command wiring;
- quit lifecycle;
- Workspace rename/trash identity;
- true-App desktop behavior.

Many tests refer to `current_file` and `modified` directly. W102 should migrate
those tests to the session API. Temporary read-only App compatibility
properties may preserve the published surface, but mutable aliases are
forbidden.

## 10. Direct audit decision

### Keep
- GTK-free `Document`;
- pure lifecycle plans;
- current read/write semantics;
- current prompts and GTK chooser placement;
- W99 lifecycle coordinator;
- one authoritative source document.

### Extract
- authoritative path;
- authoritative modified state;
- text snapshot synchronization;
- bulk-replacement guard;
- New/Open/Save/Save As transition commit;
- Workspace rename/trash document reconciliation;
- session readiness for close.

### Do not extract in W102
- undo transaction grouping;
- general command execution;
- menu state;
- preferences;
- application shutdown;
- autosave, recovery, file monitor, merge, tabs.
