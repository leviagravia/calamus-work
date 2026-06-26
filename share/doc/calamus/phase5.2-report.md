# Calamus Phase 5.2 Report — UI Separation

## Goal
Separate GTK menu and shortcut wiring from the main application class without changing user-visible behaviour.

## Changes
- Added `/usr/lib/calamus/calamus_ui.py`.
- Moved top-level menu construction out of `/usr/bin/calamus`.
- Moved accelerator/shortcut registration out of `/usr/bin/calamus`.
- Kept compatibility wrappers in `App` for dynamic menus such as Recent Files.
- Added shortcut conflict detection inside the UI wiring layer.
- Added a lightweight UI-wiring regression test; it is skipped only when PyGObject is unavailable in the test environment.
- Version aligned to `1.7.0-rc2+phase5.2` in the app and `1.7.0~rc2+phase5.2` in Debian metadata.

## Non-goals
- No new features.
- No intentional UX, menu, or shortcut changes.
- No GTK4 migration.

## Validation
- Python syntax validation: OK.
- Non-GUI selftest in build container: OK, 24 passed + 1 UI test skipped because PyGObject is not installed in the container.
- Expected installed-system result with package dependencies present: UI test should run instead of skip.

## Notes
`/usr/bin/calamus` is still the largest file, but menu/shortcut construction is no longer embedded in the main class body. The next useful cleanup step is Phase 5.3: state/preferences/session consolidation.
