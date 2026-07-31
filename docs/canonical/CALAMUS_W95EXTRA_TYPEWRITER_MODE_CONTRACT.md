# Calamus W95extra — Typewriter Mode + Initial Writing Menu Contract

**Baseline:** W95 published commit `3fbbc8fc6107d7c8771933da41eb1e429972f0ff`
**Candidate line:** Mature-Source Rebuilt R2 after one harness-only R1 failure
**Publication:** forbidden until complete True GTK and manual desktop PASS

## Scope

W95extra adds:

1. Typewriter Mode as a session-only view policy;
2. one top-level Writing menu containing exactly:
   - Typewriter Mode — `Shift+F9`;
   - Insert Date;
   - Insert Time;
   - Insert Date and Time — `Ctrl+Alt+D`;
3. complete User Guide and shortcut-registry coverage;
4. one shared editor viewport runtime used by W95 History and Typewriter.

## Typewriter invariants

- The document buffer is never modified by the mode.
- No Undo step is created by scrolling or runway changes.
- Insert mark and selection bound remain semantic History state.
- Exactly one runtime writes the vertical adjustment.
- The horizontal adjustment is never touched.
- Every target uses measured iter/visible/adjustment geometry.
- A request is replaceable and waits for real layout signals when geometry is not ready.
- No timer retry loop, polling, line-height guess or animation is permitted.
- The beginning remains naturally top-aligned until the midpoint is attainable.
- The last visual line can reach the midpoint through a view-only bottom runway.
- Pointer press/drag, non-empty selection, manual scroll and focus loss suppress projection.
- Edit, keyboard movement, Undo/Redo and explicit structural navigation resume projection.
- Releasing the pointer alone never snaps the viewport back.
- Disable and shutdown restore the exact pre-mode bottom margin.

## Menu taxonomy decision

- `Writing` owns Typewriter Mode and the three date/time insertion commands. Date/time commands must not be duplicated under `Revise`.
- Bookmarks are semantic navigation positions and therefore belong under `Navigate`, not `Writing` or `Revise`. Their callbacks and shortcuts remain unchanged.
- `Paste Clean from PDF` and `Clean Selected Text from PDF` clean or transform imported/existing text and therefore remain under `Revise`.
- The real GTK/App gate must verify positive placement and negative absence in the other menus; Help and shortcut registry must use the same taxonomy.

## Writing command invariants

- Date format: `%Y-%m-%d`.
- Time format: `%H:%M`.
- Date and time format: `%Y-%m-%d %H:%M`.
- Formatting is dispatched through `writing.insert-date-time` with explicit time and format.
- GTK mutation uses the existing grouped editor command boundary.
- All three insertions are undoable.

## GTK boundary

GTK-free:

- `calamus_viewport.py`;
- `calamus_typewriter.py`.

GTK/runtime boundary:

- `calamus_viewport_runtime.py`;
- `calamus_typewriter_runtime.py`;
- `calamus_typewriter_app.py`;
- menu and App wiring.

## Mandatory gate markers

```text
W95EXTRA_SCOPE=PASS
W95EXTRA_HEADLESS_REGRESSION=PASS
W95_TRUE_GTK_APP_GATE=PASS
W95EXTRA_REAL_WRITING_MENU=PASS
W95EXTRA_REAL_TYPEWRITER_MIDPOINT=PASS
W95EXTRA_REAL_MANUAL_SCROLL_RESUME=PASS
W95EXTRA_REAL_DISABLE_RESTORE=PASS
W95EXTRA_REAL_DATE_TIME_COMMANDS=PASS
W95EXTRA_REAL_HELP=PASS
W95EXTRA_TRUE_GTK_APP_GATE=PASS
W95EXTRA_GTK_LANES=PASS
W95EXTRA_MANUAL_DESKTOP_ATTESTATION=PASS
```

Any jitter, block jump, oscillation, pointer fight, false menu state, stale runway, horizontal movement, document mutation, failed historical W95 gate or residual process is a FAIL.
