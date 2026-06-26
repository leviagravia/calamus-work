# Calamus Phase 5.6 — Code Quality + Bugfix batch

Scope: feature freeze. No new user-facing features were added.

Changes:
- fixed Clip Collection double-click insertion using a ListBox-level mouse double-click handler;
- kept Enter inactive for clip insertion, by avoiding Gtk.ListBox row-activated;
- corrected the Favourites menu label to `Ctrl+Alt+B`;
- aligned shortcut audit metadata with the real shortcut table;
- kept runtime `__pycache__` handling non-fatal in selftest;
- updated regression tests for the Clip Collection activation path.

Version: 1.7.0~rc2+phase5.6.
