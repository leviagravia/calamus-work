# Calamus W95 — Mature-source audit for caret, selection, Undo/Redo and viewport

Date: 2026-07-30
Published baseline: `541804f8ff361b3afacb58f18e1e429c70b3a2f9`
Scope: close the existing Calamus history/caret debt without rewriting the editor; preserve findings for a future editor replacement.
Method: direct source audit of the uploaded archives. No Internet substitutes were used.

## Audited archives and SHA-256

- NotepadNext: `85ffd33d60a4ab90f66a635bcd2ff1399626079d09bd7cea64f9d641c1737298`
- ATSynEdit: `e33fb4dbf0eb9a4df5b60d11dca71c8b3e32a406e8edc259526274f689926c21`
- GNOME Text Editor: `8c330ad500dab7caaa6b9b034e4e778a0ae7c58eb8d9b0de9aa3456e41e5b148`
- GtkSourceView: `aa5c6789363b740c5b277dbf3bcc0ce337dd93f6437034534d171adb29d4e4af`
- Kate: `7b44b661957b596a7af8c3ab2c6cbdd52545d52ad86c159703f30c2b762563f8`
- Lite: `db983844656712d8f2270ca2eeb481418192273583b396ac7ab90cc46c304926`
- Geany: `beca992363f6fb590ee9f2b2d8179689060e8d050d46c343c482b01aae6bb2ac`
- Lapce: `7035f97fa04d26ba04d18ef991dcff0365573ee08285ed205aef3ab9414fd3da`

Earlier direct audits also remain relevant: Xed, Mousepad, Gedit, Zim, Gnote, CudaText and Smassh.

# 1. Calamus defect reconstructed from source

## Current pre-rebuild model

`calamus/calamus_history.py::TextHistory` stored `undo_stack: list[str]` and `redo_stack: list[str]`. A history entry had no caret, selection bound or selection direction.

`bin/calamus::estimate_history_cursor()` compared the old and new strings and returned their common-prefix offset. `set_text_from_history()` replaced the complete `GtkTextBuffer`, then called `set_cursor_offset()`. R4/R5 layered immediate and idle scrolling on top of this inferred position.

The model therefore confused three distinct responsibilities:

1. document state;
2. caret/selection state;
3. viewport projection.

The R5 gate also did not originally execute a true Undo cycle; it called `set_text_from_history()` directly. The correct proof must be edit → optional cursor navigation → `App.on_undo()` → exact text/marks → visible insertion mark.

## Root cause

The technical debt is not fundamentally a Gtk scrolling bug. The first loss happens earlier: Calamus discards the exact insert and selection-bound marks when recording history. Once that state is lost, later viewport repair can only display an estimate.

# 2. NotepadNext and bundled Scintilla

## Files, classes and functions read

- `src/UndoAction.h`, `src/UndoAction.cpp`
  - class `UndoAction`
  - constructor calls `beginUndoAction()`
  - destructor calls `endUndoAction()`
- `src/SelectionTracker.h`, `src/SelectionTracker.cpp`
  - `saveSelection()`
  - `restoreSelection()`
  - `trackInsertion()`
  - `trackDeletion()`
- `thirdparty/scintilla/src/UndoHistory.h/.cxx`
  - granular undo action storage, grouping and save-point state
- `thirdparty/scintilla/src/Editor.cxx`
  - `Editor::Undo()`
  - `Editor::Redo()`
  - `Editor::RestoreSelection()`
  - `Editor::EnsureCaretVisible()`

## Immediate finding for Calamus

NotepadNext wraps multi-step application edits with an RAII transaction. It does not depend on every caller remembering the closing call: construction begins the Undo action and destruction ends it.

`SelectionTracker` records caret and anchor separately, transforms both through insertions/deletions, and restores them with `setSelection(caret, anchor)`. It does not sort the endpoints and therefore preserves selection direction.

Scintilla’s `Editor::Undo()` obtains the new position from the document action history, restores the selection state, and only then calls `EnsureCaretVisible()`. Viewport visibility is the last operation, not the source of caret truth.

## Decision

- ADOPT now: explicit caret + anchor in history; grouped command boundary; visibility after semantic restoration.
- ADAPT later: context-manager/RAII-style Calamus edit transaction so every command has a guaranteed begin/end/finalize path.
- DEFER: Scintilla’s granular action engine and rectangular/multi-selection restoration.

## Future editor rewrite guidance

A replacement editor should expose a transaction object, not bare buffer mutation callbacks. The transaction should own inverse edits, cursor transformations, grouping metadata and cancellation. Application commands should be unable to produce a half-open Undo group.

# 3. ATSynEdit

## Files, classes and functions read

- `atsynedit/atstrings_undo.pas`
  - `TATUndoItem`
  - `TATUndoList`
  - `ItemCarets`, `ItemCarets2`
  - `ItemMarkers`, `ItemMarkers2`
  - `ItemCommandCode`, `ItemTickCount`, soft/hard marks
  - `AsString`
- `atsynedit/atstrings.pas`
  - `TATStrings.AddUndoItem()`
  - `TATStrings.UndoOrRedo()`
  - `BeginUndoGroup()` / `EndUndoGroup()`
  - `ActionSaveLastEditionPos()`
  - `ActionGotoLastEditionPos()`
  - `CaretsAfterLastEdition`
- `atsynedit/atsynedit_cmd_handler.inc`
  - calls to `ActionSaveLastEditionPos`

## Immediate finding for Calamus

Each ATSynEdit Undo item can own carets, paired-editor carets, markers, attributes, grouping identifiers and timing. `AddUndoItem()` captures caret arrays together with the edit. The engine deliberately avoids quadratic multi-caret memory by storing caret arrays only on the first handled caret of a command.

`UndoOrRedo()` explicitly restores `CaretsAfterLastEdition` before replay. Its source comments document exactly the two failures seen in Calamus:

- editing on one line, searching elsewhere, then Undo incorrectly jumping to the search line;
- editing off-screen, scrolling elsewhere, then Undo not showing the changed line.

`ActionSaveLastEditionPos()` stores the caret state associated with the last real edit. Navigation alone does not overwrite that authority.

## Decision

- ADOPT now: caret state belongs to the edit/history entry; navigation does not create or rewrite an Undo level.
- ADAPT now: store exact insert and selection-bound offsets in the bounded Calamus snapshot.
- DEFER: persistent serialized Undo, multi-caret arrays, paired views, markers/attributes and command-code grouping.

## Future editor rewrite guidance

ATSynEdit is the strongest reference for a future non-GtkSourceView custom engine. It shows that action records need edit payload, caret state, marker transforms, grouping identity, save-point semantics and explicit memory policy. Calamus should never implement multi-caret by duplicating a complete caret array on every low-level action.

# 4. GNOME Text Editor

## Files, classes and functions read

- `src/editor-document.c`
  - `EditorDocument`, a `GtkSourceBuffer` subclass
  - `_editor_document_save_insert_mark()`
  - `_editor_document_restore_insert_mark()`
  - private `saved_insert_mark` and `saved_selection_bound_mark`
- `src/editor-source-view.c`
  - `editor_source_view_scroll_to_insert_in_idle_cb()`
  - `editor_source_view_jump_to_iter()`
  - grouped editing functions using `begin_user_action()` / `end_user_action()`
- `src/editor-page.c`
  - `_editor_page_scroll_to_insert()`
  - post-load positioning paths
- `src/editor-session.c`
  - persistence of caret/selection/session state

## Immediate finding for Calamus

GNOME Text Editor treats the document as a buffer object and the viewport as a view. The document can save and restore the standard insert and selection-bound marks into private marks without sorting them. This preserves the semantic distinction between caret and anchor.

After loading/rooting, it uses one low-priority idle callback to jump to the insertion mark. That idle is bounded, owned and tied to a known lifecycle event. It is not a chain of arbitrary timeouts.

Normal scrolling uses `gtk_text_view_scroll_to_mark()` only after the insertion mark already contains the correct position.

## Decision

- ADOPT now: one cancellable low-priority idle after full-buffer restoration; no repeated timeout chain.
- ADOPT now: save/restore insert and selection-bound separately.
- ADAPT now: keep Calamus logic GTK-free, with a thin history view adapter performing mark operations.
- DEFER: convert the current document object into a `GtkSourceBuffer` subclass.

## Future editor rewrite guidance

A future Calamus editor should have a first-class Document/Buffer object with busy/loading state, file identity, marks and session state. The view should be replaceable and should not own document history. Session persistence should store caret, selection and scroll independently from the text.

# 5. GtkSourceView

## Files, classes and functions read

- `gtksourceview/gtksourcebuffer.c`
  - `_gtk_source_buffer_save_and_clear_selection()`
  - `_gtk_source_buffer_restore_selection()`
  - `begin_irreversible_action()` / `end_irreversible_action()` loading paths
- `gtksourceview/gtksourceview-snippets.c`
  - `_gtk_source_view_snippets_push()`
  - snippet insert/delete callbacks
  - `gtk_text_view_scroll_mark_onscreen()`
- GtkTextBuffer Undo/Redo integration paths in the current GTK4-oriented source

## Immediate finding for Calamus

GtkSourceView explicitly warns that ordered selection bounds are unsuitable when mark identity matters. It reads `get_insert()` and `get_selection_bound()` separately, stores them in temporary marks and restores them with `gtk_text_buffer_select_range(insert, selection_bound)`.

Snippet insertion is one user action. After the snippet engine places the active placeholder/caret, the view scrolls to the insertion mark. It does not calculate a position from textual similarity.

Bulk loading is marked irreversible and kept separate from ordinary undoable editing.

## Decision

- ADOPT now: exact insert/bound state and `select_range(insert, bound)` during restoration.
- ADOPT now: distinguish document loading/full replacement from user Undo.
- ADOPT now: `{{cursor}}` insertion remains one grouped edit, then synchronizes the committed post-edit caret state.
- DEFER: migrate Calamus to GtkSourceView/GtkSourceBuffer.

## Future editor rewrite guidance

GtkSourceView is the preferred future GTK-native foundation. It supplies mature text layout, marks, snippets, syntax infrastructure and native Undo. A migration must nevertheless be a separate architecture work item, because Calamus currently has many `Gtk.TextView` assumptions, gutter policies, commands and tests.

# 6. Kate / KTextEditor integration

## Files, classes and functions read

- `addons/format/CursorPositionRestorer.h`
  - class `CursorPositionRestorer`
  - per-view position capture
  - whitespace-insensitive semantic offset
  - exact-position fallback
- `addons/textfilter/plugin_katetextfilter.cpp`
  - `KTextEditor::Document::EditingTransaction`
  - selection removal, insertion and `setCursorPosition()`
- `apps/lib/kateviewspace.cpp`
  - view/document navigation state
- `apps/lib/ktexteditor_utils.cpp`
  - cursor/view utilities

## Immediate finding for Calamus

Kate assumes a document may have multiple views, each with its own cursor. `CursorPositionRestorer` snapshots every view. For formatter operations it stores both the literal cursor and a whitespace-insensitive semantic offset, allowing the caret to follow content when indentation changes.

Text filtering uses a document editing transaction and then restores the view cursor through the semantic KTextEditor API.

The KTextEditor implementation itself is an external dependency and is not contained in the Kate archive, so the audit certifies Kate’s integration contract, not the internal Undo algorithm.

## Decision

- ADOPT now: document state and view state must remain conceptually separate.
- REJECT for current debt: whitespace-semantic cursor remapping; W95 only needs exact pre/post offsets.
- DEFER: multi-view and moving cursor/range abstractions.

## Future editor rewrite guidance

If Calamus later supports split views or previews, caret and viewport state must be per view, while edits and Undo remain document-level. Transform-aware moving cursors/ranges are preferable to recomputing offsets after formatting.

# 7. Lite

## Files, classes and functions read

- `data/core/doc/init.lua`
  - `Doc.selection.a` and `Doc.selection.b`
  - `pop_undo()`
  - `raw_insert()`
  - `raw_remove()`
  - `undo()` / `redo()`
  - time-based command merging via `config.undo_merge_timeout`
- `data/core/docview.lua`
  - selection/caret observation
  - `scroll_to_make_visible()`

## Immediate finding for Calamus

Lite is small enough to expose the complete mechanism clearly. Its document model owns text lines and a directional two-ended selection. Before the inverse text action, `raw_insert()` and `raw_remove()` push a `selection` command. Undo replays both the text inverse and exact selection restoration.

Typing actions are merged by timestamp, but the selection record remains part of the group. The view observes changes to the document selection and scrolls only when the caret changed.

## Decision

- ADOPT now: even a lightweight editor must include selection in history.
- ADOPT now: retain Calamus’s 600 ms grouping, but store the before and after mark state at the edit boundary.
- DEFER: replace snapshots with Lite-style granular inverse commands.

## Future editor rewrite guidance

Lite provides the most approachable blueprint for a small Calamus-native engine: explicit document model, directional selection, inverse commands, merge timeout and a view that projects state. It should be studied before any custom rewrite, especially if GtkSourceView is rejected.

# 8. Geany / Scintilla integration

## Files, classes and functions read

- `src/document.c`
  - `document_undo()` / `document_redo()`
  - application metadata Undo actions layered above Scintilla
- `src/sciwrappers.c`
  - `sci_set_current_position()`
  - `sci_set_selection()`
  - `sci_scroll_caret()`
  - begin/end Undo wrappers
- `src/editor.c`
  - `snippets_make_replacements()`
  - `%cursor%` marker
  - `editor_insert_snippet()`
  - snippet completion followed by `sci_scroll_caret()`
  - transformations that track caret and anchor

## Immediate finding for Calamus

Geany deliberately separates setting the caret from scrolling. `sci_set_current_position(..., FALSE)` sets current position and anchor without moving the viewport; `sci_scroll_caret()` is a distinct final operation.

Selections preserve anchor/current direction via `SCI_SETSEL`. Snippet expansion converts `%cursor%` to a marker, inserts through the editor engine, sets the exact resulting position and then scrolls.

Document Undo delegates text actions to Scintilla while Geany layers application metadata such as BOM, encoding and EOL changes in its own stack.

## Decision

- ADOPT now: caret placement and viewport scrolling are separate operations.
- ADOPT now: `{{cursor}}` must synchronize the post-edit history state after explicit caret placement.
- DEFER: layered application/document Undo until Calamus has non-text document metadata requiring it.

## Future editor rewrite guidance

A future engine should permit app-level actions to participate in the same user-visible Undo sequence without contaminating low-level text actions. A narrow editor adapter should expose caret, anchor, selection, grouping and scroll as separate semantic methods.

# 9. Lapce

## Files, classes and functions read

- `lapce-app/src/doc.rs`
  - `Doc::do_insert()`
  - `Doc::do_edit()`
  - `Doc::do_raw_edit()`
  - `Doc::apply_deltas()`
  - `buffer.set_cursor_before()` / `set_cursor_after()`
  - revision checks
- `lapce-app/src/editor.rs`
  - command routing, cursor modes and selections
- `lapce-app/src/editor/view.rs`
  - revision-driven view invalidation and cursor rendering

The underlying buffer/Undo implementation is supplied by the external `floem_editor_core` workspace dependency and is not fully present in the archive. The application integration is nevertheless explicit.

## Immediate finding for Calamus

Before an insert/edit, Lapce clones the old cursor mode. After the buffer returns deltas, it writes both `cursor_before` and `cursor_after` into the buffer history. Undo therefore does not infer cursor state from text.

Every edit yields rope deltas. The same deltas transform syntax, diagnostics, inlay hints, find results, completion lenses and breakpoints. Revision IDs prevent stale asynchronous results from being applied to a newer document.

## Decision

- ADOPT now: store pre/post cursor state explicitly.
- REJECT for W95: rope/delta conversion and asynchronous revision architecture.
- DEFER: revisioned immutable edit pipeline for a future rewrite.

## Future editor rewrite guidance

Lapce is the long-term reference for large documents and asynchronous analysis. A new Calamus engine should expose revisions and deltas from day one, so Navigator, Search, gutter and future document overview can update incrementally and reject stale work. This is substantially beyond W95.

# 10. Cross-source conclusions

All mature editors agree on the following principles:

1. Caret/selection state is explicit.
2. Caret and anchor/selection-bound remain distinct.
3. Navigation alone is not a text Undo level.
4. Multi-step edits have a transaction/group boundary.
5. Undo restores semantic editor state before scrolling.
6. Viewport movement is a final projection step.
7. Full-document load/reload is not normal Undo.
8. A future high-performance editor should use granular edits or deltas, not complete snapshots.

No mature source supports Calamus’s retired pattern of storing only strings and guessing the caret from a common prefix.

# 11. Immediate architecture decision — close debt without editor rewrite

## ADOPT/ADAPT

Introduce GTK-free immutable:

```python
HistoryState(
    text: str,
    insert_offset: int,
    selection_bound_offset: int,
)
```

`TextHistory` stores bounded `HistoryState` entries. Memory accounting still counts text size and retains existing large-document limits.

A thin GTK boundary captures the standard insert/selection-bound marks. It restores text, then calls `select_range(insert, selection_bound)` to preserve direction.

A debounced edit group records:

- state before the first edit;
- state after the last edit;
- no new entry for navigation alone.

A command flushes any pending typing group, refreshes the current pre-command marks, performs one `begin_user_action`/`end_user_action`, applies the final selection/caret, then commits the post-command state.

`{{cursor}}` explicitly places the caret after the grouped insertion and then synchronizes the current history state, so Redo returns to the marker rather than the end of the inserted body.

After Undo/Redo, the view schedules exactly one cancellable low-priority idle scroll to the insertion mark. The source is removed on replacement or window destruction.

## REJECT

- common-prefix caret estimation;
- repeated idle/timeout stacking;
- direct `set_text_from_history()` called as a fake Undo test;
- sorting selection endpoints during capture/restore;
- migration to a new editor component inside W95.

# 12. Required proof

The True App/True GTK gate must execute:

1. real grouped edit;
2. cursor navigation away from the edit;
3. real `App.on_undo()`;
4. exact pre-edit text;
5. exact insert and selection-bound offsets, including reversed selection;
6. insertion mark inside the visible viewport;
7. Redo exact post-edit caret;
8. `{{cursor}}` at beginning, end and middle;
9. one-step Undo of complete Clip insertion;
10. normal close with no residual process.

# 13. Future Calamus editor rewrite blueprint — recorded, not authorized

A future rewrite must be a dedicated, explicitly authorized work item after current roadmap closure. It should not be smuggled into W95.

## Required layers

1. **Document core** — text storage, revision, encoding/EOL/file identity, dirty/save point.
2. **Selection model** — insert/caret, anchor, affinity, direction; optional multiple selections later.
3. **Edit transaction** — guaranteed begin/commit/rollback; inverse actions or deltas.
4. **Undo engine** — granular action groups, merge policy, cursor-before/after, save points and bounded memory.
5. **Marks/ranges** — transform through edits; support bookmarks, search hits and snippet placeholders.
6. **View adapter** — rendering, focus and viewport only; no document authority.
7. **Revision/delta bus** — Navigator, Search, gutter and analysis consume deltas and reject stale revisions.
8. **Load/reload lane** — irreversible/bulk replacement distinct from interactive edits.
9. **Session state** — per-view caret, selection and scroll, independent of document text.
10. **Testing** — pure model tests, transaction property tests, true widget tests, lifecycle and large-document stress.

## Candidate foundations

- Preferred GTK-native route: GtkSourceView/GtkSourceBuffer.
- Preferred custom-small-engine reference: Lite.
- Preferred advanced action/caret reference: ATSynEdit.
- Preferred high-performance delta/revision reference: Lapce.
- Preferred embedded mature engine reference: Scintilla through NotepadNext/Geany.

No foundation decision is authorized by this audit alone.

# 14. R1 source-preflight regression — UI callback return contract

The first mature-source rebuilt package was correctly stopped in the T480 source-preflight lane by the pre-existing W88 true-App regression:

```text
undo_result = win.on_undo()
assert undo_result is None
```

The mature-history rebuild had changed `App.on_undo()` and `App.on_redo()` to return Boolean success values because the new W95 gate used `require(app.on_undo(), ...)`. That was an architectural integration regression, not evidence against `HistoryState` or exact mark restoration.

The canonical W88 Authoring Bridge contract already states that `App.on_undo()` is a GTK/UI callback and its return value is not a semantic success flag. Existing menu and signal callers ignore that return. Mature editors likewise prove Undo through action availability and resulting document/caret state, not through a widget callback Boolean.

The repaired contract is:

1. `App.on_undo()` and `App.on_redo()` retain their historical `None` callback result;
2. an unavailable action remains a no-op, optionally reporting the bounded-history status;
3. the True GTK gate flushes pending history and checks `history.can_undo` / `history.can_redo` before invocation;
4. the gate invokes the real UI callback;
5. success is certified only from exact text, insert mark, selection-bound mark and viewport effects;
6. no test may use `require(app.on_undo(), ...)` or `require(app.on_redo(), ...)`.

This preserves the mature-source history architecture while restoring compatibility with W88 and the long-standing App callback surface.

# 15. Two-consecutive-FAIL reset and new direct audit: VS Code and Pulsar

After the mature-source rebuild R1 and R2 both failed, the candidate line was suspended and the source was re-audited before any further candidate. R1 failed the pre-existing `App.on_undo()` callback-return contract. R2 passed 1,459 tests and restored exact long-document text and caret, but the True GTK gate reported `caret_y=11381 visible=-10:637`. This proved the remaining defect was viewport projection, not history state.

The full direct audit is recorded in `docs/canonical/CALAMUS_W95_VSCODE_PULSAR_VIEWPORT_SOURCE_AUDIT.md`.

## Visual Studio Code 1.131.0

The uploaded stable release bundle stores `beforeCursorState` and `afterCursorState` inside serialized edit-stack elements. `undo()` calls `_applyUndo(..., beforeCursorState)` and `redo()` calls `_applyRedo(..., afterCursorState)`. Cursor/selection restoration is therefore action data. Separate view APIs include `revealPositionInCenterIfOutsideViewport()` and `revealRangeInCenterIfOutsideViewport()`: reveal is a layout/view request performed after selection restoration.

## Pulsar 1.132.0-dev

`TextEditor.undo()` delegates to `buffer.undo({ selectionsMarkerLayer })`, then calls `getLastSelection().autoscroll()`. Transactions, checkpoints and grouping all carry the same selection-marker layer. Specs prove restoration of multiple cursors, directional selections and the initiating view's selection when multiple editors share one buffer. The viewport belongs to the view, while text history and marker transformation belong to the buffer.

## Revised immediate decision

Retain exact `HistoryState`. Replace the assumption that one `scroll_to_mark()` callback proves visibility. Use one replaceable, event-driven reveal intent that waits for valid `GtkAdjustment` geometry, then directly computes a clamped vertical adjustment. Preserve the viewport when the caret is already visible; center it only when outside. Geometry changes, not elapsed time, re-trigger a pending request.

## Future rewrite addition

Add per-edit before/after selection sets, explicit document revisions, transaction checkpoints, a per-view selection layer, and a view-level reveal-intent API. A future engine must support one document with multiple views and reject stale background results by revision. These findings supplement GtkSourceView, ATSynEdit, Lite and Lapce; they do not authorize an editor rewrite inside W95.
