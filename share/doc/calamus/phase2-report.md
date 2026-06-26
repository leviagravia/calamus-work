# Calamus phase 2 report

Scope: split recurring GTK dialog code out of `/usr/bin/calamus` while preserving the GTK3 runtime and existing behaviour.

## Changes

- Added `/usr/lib/calamus/calamus_dialogs.py`.
- Moved or delegated these UI responsibilities out of the main `App` class:
  - message dialogs (`info`, `large_info`, `error`);
  - unsaved-changes confirmation;
  - open/save file chooser dialogs;
  - Go to Line dialog;
  - Find / Replace dialog construction and response loop;
  - External Spellcheck suggestion dialog;
  - Keyboard Shortcuts dialog and shortcut table;
  - About dialog and About-specific CSS.
- Updated package and runtime version to `1.7.0~rc2+phase2` / `1.7.0-rc2+phase2`.

## Result

The main script remains the application controller, but dialog construction is now isolated in a dedicated module. This reduces the amount of GUI boilerplate inside `App` and prepares the next phases for cleaner separation of menus, state, and editor behaviour.

## Validation

- `python3 -m py_compile` passes for `/usr/bin/calamus` and all modules in `/usr/lib/calamus`.
- Package metadata updated.
