# Calamus W100 — Direct source monolith audit

Baseline: `9a80b266cbdb41b499efdb296ff2a312cf85656f`
Scope: `bin/calamus`, `calamus/calamus_ui.py`, application-boundary helpers,
release profiles and all direct whole-App parameters.

## Measured baseline

- launcher: **3298 lines**;
- `App`: **3066 lines**;
- methods defined in `App`: **266**;
- distinct Calamus imports: **92**;
- assigned `self.*` attributes: **94**;
- attributes assigned by `__init__`: **66**;
- `calamus_ui.py`: **401 lines**;
- distinct `app.*` attributes in `calamus_ui.py`: **156**;
- total `app.*` references in `calamus_ui.py`: **281**;
- functions in Calamus modules accepting an `app` parameter: **35**.

## Complete classification

Every currently defined App method is assigned exactly once in
`CALAMUS_W100_APP_METHOD_RESPONSIBILITY_INVENTORY.json`. Every assigned App
attribute is assigned exactly once in
`CALAMUS_W100_APP_ATTRIBUTE_RESPONSIBILITY_INVENTORY.json`. Whole-App parameters
are frozen in `CALAMUS_W100_WHOLE_APP_COUPLING_INVENTORY.json`.

## Root finding

The defect is not merely file length. The concrete GTK window is simultaneously:

- the object-graph constructor;
- document session authority;
- editor transaction coordinator;
- command callback namespace;
- preference/state owner;
- Workspace/Research/Search/Navigator host;
- menu service locator;
- cross-cutting dialog and lifecycle boundary.

Physical helper modules that still receive `app` are transitional seams, not a
completed decomposition.
