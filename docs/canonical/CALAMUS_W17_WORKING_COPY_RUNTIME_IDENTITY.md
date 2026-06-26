# CALAMUS W17 — Working Copy Runtime Identity

## Status

Accepted and implemented as a low-risk runtime identity distinction for the source working copy.

## Problem

The machine can contain two Calamus runtimes at the same time:

- installed stable runtime: `/usr/bin/calamus`
- source working copy: `/home/luciano/Projects/calamus-work/bin/calamus`

During validation, this can create ambiguity. A visible runtime distinction is needed so the source working copy is not confused with the installed package.

## Decision

Use a display-only identity for the source working copy:

- window/top bar: `Calamus Copy`
- About visible identity: `Calamus-Working-Copy`

The formal package/application version remains:

- `APP_VERSION = "1.7.0-rc3-stable4.3"`

## Scope

W17 changes only source runtime display identity:

- `bin/calamus`
- `calamus/calamus_dialogs.py`
- `tests/test_runtime_identity_working_copy.py`
- this document

## Non-goals

W17 does not rename package, executable, app-id, desktop file, icon, or installed `/usr` runtime.

W17 does not add or alter editor features.

## Implementation rule

The working-copy title is driven by `APP_TITLE = "Calamus Copy"`.

The About dialog supports a display-only label while preserving the formal version fallback:

```python
def show_about(parent, version, display_name=None):
    about_header = display_name or f"Calamus {version}"
```

The source runner passes `show_about(self, VERSION, RUNTIME_ABOUT_NAME)` where `RUNTIME_ABOUT_NAME = "Calamus-Working-Copy"`.

## Validation

Required gates:

- static syntax check
- source provenance
- targeted runtime identity tests
- existing W15 command-layer regression tests
- full source selftest
- strict identity safety gates
- desktop validation:
  - source launch shows `Calamus Copy`
  - About shows `Calamus-Working-Copy`
  - installed `/usr/bin/calamus` remains normal `Calamus`
