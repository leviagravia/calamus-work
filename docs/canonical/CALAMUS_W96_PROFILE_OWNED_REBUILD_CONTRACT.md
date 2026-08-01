# Calamus W96 — Profile-Owned Rebuild Contract

**Lineage:** Profile-Owned Rebuild Candidate R1
**Published baseline:** `792ca0f76db39525a9052bd61e43fe929988af2e`
**Product scope:** Document Overview Core — Gate C
**Repository rule:** canonical repository remains read-only until complete desktop PASS.

## 1. Independent-line identity

This line is not Architecture Rebuilt R4 and is not a narrow amendment of the
retired R3 policy. Architecture Rebuilt R1/R2/R3 remain retired. The source is
reconstructed as one unit from the published baseline.

The Document Overview product boundary is retained because none of the prior
FAILs demonstrated a product defect:

```text
immutable Document Dossier snapshot
→ GTK-free controller/runtime/presentation model
→ App integration boundary
→ GTK view adapter
```

No database, watcher, AI, background index or new authority is introduced.

## 2. Canonical release-test owner

`scripts/calamus-release-profiles.py` and
`tests/calamus_release_test_profiles.json` jointly own:

- exact selected test identities;
- capability prerequisites;
- environment variables and variables that must be absent;
- concrete script executables for historical fixture-heavy gates;
- working directory and import topology;
- zero-skip result validation;
- complete discovered-test assignment.

`unittest discover` is permitted only for inventory. It is not an
undifferentiated release gate.

Every automated release profile requires **zero skips**. Missing capability is
a precondition FAIL before test execution.

## 3. Required profiles

- `headless-core` — deterministic tests, display explicitly removed;
- `w96-headless-focused` — exact W96 Gate C headless surface, zero skips;
- `filesystem-capabilities` — exact symlink/FIFO tests;
- `pandoc-real` — real Pandoc tests after executable probe;
- `gio-real` — exact GIO tests after GIO, symlink and case-rename probes;
- `gtk-components` — selected real-display component tests;
- `workspace-e2e-real` — eleven true-App workspace tests, each with a fresh fixture;
- `w86-w87-real-fixtures` — real Tag Integrity and BibTeX fixture workflows;
- `historical-w89-w94` — registered historical GTK executable;
- `historical-w95extra` — registered W95extra executable;
- `w96-identity-smoke` — current identity first;
- `w96-product-smoke` — current product first;
- `manual-desktop` — the seventeen-point final checklist.

Every discovered test identity must belong to at least one profile. Unknown or
unassigned tests fail package construction.

## 4. Anti-recurrence ledger

### W96 original R1 — historical identity collision

- Classification: historical/current identity contract defect.
- Barrier: historical W95 gate does not import current `DEVELOPMENT_WORK_ITEM`,
  description or baseline.
- Executable proof: `tests.test_w96_identity_gate_contract`.
- Failure phase: package/headless contract, before historical GTK.

### W96-TEST-TOPOLOGY-01

- Cause: package-style test invocation combined with top-level helper import.
- Barrier: `tests` is an explicit package; helper imports are package-qualified;
  canonical `PYTHONPATH` is only `calamus:repository-root`.
- Additional correction in this line: Pandoc helper imports use
  `tests.calamus_pandoc_artifact_assertions`.
- Executable proof: profile inventory rejects `_FailedTest`, unknown and zero tests.

### CALAMUS-CANDIDATE-PREFLIGHT-01

- Cause: final package structure was checked without executing the exact desktop
  entrypoint path.
- Barrier: final ZIP is extracted to a new directory and its own runner executes
  inventory, `headless-core`, fixture generation and source verification.

### Embedded fixture SyntaxError

- Cause: Python embedded inside Bash was invisible to Python compilation.
- Barrier: fixture creation is a real Python module and a real executable entrypoint;
  no embedded Python is allowed in the desktop wrapper.

### CALAMUS-RUNNER-EVIDENCE-01

- Cause: validator-owned log captured stdout but not unittest stderr.
- Barrier: profile runner validates `unittest.TestResult` directly; script profiles
  capture merged stdout/stderr from a concrete process.

### CALAMUS-TEST-SKIP-PROFILE-01

- Cause: environment-dependent aggregate skip count was treated as portable.
- Barrier: no global skip count is accepted; every selected profile requires
  `result.skipped == []`.

### CALAMUS-TEST-PROFILE-OWNERSHIP-01

- Cause: broad discovery mixed deterministic, GTK, GIO, Pandoc and fixture tests.
- Barrier: exact profile-owned identities and capabilities precede execution.
  Inventory runs in a disposable interpreter; the selected profile runs in a
  distinct interpreter/process state so discovery cannot cache class decorators,
  GTK availability or lane flags before the profile environment is installed.

### CALAMUS-PROFILE-IMPORT-STATE-01

- Cause: the first provisional profile runner performed broad inventory discovery
  and selected-profile execution in one Python process. Imported test modules could
  cache class decorators, GTK availability and lane flags before the profile-owned
  environment was installed.
- Barrier: inventory executes in a disposable child interpreter; the selected
  profile imports its exact test identities only after capability probes and
  environment installation in the parent profile process.
- Executable proof: `test_inventory_and_profile_imports_use_distinct_processes`.
- Failure phase: headless architecture contract, before package construction.

### CALAMUS-DISCOVERY-MIXED-CAPABILITIES-01

- Cause: the so-called headless run inherited the real desktop display.
- Barrier: `headless-core` explicitly removes `DISPLAY`, `WAYLAND_DISPLAY`,
  `MIR_SOCKET` and `GDK_BACKEND` and excludes capability-bound tests.

### CALAMUS-SKIP-AS-ORACLE-01

- Cause: skip output was normalized into release PASS by count or reason.
- Barrier: zero skips in every automated gate; a skip is a profile failure.

### CALAMUS-SIMULATED-ENVIRONMENT-EVIDENCE-01

- Cause: a modified JSON report was used to simulate T480 execution.
- Barrier: evidence is accepted only from actual profile execution. JSON editing,
  record deletion and synthetic desktop reports are forbidden.

## 5. Order of release validation

1. bundle/source integrity and canonical read-only preflight;
2. profile inventory;
3. compile and Bash syntax;
4. extracted-package `headless-core` with zero skips;
5. executable W96 fixture preflight;
6. desktop capability profiles;
7. W96 identity and product smoke profiles before long historical lanes;
8. workspace and W86/W87 fixture profiles;
9. historical W89-W94 and W95extra profiles;
10. W96 identity/product complete rerun;
11. manual checklist;
12. authority-byte and no-residual-process postflight;
13. only after PASS: apply to canonical repository, retest, commit, push and publish.

## 6. Failure accounting

This independent line allows at most two desktop FAILs. A second FAIL retires the
line. No third incremental candidate is allowed.


## Profile-Owned R1 desktop crash barrier

`CALAMUS-DOCUMENT-OVERVIEW-CATEGORY-ROW-LIFECYCLE-01` records the R1 manual
crash: selecting Research synchronously rebuilt the category `Gtk.ListBox`,
removed the native pointer-event row, emitted invalid-widget GTK criticals and
ended with exit 139. Category navigation rows are now persistent for the view
lifetime; refresh updates labels and selection only. Item rows remain snapshot
projections and may be rebuilt because their list is not the source of the
category pointer event. The headless adapter lifecycle tests and the true-App
product profile both assert stable category-row identity across every category.
