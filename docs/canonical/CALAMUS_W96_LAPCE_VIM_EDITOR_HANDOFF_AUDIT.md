# Calamus W96 — Direct Lapce and Vim editor-handoff audit

Date: 2026-08-01

## Scope and provenance

This audit reads the uploaded source archives directly. No web research was used.

- `lapce-master(1).zip` — SHA-256 `7035f97fa04d26ba04d18ef991dcff0365573ee08285ed205aef3ab9414fd3da`
- `vim-master.zip` — SHA-256 `951efd91d9f9a8d00576c5a99f2cb564795189575b63eff7eb3159b3704b7c8a`

The immediate Calamus evidence is the dedicated desktop-profile log in which
cursor movement and `Gtk.TextView` focus had succeeded, while the only failed
assertion was `Gtk.Window.is_active()` after the user activated another editor.

Classification: `CALAMUS-DESKTOP-WM-ACTIVE-ORACLE-01`.

## Lapce

### Files read

- `lapce-app/src/editor.rs`
- `lapce-app/src/editor/view.rs`
- `lapce-app/src/main_split.rs`
- `lapce-app/src/window_tab.rs`
- `lapce-app/src/app.rs`
- `lapce-app/src/command.rs`

### Findings

`EditorData::go_to_position()` converts the semantic position into an exact
offset, sets the editor cursor, and optionally sets the editor scroll target.
The navigation result is therefore represented by editor-owned state.

The editor view's `ensure_visible` closure derives a cursor rectangle from the
current cursor offset, compares it with the viewport, and requests the minimum
scroll needed to reveal it. Cursor visibility is an editor/viewport invariant,
not a claim about which desktop application globally owns focus.

`FocusEditor` changes Lapce's internal focus model to `Focus::Workbench`.
`WindowGotFocus`, by contrast, updates a separate `window_focus` signal used by
the window layer. Lapce does not make the global window-manager focus event the
success criterion for `go_to_position()`.

`MainSplitData::jump_to_location()` first records jump history and then delegates
to `go_to_location()`. History, editor position, viewport and window focus remain
separate responsibilities.

### Decision for Calamus

ADOPT:

- exact cursor/selection as command state;
- viewport visibility as a separate invariant;
- internal editor focus as a separate invariant;
- external window-focus observation separated from command success.

ADAPT:

- Calamus still calls `Gtk.Window.present()` because it navigates from a distinct
  non-modal tool window, but the automatic release gate certifies the call/order
  and the internal editor result rather than a transient window-manager outcome.

REJECT:

- `Gtk.Window.is_active()` as a portable automatic PASS/FAIL oracle.

## Vim

### Files read

- `src/move.c`
- `src/edit.c`
- `src/normal.c`
- `src/window.c`
- `src/gui.c`
- `src/testdir/test_edit.vim`
- `src/testdir/test_scroll_opt.vim`

### Findings

`update_topline()` explicitly updates the current window's `w_topline` so the
cursor is on screen. It reasons from cursor line, top line, bottom line, window
height, folds and scroll context. `validate_cursor()` then validates the cursor's
window row and column after the viewport is valid.

This is an important two-stage contract:

1. cursor position and viewport are made coherent;
2. screen-relative cursor coordinates are validated.

The tests inspect deterministic editor state such as `getpos('.')` and
`winsaveview()['topline']`. For example, `Test_edit_CTRL_EY()` verifies both the
cursor position and the resulting top line. It does not require Vim to be the
operating system's globally active application.

GUI focus handling exists in Vim, but cursor/viewport correctness is not defined
by the external window manager granting focus at the exact instant of an
assertion.

### Decision for Calamus

ADOPT:

- exact cursor/selection plus viewport visibility as the release invariant;
- explicit validation after movement;
- deterministic state assertions independent of unrelated desktop activity.

ADAPT:

- Calamus uses GTK `scroll_to_iter()` and TextView geometry instead of Vim's
  `w_topline`, `w_wrow` and `w_wcol`, while preserving the same separation.

REJECT:

- global desktop active-window state as proof that cursor navigation succeeded.

## Frozen W96 rule

A Document Overview navigation is automatically certified when all applicable
internal invariants hold:

1. the exact offset or selection is installed;
2. the main Calamus window is mapped and visible;
3. the TextView is the focus widget inside Calamus;
4. the target intersects the TextView viewport;
5. the application boundary called `present()` before `grab_focus()`.

`Gtk.Window.is_active()` may be emitted as a diagnostic observation. It must not
be asserted by an automatic release profile because the desktop window manager,
the user, or another process may change it asynchronously.

The manual validation remains the authority for the human-visible handoff from
Document Overview to the editor.
