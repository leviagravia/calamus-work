# Calamus W101 — Isolation-Contract Rebuild

**Baseline:** `fb003223643d9da5f81ddaa3f3e0e4a9304f3903`  
**Candidate line:** Isolation-Contract Rebuild Candidate R1  
**Product identity:** W101 — Core Composition Boundary and Dependency Enforcement

## Status and negative evidence

The earlier W101 Candidate R1 and Candidate R2 are retired after two desktop
failures. Candidate R1 exposed a provenance-process GTK namespace ordering bug.
Candidate R2 repaired that gate, then exposed a test-fixture/config-resolver
mismatch before manual validation. Neither candidate is a publication source.
This rebuild is reconstructed from the exact W100 published baseline.

## Root cause

Calamus production state resolves its configuration through
`$HOME/.config/calamus`. W101 does not migrate persistence to
`XDG_CONFIG_HOME`. Candidate R2 wrote its true-App fixture and manual runner
state below an XDG-only path while leaving the actual Calamus resolver pointed
elsewhere. The observed Workspace root `None` was therefore produced before
composition and was not evidence of a Workspace builder regression.

## Binding isolation contract

1. `HOME` is replaced before importing or constructing Calamus.
2. The test fixture is written to `$HOME/.config/calamus/settings.json`.
3. `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, and `XDG_CACHE_HOME` are coherent child
   paths of the same isolated HOME.
4. The true-App gate asserts the exact `StateManager.config_dir` and settings
   file before asserting Workspace startup binding.
5. The user's real `$HOME/.config/calamus` is snapshotted read-only before and
   after the automated and manual lanes; any difference is a hard failure.
6. No production persistence resolver or migration is changed in W101.
7. Search, Navigator, Workspace, Clip Collection, Research presence, Document
   Overview presence, lifecycle shutdown, and no residual process remain
   mandatory true-App/true-GTK evidence.

## Direct mature-source decisions

- **Kate — ADAPT:** set test mode and temporary configuration before app
  construction.
- **gedit / Pluma / Geany — ADAPT:** derive configuration through one explicit
  resolver and point tests at the resolver actually used by the application.
- **REJECT:** framework-specific migrations or changing Calamus persistence
  semantics within W101.

## Release barrier

The rebuild is not certifiable until package verification, Git read-only audit,
source provenance, GTK boundary, W101/W100/W99/W98 zero-skip profiles, isolated
true-App gates, real-config integrity checks, manual validation, normal close,
and residual-process checks all pass.
