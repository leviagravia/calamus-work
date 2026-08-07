# W105 Mature Source Comparison

Direct source files from the user-supplied mature corpus were inspected.

## GNOME Text Editor

Files:
- `editor-window-actions.c`
- `editor-window.c`
- `editor-page-actions.c`

`_editor_window_actions_update()` derives booleans such as `has_page`,
`can_save`, `modified`, `draft`, `externally_modified` from authoritative page
and document state, then projects them with `gtk_widget_action_set_enabled()`.
Window signal/binding groups trigger that update when the active page changes.

ADOPT:
- compute state from authorities, then project;
- one coherent update function for a state domain;
- action ID is the projection key.

ADAPT:
- Calamus core projection must remain GTK-free; only its adapter calls GTK.

## gedit

File: `gedit-window.c`.

`set_sensitivity_according_to_tab()` derives Save/Save As/Undo/Redo/Cut/Copy/
Paste/Search state from tab/document/view facts. A separate
`set_sensitivity_according_to_window_state()` derives window-wide action-group
state. Toggle action state is synchronized separately from actual panel/window
visibility.

ADOPT:
- explicit fact domains;
- grouped projection instead of scattered callback-local widget mutation.

REJECT:
- deprecated GtkAction/GtkActionGroup API itself;
- plugin extension state fan-out.

## Pluma

File: `pluma-window.c`.

Pluma follows the same mature pattern: document/tab state is sampled, then
actions are updated centrally; save/undo/selection sensitivity is not owned by
the menu callback that executed the previous command.

ADOPT:
- central projection and authoritative facts.

REJECT:
- old GtkAction implementation details.

## NotepadNext

File: `MainWindow.cpp`.

It has named update functions such as:
- `updateFileStatusBasedUi()`
- `updateSaveStatusBasedUi()`
- `updateEditorPositionBasedUi()`
- `updateLanguageBasedUi()`
- `updateSelectionBasedUi()`
- `updateContentBasedUi()`

These derive QAction enabled/checked state from editor facts. The source also
shows the downside of letting many update functions accumulate in MainWindow.

ADOPT:
- state categories and derivation.

REJECT:
- putting the entire projection controller back into the monolithic window.

## Kate

File: `katemainwindow.cpp`.

Stable actions are updated from explicit facts (`hasUrl`,
historyBackEnabled/historyForwardEnabled) and checked state reflects settings.
Action objects remain a view/action layer rather than domain authorities.

ADOPT:
- stable action ID + explicit fact projection.

REJECT:
- plugin/action-collection breadth outside Calamus scope.

## Airpad

File: `window.c`.

Airpad directly calls check-menu and sensitivity setters from window callbacks,
including clipboard-state handling.

Classification: NEGATIVE PRECEDENT. This resembles the coupling W105 should
remove, not emulate.

## Convergent lesson

Across mature editors, the robust pattern is:
1. authoritative model/runtime facts first;
2. action/menu state derived from those facts;
3. one projection update boundary;
4. UI controls are outputs, not model state;
5. execution and availability/check projection remain distinct.
