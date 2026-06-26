# Calamus Phase 5.4.2 — UI Bugfix Pack

Applied conservative UI fixes for the test build.

## Fixed
- Clip Collection is hidden by default and opens only via View > Clip Collection.
- Clip Collection is hosted in a horizontal Gtk.Paned layout instead of taking over the whole window.
- Clip Collection shortcut changed from Alt+F10 to Ctrl+Alt+C to avoid common window-manager conflicts.
- Clip buttons reduced to compact Add / Insert / Delete controls.
- Window title shows saved state: `(saved)` or `(not saved)`.
- Document Statistics remains exposed explicitly from Tools > Document Statistics and Ctrl+Alt+W.
- Selftest shortcut audit updated for Ctrl+Alt+C.

## Scope
No new feature work in this phase; this is a bugfix/stability package.
