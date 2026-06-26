# Calamus Phase 5.4.1 Report

Hotfix for Phase 5.4 selftest audit scope.

## Fixed

- The release audit no longer scans the whole `/usr` tree.
- Python compile checks are limited to Calamus paths only:
  - `/usr/bin/calamus`
  - `/usr/bin/calamus-selftest`
  - `/usr/lib/calamus`
  - `/usr/share/calamus`
- `__pycache__` checks are limited to Calamus package paths only.
- This avoids false failures caused by unrelated system packages.

No feature or UX changes.
