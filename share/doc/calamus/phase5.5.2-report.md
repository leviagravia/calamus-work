# Calamus Phase 5.5.2 — Clip UX cleanup

Scope: feature freeze micro-release. No new features.

Changes:
- Removed Enter-to-insert behavior from Clip Collection.
- Kept mouse double-click to insert selected clip.
- Kept Insert button and Ctrl+Alt+1..9 clip insertion shortcuts.
- Added regression coverage to ensure Clip Collection does not use Gtk.ListBox row-activated, avoiding implicit Enter activation.
- Version aligned to 1.7.0-rc2+phase5.5.2 / 1.7.0~rc2+phase5.5.2.
