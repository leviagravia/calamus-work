# W102 Candidate R1 Failure and Candidate R2 Repair

## Status

- Baseline: `17b409a05f356477173b2bdd348a67a4cf01f43c`
- Candidate R1: retired, FAIL 1/2
- Candidate R2: test-authority repair; product implementation unchanged
- Canonical repository: not mutated

## R1 observed failure

The T480 automated sequence completed:

- full discovery: 1700 tests, PASS, 48 ambient GTK skips;
- W102 current identity true-App: PASS;
- W102 DocumentSession true-App: PASS;
- W101 composition true-App: PASS;
- W99 lifecycle true-App: PASS.

The historical W98 product-smoke fixture then executed:

```python
win.modified = False
```

W102 correctly makes `App.modified` a read-only projection of the authoritative
GTK-free `DocumentSession`. The assignment therefore raised `AttributeError`.
The failure happened before manual desktop validation.

## Root cause

R1 migrated product code and headless tests away from mutable App mirrors, but
its audit did not include every conditionally executed historical GTK fixture.
Full discovery could not expose the defect locally because those fixtures are
skipped without a real GTK display. This was a test migration gap, not a
runtime/session transition failure.

## R2 repair

R2 migrates every identified real-App fixture that directly mutated W102
read-only projections:

- `tests/test_w98_research_panel_app_desktop_e2e.py`
  uses `document_session.mark_clean()` before normal close and cleanup;
- `scripts/w95-true-gtk-app-gate.py`
  uses `document_session.mark_clean()` during cleanup;
- `tests/test_workspace_app_desktop_e2e.py`
  uses `document_session.mark_modified()` for deterministic dirty fixtures.

A new AST contract test scans these true-App fixtures and rejects assignments
to `modified`, `current_file`, `loading`, or `document` on `app`/`win`.

## Product delta

None. R2 changes no Calamus runtime module relative to R1. The repair is limited
to historical GTK fixtures, release-profile inventory, tests, and canonical
evidence.

## Acceptance barrier

R2 must rerun the complete automated T480 sequence. It may reach manual desktop
validation only after W102, W101, W99, and W98 true-App profiles all pass.
