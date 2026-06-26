# Calamus Phase 5.4 — Regression & Stability Pass

Scope: no new end-user features. This pass extends automated regression checks and adds a shortcut/release audit layer.

Changes:
- Added `calamus_audit.py` with a canonical shortcut audit table.
- Added duplicate shortcut detection independent from GTK.
- Added explicit audit coverage for requested shortcuts:
  - Character Map: `Ctrl+Alt+F10`
  - Clip Collection: `Alt+F10`
- Documented `Alt+F10` as potentially intercepted by some window managers.
- Extended `calamus-selftest` with:
  - `--full`
  - `--list-shortcuts`
- Added package hygiene tests:
  - Python source compilation
  - no `__pycache__`
  - launcher/selftest executability
  - required module presence
- Added extra regression coverage for writing tools and state fallback.

Expected selftest result in this build environment: all non-GTK tests pass; GTK-specific UI wiring may skip on headless/container systems without PyGObject.
