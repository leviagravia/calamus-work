# Calamus W95extra — Typewriter Mode Mature-Source Re-Audit

**Date:** 2026-07-31
**Baseline:** W95 published, `3fbbc8fc6107d7c8771933da41eb1e429972f0ff`
**Status:** BINDING ARCHITECTURAL AUDIT FOR THE POST-TWO-FAIL REBUILD
**Implementation line:** Mature-Source Rebuilt Candidate R1; not an incremental R3

## 1. Why this audit exists

Two W95extra validation attempts were retired before a desktop Typewriter verdict:

1. R1 stopped in the headless harness because it required an unavailable external `pytest` module.
2. R2 passed 1,499 source tests, then stopped in the historical W95 True GTK gate because the Research-selector popover had mapped at `1x1` before receiving usable allocation.

The second failure did not prove that the Typewriter runtime was wrong, but the Calamus method is stricter: after two failed candidates the patch line is withdrawn, the source is re-read, mature precedents are re-audited, and a unitary candidate is reconstructed from the last published baseline. R1/R2 are negative evidence only; their patch is not the authority for this rebuild.

## 2. Historical Calamus constraints re-read

### Entry 222 — measured-scroller prerequisites

The canonical MO already required: measured iterator rectangle, measured viewport, direct vertical-adjustment target, keyboard/mouse distinction, no centering during pointer drag, resize protection, wrapped-line and boundary tests, and no `scroll_to_iter` guessing loop.

### Entry 245 — reason for historical retirement

The old implementation remains permanently retired because it produced jitter and non-deterministic scrolling. `Gtk.TextView.scroll_to_mark()` alone is not a deterministic Typewriter engine. Apostrophe was recorded as proof that a dedicated geometry-owned scroller is possible.

### W95 — the new enabling foundation

W95 changed the relevant architecture:

- `calamus_history.HistoryState` records text, insert offset and selection-bound offset.
- `calamus_history_runtime.restore_buffer_state()` restores marks semantically before presentation.
- `SnapshotHistoryRuntime` has one replaceable, event-driven reveal request.
- `bin/calamus::on_cursor_position_notify()` explicitly refuses unconditional scroll because mouse clicks and selection previously produced block jumps.
- W95 desktop evidence certified exact cursor extremes, selection direction, Undo/Redo and viewport restoration.

W95 therefore supplies the semantic state and measured one-shot reveal that the historical Typewriter attempt lacked. It does not by itself supply a persistent Typewriter policy.

## 3. Direct re-audit of Calamus W95 source

### `calamus/calamus_editor.py`

The real editor topology is `Gtk.TextView` as the direct child of `Gtk.ScrolledWindow`; the line-number gutter is external. The view already supports top/bottom margins, wrapped visual lines, pointer/key events, `size-allocate`, visible rectangles and vertical adjustment access.

**Decision:** ADOPT unchanged. No editor-widget replacement and no GtkSourceView migration are required for W95extra.

### `calamus/calamus_history.py`

History snapshots own document and mark state, not the viewport. Undo receives the current view state and returns the exact preceding state; Redo returns the exact later state.

**Decision:** PRESERVE. Typewriter never enters the history model and never creates an Undo record.

### `calamus/calamus_history_runtime.py`

The W95 implementation combined snapshot coordination with its own vertical-adjustment write. That is safe for a one-shot History reveal but cannot coexist with a second persistent writer without races.

**Decision:** ADAPT by extracting the projection lane into one `EditorViewportRuntime`. History delegates to it; the semantic snapshot contract remains unchanged.

### `bin/calamus`

Relevant signal order and gateways:

- `begin-user-action` / `end-user-action` delimit semantic edits;
- `changed` invalidates projections and updates history;
- `move-cursor` represents keyboard-style semantic movement;
- pointer press/release, motion, wheel/trackpad scroll and focus loss are available;
- `set_cursor_offset()` is the programmatic navigation gateway;
- `set_text_from_history()` restores exact state before reveal;
- `on_destroy()` owns runtime shutdown.

**Decision:** ADAPT with thin signal classification. Keep `notify::cursor-position` non-scrolling.

### `calamus/calamus_ui.py`, `calamus_shortcuts.py`, Help

The published runtime had no top-level Writing menu. Date/time was under Revise and Typewriter was absent. The user authorized an initial bounded menu containing exactly Typewriter Mode, Insert Date, Insert Time, and Insert Date and Time.

**Decision:** ADD one real top-level Writing menu between Navigate and Revise, a checked Typewriter item with unique `Shift+F9`, and three insertion commands. Help and shortcut registry must describe exactly this live surface.

### `scripts/w95-true-gtk-app-gate.py`

The R2 failure exposed a gate race: the predicate waited only for `mapped=True`; GTK could map a popover shell at `1x1` before allocation. The subsequent immediate allocation assertion then failed.

**Decision:** REPAIR THE HARNESS, not the Research product. Wait semantically until popover, scroller, list and rows are visible, realized, mapped and positively allocated, then assert. No millisecond guess is introduced.

## 4. Mature-source findings

### 4.1 Apostrophe (GNOME editor; prior direct source audit retained in MO)

`TextViewScroller` owns measured iterator and viewport geometry, distinguishes keyboard and pointer movement, waits until pointer release, reacts to resize and owns any animation. Focus layout and Typewriter scrolling are separate concerns.

**ADOPT:** dedicated scroller boundary, measured geometry, pointer/keyboard lifecycle.
**REJECT:** reviving old Calamus code or sharing scroll ownership among features.

### 4.2 QOwnNotes / QMarkdownTextEdit (prior direct source audit)

`MainWindow::on_actionTypewriter_mode_toggled()` passes the setting into the editor component; centering is an editor concern, separate from fullscreen/distraction-free, and is suppressed while a mouse button is held.

**ADOPT:** checked command, editor ownership, pointer suppression.
**ADAPT:** Qt native `centerCursor()` cannot be copied into GTK.

### 4.3 GNOME Text Editor

Direct files/functions:

- `src/editor-source-view.c::editor_source_view_update_overscroll()` sets bottom margin to 75% of the visible height.
- `editor_source_view_jump_to_iter()` reads iter location, visible rectangle, top margin and adjustments, then writes a deterministic target.

**ADOPT:** dynamic view-only runway and direct measured adjustment.
**ADAPT:** Calamus uses 55% for a 50% working line with visual-row/rounding surplus; no animation in the first release.

### 4.4 GtkSourceView

Direct function: `gtksourceview/gtksourceutils.c::_gtk_source_view_jump_to_iter()` reconstructs reveal from iter rectangle, visible rectangle, margins and adjustments, preserving independent horizontal and vertical decisions.

**ADOPT:** geometry math and clamp discipline.
**DEFER:** full migration from `Gtk.TextView`; it is not necessary for this work item.

### 4.5 Xed

Direct functions include `xed_view_scroll_to_cursor()`, `gtk_text_buffer_place_cursor()`, grouped `begin_user_action/end_user_action`, and search/navigation paths that place/select first and reveal afterward.

**ADOPT:** semantic marks before presentation and grouped edits.
**REJECT:** ordinary `scroll_to_mark()` as the complete persistent Typewriter engine.

### 4.6 Gedit

`gedit_view_scroll_to_cursor()`, file-load idle reveal, explicit cursor placement and plugin user actions maintain the same separation: mutation/selection first, view reveal later.

**ADOPT:** ordering and lifecycle.
**REJECT:** treating the normal ensure-visible helper as continuous centering.

### 4.7 Mousepad

Mousepad restores or places the insert mark and then uses ordinary view visibility. It is a conservative baseline for normal editor behavior but has no persistent midpoint, runway or input-origin classifier.

**ADOPT:** non-Typewriter fallback behavior.
**REJECT:** assuming the baseline helper satisfies W95extra.

### 4.8 Visual Studio Code / Monaco integration

Selections are explicit before/after state, while the editor view receives a separate reveal intent such as center-if-outside. View state is not inferred from the textual diff.

**ADOPT:** semantic state and projection as separate contracts.
**REJECT:** Typewriter state in Undo data.

### 4.9 Pulsar

`Selection` exposes autoscroll as an explicit option; the editor component owns scrolling after markers/selections are updated. Transactions/checkpoints and view autoscroll are distinct.

**ADOPT:** per-view projection after semantic restoration and the ability to suppress autoscroll during intermediate selection work.
**REJECT:** coupling Typewriter to buffer transactions.

### 4.10 BufferScroll

Direct file `BufferScroll.py::on_modified()` saves horizontal viewport position, calls `show_at_center(point)`, then restores X while retaining the new Y. Other paths store/restore viewport positions explicitly.

**ADOPT:** vertical-only Typewriter authority and horizontal preservation.
**REJECT:** its broad event/persistence/polling surface as a model for Calamus.

Archive SHA-256: `c6b2ff04e0c912788eda64d09d3c8dc5d4fd57da062605cac3993d312dc8a938`.

### 4.11 Logseq Typewriter Mode

Direct files `src/main.ts` and `src/utils.ts` use `ResizeObserver`, measured cursor/container rectangles and direct `scrollTop`; visible floating popups suppress scrolling. The implementation uses throttle and optional smooth animation.

**ADOPT:** resize awareness, correct scroll-container selection and popup/focus suppression.
**REJECT:** throttle delays, smooth animation and potentially stale asynchronous promises in W95extra.

Archive SHA-256: `fe0b23b123f60fc924ddebaef06f82673694357a757ed0906be2a1124c33cda7`.

### 4.12 MadEdit-Mod

Direct files under `src/MadEdit/` update `m_TopRow` from exact line/subrow deltas during insert, delete, wrap and reformat. Typewriter behavior is integrated into the editor’s own visual-row engine.

**ADOPT:** visual-row geometry rather than logical-line estimates.
**REJECT:** porting its proprietary layout engine or maintaining a second row model beside GTK.

Archive SHA-256: `884650448dd4ea1fb47c9a284b120d592a3aaa354ebccfc6517156892b53ea36`.

### 4.13 Obsidian Scroller

The compiled `main.js` coalesces work with one animation frame, measures the caret and supports fixed position or safe-band behavior. It suppresses inappropriate selection cases and cancels obsolete animation work.

**ADOPT:** replaceable/coalesced request, fixed target and bounds.
**REJECT:** wheel-to-cursor movement and browser animation as first-release behavior.

Archive SHA-256: `6574541b62a49ff31f23b0cdd35e2a5931a8cc5b3ceb43f4cfcd9e23cf1b1782`.

### 4.14 Obsidian Typewriter Mode

Direct files:

- `src/cm6/plugin.ts`: rejects `select.pointer`, separates measure/write via `requestMeasure`, observes resize and tracks user-event classes.
- `src/cm6/typewriter-offset-calculator.ts`: computes caret height, active-line offset, target offset, bounds and “only maintain when reached”.
- `only-maintain-typewriter-offset-when-reached.ts`: explicitly avoids blank space at the top until the target is naturally reached.

**ADOPT:** event classification, read/write separation, resize, latch-on-reach and no forced blank top.
**ADAPT:** GTK low-priority idle plus `changed/size-allocate` replaces CodeMirror `requestMeasure`.

Archive SHA-256: `96e534f08e692abd81360dd1ad143b4d8e2795640141eb2518413df931d6d051`.

### 4.15 typewriter-roll-mode

`typewriter-roll-mode.el` installs targeted command hooks and uses window-start/recenter policies; the accompanying ERT suite explicitly checks cursor and top-line behavior, scroll margins and regressions.

**ADOPT:** explicit lifecycle and boundary-focused tests.
**REJECT:** `fill-paragraph()` or any document mutation as part of viewport mode.

Archive SHA-256: `19977cabaa5d99ca04c9f84939fe987be2f9b0516dcf3ee73ed70ec463b8665f`.

### 4.16 VSCode-TypewriterScrollMode

`src/extension.ts::_onTextDocumentSelectionChanged()` centers every selection event with `revealRange(...InCenter)` and has no pointer classifier, runway, resize contract, final-line proof or substantive tests.

**Decision:** REJECT as a counterexample. It reproduces the “simple callback” design that historically caused Calamus jitter.

Archive SHA-256: `55585f82afa616705e27527589c440927b3e4da4ab09aa44674a97c03b992a6e`.

### 4.17 write0

`components/Editor.tsx::centerCaretInTextarea()` mirrors textarea typography, measures a marker at `selectionStart`, computes a clamped midpoint and writes `scrollTop`; pending requests are applied after layout. CSS supplies bottom space.

**ADOPT:** post-layout measurement, clamp and runway.
**REJECT:** a DOM mirror in GTK and browser-specific triggering.

Archive SHA-256: `4f9e0c9919ae2ea9140d906e43dbe41c87a0caa163acb3b4f0176854058475fc`.

## 5. Frozen architecture

### 5.1 One viewport owner

`EditorViewportRuntime` is the only component permitted to write the editor vertical adjustment or temporary Typewriter bottom margin.

Producers submit intents:

- History/ordinary navigation: ensure-visible or center-if-outside;
- Typewriter: persistent midpoint policy;
- pointer/manual scroll: cancellation/suspension, not a competing target.

A new intent replaces the older one. Geometry not yet ready keeps the intent pending until a real `adjustment::changed` or `size-allocate` event; no retry timeout is used.

### 5.2 GTK-free policy

- `calamus_viewport.py`: measured geometry, clamp and ordinary reveal.
- `calamus_typewriter.py`: target fraction, runway, latch-on-reach and tolerance.

They import no GTK and are exhaustively unit-tested.

### 5.3 GTK runtime

- `calamus_viewport_runtime.py`: geometry measurement, one low-priority projection, single adjustment write, runway ownership and lifecycle disconnect.
- `calamus_typewriter_runtime.py`: state and event-origin classification only; no buffer mutation and no adjustment write.
- `calamus_typewriter_app.py`: thin App callbacks.

### 5.4 First-release behavior

- midpoint target: 50%;
- runway: 55% of current page size plus existing bottom margin;
- no animation;
- natural document start until midpoint is attainable;
- pointer press/drag, non-empty selection, manual scroll and focus loss suppress projection;
- edit, keyboard movement, Undo/Redo and explicit structural navigation resume;
- horizontal adjustment untouched;
- setting session-only;
- independent from Focus and Distraction-Free modes.

## 6. Writing menu contract

The live menu is exactly:

```text
Writing
├── Typewriter Mode              Shift+F9
├── Insert Date
├── Insert Time
└── Insert Date and Time         Ctrl+Alt+D
```

Date/time commands pass an explicit `datetime` and explicit format through `writing.insert-date-time`, then mutate the GTK buffer through the existing grouped `execute_command()` gateway. They remain undoable and do not bypass CommandLayer.

## 7. Negative rules

The rebuilt candidate must contain none of the following:

- old Typewriter code or an incremental R1/R2 patch base;
- unconditional scrolling from `notify::cursor-position`;
- independent History and Typewriter adjustment writers;
- repeated `timeout_add`, polling or guessed line heights;
- centering during pointer drag or a non-empty pointer selection;
- document padding characters/blank lines;
- horizontal scroll mutation;
- smooth animation in the initial release;
- persistent setting added without a separate lifecycle decision;
- fake menu/Help exposure without real App activation.

## 8. Required evidence before desktop attestation

1. baseline/source provenance and exact file-set gate;
2. Python compile and Bash syntax;
3. full source selftest without external `pytest` dependency;
4. pure policy and fake-runtime tests;
5. historical W95 True GTK gate, with allocation-aware Research selector wait;
6. real App Writing-menu activation;
7. real midpoint geometry and runway;
8. pointer/selection/manual-scroll suppression and semantic resume;
9. final-line behavior, Undo/Redo and exact disable restore;
10. actual User Guide navigation to Writing and Typewriter Mode;
11. normal-close lifecycle and no residual process;
12. manual desktop checklist on an isolated candidate.

## 9. Audit conclusion

Typewriter Mode is feasible on Calamus’ current `Gtk.TextView`, but only under the frozen single-owner viewport architecture. The mature-source rebuild is materially different from the two retired candidates: it begins from W95, moves the W95 reveal into a shared viewport owner, treats input origin as first-class state, preserves natural start, uses a measured runway, and makes the new Writing menu and Help part of the real App gate.
## 14. Post-R1 menu taxonomy and gate correction

Mature-Source Rebuilt R1 reached the real GTK/App lane after all 1,499 source tests and the historical W95 gate passed. It stopped only because the Help test required the exact substring `manual scrolling`, while the visible guide truthfully described the same contract as wheel, touchpad or scrollbar usage performed manually. The product behavior had already passed the real manual-scroll suspension/resume assertions. R2 therefore repairs the semantic Help assertion rather than changing runtime behavior.

The user also froze menu taxonomy: bookmarks are navigation targets and move to `Navigate`; date/time exists only under `Writing`; both PDF cleaning commands remain under `Revise`. Positive and negative real-App tests prevent future duplication or drift.
