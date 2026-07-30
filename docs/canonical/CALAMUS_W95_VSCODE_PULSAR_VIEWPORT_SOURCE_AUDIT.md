# Calamus W95 — VS Code and Pulsar source audit for Undo, caret, selection and viewport

Date: 2026-07-30
Published baseline: `541804f8ff361b3afacb58f18e1e429c70b3a2f9`
Trigger: two consecutive failures of the mature-source rebuild line (R1 source-preflight callback-contract regression; R2 True GTK viewport failure).
Method: direct inspection of the uploaded archives and of the Calamus candidate source. No web or README substitution.

## Uploaded evidence

- Visual Studio Code stable Linux x64 archive: `code-stable-x64-1785237707.tar.gz`
  - SHA-256: `8632e6f9aed7a2c5612475559ff3d18c661d35432c226506db70444a99845731`
  - packaged product: Visual Studio Code 1.131.0
  - commit: `e4c7e7b1d6d060162f4aa7f8225271b67ce1df75`
  - build date: `2026-07-28T10:51:25Z`
  - caveat: this is a compiled release distribution, not the TypeScript source repository. The audit reads the shipped bundled JavaScript in `resources/app/out/vs/workbench/workbench.desktop.main.js`; class names and operational contracts remain present, but original module paths and comments are mostly lost.
- Pulsar archive: `pulsar-master.zip`
  - SHA-256: `670f3bfd253937c49cf52992461163a57c63c8f63a873ea17d902557341e52f0`
  - package version: `1.132.0-dev`
  - caveat: the repository contains the TextEditor integration and extensive specs, while the underlying `@pulsar-edit/text-buffer` implementation is an external dependency (`^14.0.4`) and is not embedded in the archive.
- T480 R2 validation log: `Pasted text(96).txt`
  - SHA-256: `11efeda069f09a1df29097433ffffeca852cb0ba9f666834a0447c61029f337f`

# 1. Calamus failure reconstructed from source and log

The R2 source-preflight passed 1,459 tests and the mature-history regression lanes. The True GTK gate then executed a real long-document edit, moved the cursor away, invoked the true `App.on_undo()`, restored the exact text and exact caret offset, and failed only on viewport projection:

```text
Undo caret outside viewport: caret_y=11381 visible=-10:637
```

The exact caret state was therefore correct. The remaining debt was not history state and not cursor inference. It was the view lane.

`calamus/calamus_history_runtime.py::queue_scroll_to_insert()` scheduled one low-priority idle and called `Gtk.TextView.scroll_to_mark()`. It cleared `scroll_source` when that callback returned. The gate waited only for `scroll_source is None` and then asserted the viewport.

This contract was insufficient in two ways:

1. completion of the application-owned idle did not prove that GTK's scroll geometry had accepted and projected the request;
2. `scroll_to_mark()` was asked to act while a full-buffer restore could still be updating the vertical adjustment range.

The R2 log proves that the insert mark location was already calculable (`y=11381`) but the visible rectangle remained at the top. A third timeout or repeated blind idle would only mask this missing view contract.

# 2. Visual Studio Code 1.131.0 — direct shipped-code audit

## Files and shipped symbols inspected

Primary shipped bundle:

- `resources/app/out/vs/workbench/workbench.desktop.main.js`

Relevant surviving symbols and code paths:

- serialized edit-stack data class containing:
  - `beforeVersionId`
  - `afterVersionId`
  - `beforeEOL`
  - `afterEOL`
  - `beforeCursorState`
  - `afterCursorState`
  - `changes`
- `SingleModelEditStackElement.undo()`
- `SingleModelEditStackElement.redo()`
- text model `_applyUndo(...)`
- text model `_applyRedo(...)`
- edit stack `pushEditOperation(...)`
- model `pushStackElement()` / `popStackElement()`
- editor `executeEdits(...)`
- view-model `setSelections(...)`
- editor reveal methods:
  - `revealAllCursors(...)`
  - `revealPositionInCenterIfOutsideViewport(...)`
  - `revealRangeInCenterIfOutsideViewport(...)`

## Undo/caret contract

The serialized edit-stack payload writes and reads complete arrays of selections both before and after the edit. Each selection stores four coordinates:

- selection start line;
- selection start column;
- active position line;
- active position column.

This preserves anchor/active-end identity and supports multiple cursors. The edit-stack element invokes:

```text
model._applyUndo(changes, beforeEOL, beforeVersionId, beforeCursorState)
model._applyRedo(changes, afterEOL, afterVersionId, afterCursorState)
```

Therefore Undo and Redo are not expected to infer a caret from the changed text. Cursor state is first-class action data.

`pushEditOperation(...)` accepts a pre-edit cursor state, applies edits, computes the post-edit cursor state through a cursor-state computer, and appends both the text changes and resulting cursor state to the same stack element.

`pushStackElement()` explicitly closes a group; `popStackElement()` can reopen the last compatible group. This confirms that grouping is a model contract, not a UI callback side effect.

## Viewport contract

VS Code exposes cursor/selection restoration independently from reveal methods. The view model can set selections without forcing a reveal. A caller may then issue an explicit reveal request.

The particularly relevant API is:

```text
revealPositionInCenterIfOutsideViewport(...)
```

This states the intended policy directly:

- if the cursor is already visible, preserve the viewport;
- if it is outside, center it through the view model.

The reveal request is interpreted by the editor's layout/view model, not by the Undo stack. It is therefore processed against valid view geometry.

## Immediate decision for Calamus

ADOPT/ADAPT:

1. keep the exact `HistoryState` before/after edit;
2. keep viewport projection separate from `TextHistory`;
3. define a named policy: center only if the caret is outside a safe visible area;
4. apply the policy through the scroll model (`GtkAdjustment`) after valid geometry exists;
5. keep one replaceable pending reveal request rather than stacking callbacks.

REJECT:

- treating idle callback completion as proof of viewport completion;
- blind repeated `scroll_to_mark()` calls;
- adding elapsed-time delays;
- moving cursor state into the view adapter.

## Future editor rewrite findings

A future Calamus editor should record, per edit group:

- before/after revision IDs;
- before/after selection arrays;
- inverse text changes;
- EOL/encoding-affecting metadata where relevant;
- a command/source descriptor;
- a merge/group boundary.

The document core should emit a cursor-state result from the edit itself. The view should consume a reveal intent after selection restoration. Search, Navigator, gutter and Research consumers should subscribe to document revisions rather than reread the whole text.

The compiled-release limitation means a later full VS Code architectural comparison should use the matching source commit archive. This is not required for the current Calamus repair because the shipped undo/cursor/reveal contracts are explicit.

# 3. Pulsar 1.132.0-dev — direct source and spec audit

## Files, classes and methods inspected

- `src/text-editor.js`
  - `undo(options = {})`
  - `redo(options = {})`
  - `transact(groupingInterval, fn)`
  - `abortTransaction()`
  - `createCheckpoint()`
  - `revertToCheckpoint(checkpoint)`
  - `groupChangesSinceCheckpoint(checkpoint)`
  - `setCursorBufferPosition(position, options)`
  - `setSelectedBufferRange(bufferRange, options)`
  - `setSelectedBufferRanges(bufferRanges, options)`
  - `scrollToCursorPosition(options)`
- `src/cursor.js`
  - `changePosition(options, fn)`
  - `autoscroll(options = {})`
- `src/selection.js`
  - `setBufferRange(bufferRange, options = {})`
  - `autoscroll(options)`
  - reversed-orientation handling
- `src/register-default-commands.js`
  - editor command transaction boundary
- `spec/text-editor-spec.js`
  - Undo/Redo text restoration
  - multiple-cursor grouping
  - exact cursor/selection restoration
  - transaction restoration
  - shared-buffer/multiple-editor selection ownership

## Undo/caret contract

`TextEditor.undo()` calls:

```javascript
this.buffer.undo({ selectionsMarkerLayer: this.selectionsMarkerLayer })
```

and only after buffer Undo completes calls:

```javascript
this.getLastSelection().autoscroll()
```

Redo follows the same order.

The `selectionsMarkerLayer` is passed into:

- Undo;
- Redo;
- transactions;
- checkpoints;
- grouping since checkpoint.

Selections are thus transaction/history participants, not reconstructed from plain ranges after the fact.

The public specs directly prove that Undo and Redo restore:

- several cursors simultaneously;
- multiple selected ranges;
- pre-edit and post-edit selection states;
- the initiating editor's selection when two editors share the same TextBuffer.

The transaction spec performs delete, cursor movement and insertion within one transaction, then proves that Undo restores the original selection and Redo restores the final collapsed caret.

This is especially relevant to Calamus `{{cursor}}`: the final caret belongs to the committed transaction state.

## Selection direction and view ownership

`Selection.setBufferRange()` accepts `options.reversed` and defaults to the selection's existing orientation. Autoscroll is optional and defaults only for the most recently added selection.

`Cursor.changePosition()` first changes semantic position, then optionally calls `autoscroll()`.

`Cursor.autoscroll()` converts the cursor to a screen range and delegates to `editor.scrollToScreenRange(...)`.

`Selection.autoscroll()` reveals either the directional selection range or the cursor. The view owns scrolling; the buffer owns text and marker transformations.

## Viewport contract

`TextEditor.scrollToCursorPosition()` calls the last cursor's autoscroll with centering enabled unless explicitly disabled. This is the same policy seen in VS Code: center only through a named view operation after semantic state is correct.

Pulsar does not make a raw timeout part of the Undo contract. It asks the display layer to reveal a screen range. The display layer can resolve that against current layout.

## Immediate decision for Calamus

ADOPT/ADAPT:

1. preserve exact selection direction;
2. apply Undo/Redo to the document/history first;
3. issue an independent autoscroll/reveal operation afterward;
4. center the final caret only when outside the visible safe region;
5. keep the reveal request replaceable, because a later cursor action supersedes an earlier view intent;
6. prove effects from text, marks and viewport—not callback return values.

REJECT:

- attaching viewport state to snapshot identity;
- adding a history level for cursor navigation;
- assuming that a generic scroller method has completed when the initiating callback returns.

## Future editor rewrite findings

Pulsar provides a strong model for a future view-independent Calamus API:

- one TextBuffer may back more than one editor view;
- each view owns its selection-marker layer and viewport;
- the shared document owns text history;
- transactions accept selection state explicitly;
- checkpoints allow provisional multi-step operations and rollback;
- command dispatch automatically wraps mutating editor commands in a transaction;
- the last/active selection alone drives default autoscroll.

For future Calamus, this suggests:

- document-level Undo with per-view selection state;
- checkpoint APIs for modal or preview-based transformations;
- reversible transactions for structural Markdown commands;
- a view adapter exposing `reveal_selection()` rather than widget-specific scrolling;
- tests with two views sharing one document.

The underlying `@pulsar-edit/text-buffer` source is absent from the uploaded archive. A later engine-level audit should include that package, but Pulsar's integration and executable specs are sufficient for the present view/history decision.

# 4. Revised Calamus contract after the two consecutive failures

## History lane — retained

`HistoryState(text, insert_offset, selection_bound_offset)` remains the minimum correct no-rewrite solution. R2 proved that exact text and caret restoration worked. The model is not rolled back.

## View lane — replaced

The retired view contract was:

```text
low-priority idle -> Gtk.TextView.scroll_to_mark() -> idle returned -> assume visible
```

The revised contract is:

1. restore exact text, insert mark and selection-bound mark;
2. create one replaceable pending reveal intent;
3. observe the real `GtkAdjustment` and TextView allocation;
4. attempt projection only when the vertical adjustment can represent the caret location;
5. calculate a clamped vertical adjustment from:
   - caret rectangle;
   - visible rectangle;
   - adjustment lower/upper/page size;
   - top margin;
6. preserve the viewport when the caret is already inside the safe region;
7. otherwise center the caret;
8. clear pending state only after the adjustment is applied or the caret is already visible;
9. cancel and replace an older reveal intent when a newer navigation/edit occurs;
10. disconnect geometry handlers during shutdown.

This is event-driven. There is no retry timeout and no sequence of guessed delays. If geometry is not ready, the request remains pending and is retriggered by `GtkAdjustment::changed` or `size-allocate`.

## True GTK proof

The gate must wait for both:

```text
scroll_source is None
reveal_pending is False
```

Only then may it inspect `get_visible_rect()`.

The test continues to require:

- real edit;
- navigation away;
- real `App.on_undo()`;
- exact text;
- exact caret;
- caret intersects visible rectangle;
- real Redo with exact final state.

# 5. Future rewrite synthesis added to MO

VS Code and Pulsar reinforce a future architecture with five explicit objects:

1. `DocumentModel`: text, revision, save point, file metadata;
2. `EditTransaction`: inverse edits, before/after selections, grouping and rollback;
3. `SelectionSet`: one or more directional caret/anchor pairs, per view;
4. `EditorViewAdapter`: layout and reveal intents only;
5. `RevisionBus`: deltas to Search, Navigator, gutter and Research clients.

The current W95 repair intentionally implements only the minimum bridge:

- snapshot history remains bounded;
- selection state is exact;
- view reveal is geometry-owned;
- no new editor dependency is introduced;
- no multi-caret, rope or incremental renderer is introduced.
