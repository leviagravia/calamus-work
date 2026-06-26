# Calamus 1.7.0~rc3 — Phase 5.8 Release Candidate

Feature freeze remains active. This build is a release-candidate consolidation package.

## Changes

- Version promoted to 1.7.0~rc3.
- Help/About text replaced with a concise user-facing description of Calamus.
- No new runtime dependencies.
- No intentional UX or shortcut changes.
- Previous stability fixes retained, including Clip Collection double-click insertion and Enter disabled for clip insertion.

## Validation target

Run:

```bash
calamus-selftest --full
```

Expected result: all non-GUI regression tests pass.
