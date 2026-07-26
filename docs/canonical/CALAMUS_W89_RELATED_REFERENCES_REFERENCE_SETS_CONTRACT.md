# Calamus W89 — Related References and Transparent Reference Sets

**Status:** CONTRACT RE-FROZEN AFTER MATURE GTK AUDIT AND VERIFIED ROLLBACK
**Date:** 2026-07-26
**Published baseline:** `569dd742abd607bb55a1e6bf9efbad1fdba1684c`
**Authorized product scope:** Option B
**Binding prerequisites:** GTK boundary policy and mature-source audit

## 1. Purpose

W89 adds:

1. explicit symmetric **Related References** stored in `references.md`;
2. transparent static ordered **Reference Sets** stored in `reference-sets.md`;
3. Related References navigation in the Authoring Bridge;
4. integrity and key-migration coverage for both authorities;
5. the GTK-boundary and normal-close lifecycle hardening required to test and
   certify these modal workflows safely.

## 2. Authorities

### Related References

`references.md` remains the only authority. Canonical field:

```text
Related Keys: ratzinger1968, newman1870
```

Rules:

- persisted values are primary canonical keys;
- aliases may resolve input but are never persisted as the new value;
- `A ↔ B` is symmetric;
- self-relations, duplicates, missing and ambiguous identities fail closed;
- one approved immutable plan updates both endpoints in one atomic write;
- nothing is inferred from tags, authors, citations, notes or similarity.

### Reference Sets

New transparent global authority:

```text
$XDG_DATA_HOME/calamus/research/reference-sets.md
```

Canonical format:

```markdown
# Calamus Reference Sets v1

## Core sources
Description: Primary sources for the article.

- ratzinger1968
- newman1870
```

A set owns only name, optional one-line description and ordered canonical keys.
Bibliographic metadata remains exclusively in `references.md`.

## 3. Visible UI

### References

A selected record exposes **Related References…** with filtering, semantic
identity, current symmetric closure, immutable impact preview, additions,
removals and affected-record count.

### Reference Sets

`Research → Reference Sets` opens a Research client with search, set selector,
description, ordered members, Add, Edit, Delete and Open Reference.

### Authoring Bridge

**Related References** is an on-demand mode. Activating an occurrence opens the
canonical target Reference.

## 4. Integrity and migration

Research Check diagnoses malformed, missing, ambiguous, alias, duplicate,
self-related and asymmetric Related Keys, plus malformed or invalid Reference
Set memberships.

Rename Reference Key updates four authorities after fresh-token impact preview:

1. `references.md`, aliases and Related Keys;
2. `reference-sets.md` memberships;
3. current Source Notes sidecar;
4. active-document citations through the Undo gateway.

Persistence uses atomic writes and compensating rollback. Any stale authority
cancels without blind overwrite.

## 5. GTK and lifecycle prerequisite

W89-G0 is part of this unitary contract because W89 adds and exercises modal GTK
workflows.

- Gtk 3.0, Gdk 3.0, Pango 1.0 and PangoCairo 1.0 are required explicitly;
- models, planners, stores, controllers and the modal adapter remain GTK-free;
- W89 nested loops use the single modal adapter;
- focused tests exclude true-App modal E2E;
- true-App workflows use semantic controls, bounded polling and cleanup;
- X, File → Quit and `Ctrl+Q` share one close gateway;
- accepted close destroys the window;
- final-window destruction exits `Gtk.main()`;
- a surviving process after normal close blocks certification.

## 6. Failure behaviour

- malformed authorities are read-only and reported;
- external changes trigger Reload / Overwrite / Cancel at the owning controller;
- missing or ambiguous identities never create records;
- opening a dialog never silently repairs symmetry;
- explicit approved edits may repair both halves;
- stale Authoring Bridge projections refuse navigation until Refresh;
- UTF-8 and atomicity are preserved;
- watchdog or SIGTERM cleanup is never treated as a successful normal close.

## 7. Explicit exclusions

- no database or JSON authority;
- no graph;
- no watcher;
- no background index;
- no dynamic, smart, saved-query, nested or hierarchical sets;
- no recommendations, similarity scoring or inferred relations;
- no persistent counts, cloud, account, sync, AI or network;
- no per-record set membership;
- no bibliography-manager implementation in W89;
- no change to deferred W88H-F1 editorial refinement.

## 8. Bloat boundaries

- `bin/calamus` remains composition plus canonical lifecycle and stays below 3,100 lines;
- each new runtime/controller/view/dialog stays below 450 lines;
- no new dependency;
- one new persistent Markdown format and one version header;
- no duplicate `references.md` parser.

## 9. Mandatory gates

- pure planning, parsing and canonicalization;
- self, duplicate, alias, missing, ambiguous and asymmetry cases;
- Reference Sets round-trip and malformed input;
- real filesystem stale-token and atomic-write tests;
- persist-first controllers and conflict decisions;
- four-authority migration with rollback;
- Research Check and Authoring Bridge navigation;
- modal adapter and GI namespace enforcement;
- canonical lifecycle unit and true-App subprocess proofs;
- focused and full regression;
- source provenance, exact dirty set, warning and bloat gates;
- isolated manual desktop validation and post-close no-process proof.

## 10. Publication gate

No commit or push before all automated gates, true-App GTK, manual validation,
exact verifier, clean process lifecycle and explicit user confirmation pass.

## Final re-freeze additions after desktop verifier mismatch

The following requirements are binding for the publishable W89 candidate:

1. Reference Set names are case-sensitive presentation data and must survive
   dialog → model → Markdown store → reload byte-for-byte. The exact test value
   `Core sources` must never become `Core Sources`.
2. The final verifier remains byte-exact and must not normalize case.
3. The desktop checklist must label the set name as case-sensitive and require
   an exact reopen check before continuing.
4. The canonical User Guide must contain a beginner References tutorial with
   concrete book/article/chapter records, Quick Cite, Related References,
   Reference Sets, four-authority key rename, import/export and recovery.
5. Help → About Calamus displays only `Calamus`.
6. System Info displays `Development build`, work item `W89`, and published
   baseline `569dd742abd607bb55a1e6bf9efbad1fdba1684c`; the historical package
   version remains packaging provenance, not active runtime identity.
7. All GTK boundary, namespace-version, modal-driver and normal-close lifecycle
   requirements from the mature-source audit remain blocking.

## Final mature dialog-identity re-freeze after repeated true-App failure

A failed identity E2E exposed both an undefined helper and a deeper dependency
on the accidental ordering of `Gtk.Window.list_toplevels()`.  The publishable
W89 candidate therefore adds these binding requirements:

1. Runtime product/build identity and System Info rendering are GTK-free data
   and functions.
2. About and System Info each have one typed builder result containing the exact
   owned dialog and semantic text widget.
3. Presentation is isolated in a GTK adapter and uses the canonical modal
   adapter for run/destroy ownership.
4. No identity test may use `visible_dialogs()[0]`, global top-level ordering or
   label scraping when a semantic text widget is available.
5. Component tests call the exact builders and inspect the returned widget
   bundle.
6. The true-App identity lane runs separately from the Related References /
   Reference Sets lane and resolves dialogs by exact title, semantic dialog name
   and semantic text-view name.
7. Changed identity paths must emit no `PyGTKDeprecationWarning`.
8. W89 does not convert every historical Calamus dialog; broad dialog cleanup
   remains part of the post-Research GTK-free architecture review.
