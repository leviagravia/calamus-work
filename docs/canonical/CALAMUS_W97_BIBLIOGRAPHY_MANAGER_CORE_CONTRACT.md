# Calamus W97 — Bibliography Manager Core Search/Model Rebuild contract

Status: FROZEN FOR SEARCH/MODEL REBUILD CANDIDATE R1
Published baseline: `199459fb023e4862407f7eb60318192f276d3239`

## Attempt accounting

The earlier W97 Core Candidate R1 and Candidate R2 are quarantined. Their exact product logs prove the same false-negative test oracle: the test asserted immediately after `Gtk.SearchEntry.set_text()` while the selected `search-changed` signal had not yet delivered the query. They are INVALID RUNS, not valid product failures. This Search/Model Rebuild starts a new line at Candidate R1, valid attempt 1/2. It is not Candidate R3 and it does not reuse either retired desktop runner unchanged.

## Identity

- Work item: `W97`
- Description: `Bibliography Manager Core`
- Visible client: `Bibliography`
- Existing internal Research client ID: `references`

## Authority

`references.md` remains the sole canonical bibliography authority. W97 creates no database, JSON/YAML index, cache, background watcher, second library or second application. Search, filters, sorting, detail, counts and integrity are disposable projections.

## Architecture

```text
references.md
  → MarkdownReferenceStore
  → immutable ReferenceRecord values
  → GTK-free BibliographyProjection
  → existing ReferenceController
      owns selected citation key
  → ReferencePanelRuntime
  → GTK Bibliography list/detail client
```

App is composition only. Mutations remain persist-first and stale-token guarded by `ReferenceController` and `MarkdownReferenceStore`.

## Search contract: explicit delayed/coalesced delivery

Calamus deliberately uses delayed/coalesced search because complete-field projection and GTK list/detail rendering should not run once for every intermediate keystroke.

1. `Gtk.SearchEntry.changed` reports every text mutation immediately.
2. `CoalescedQueryDispatcher` owns a 150 ms quiet-period timer.
3. A newer generation cancels the older timer.
4. Only the latest query is delivered to `ReferenceController`.
5. The dispatcher is GTK-free and tested with an injected scheduler.
6. Destroying the panel cancels pending delivery.
7. Programmatic selection by citation key clears/cancels pending search before resetting filters.
8. True-App tests use a bounded wait for the delivered query and visible projection; a single `pump()` is forbidden as a completion oracle.
9. `search-delivered` may be logged only after query delivery and expected visible keys are proven.

## Selection contract

The canonical selected citation key belongs to `ReferenceController`, not to `Gtk.ListBoxRow`. User row selection is translated into that key; refresh/filter/render derive the row selection from controller state. Destruction or replacement of a row cannot erase semantic selection before the controller decides whether the key is still visible.

## Core functional contract

1. One Research client labelled Bibliography; no duplicate References/Bibliography clients.
2. Compact list plus read-only detail for the selected record.
3. Complete free-text search across every canonical field, aliases, local path, annotation and additional fields.
4. Combinable Type, Tag, Use, File and Integrity filters.
5. Stable sorting by author/year, title, year, key or type; missing values last.
6. New and Edit reuse the canonical Reference dialog and preserve unknown fields.
7. Duplicate proposes a collision-free key, clears aliases and requires explicit review before save.
8. Safe Delete previews current document citations, current Source Notes, Related References and Reference Sets; it never silently rewrites those authorities.
9. Quick Cite, Copy Key, Show Uses, Related References and Refresh operate on the current canonical selection.
10. one local-file path may be selected, opened or revealed; Calamus stores only the path.
11. Open Bibliography File delegates `references.md` to the OS; subsequent mutations retain stale-token protection.
12. Markdown and plain-text export write the current visible projection atomically as derived files.
13. Existing W87 BibTeX/BibLaTeX and W90 Pandoc/citeproc workflows remain the sole owners of their formats.
14. Malformed `references.md` remains read-only; no repair is automatic.
15. Current identity is exact W97 over published W96 baseline; historical functional gates remain independent.

## Integrity projection

- error: exact duplicate DOI/ISBN/ISSN identity;
- warning: missing author/date, or configured local file missing;
- advisory: unused in current context, no tags, or no DOI/ISBN/ISSN/URL;
- clean: no derived issue.

These classifications never mutate a record.

## Explicit exclusions

Core excludes web metadata retrieval, AI, cloud/sync, PDF indexing or preview, file copying, multiple attachments, relative-path migration, background indexing, batch editing, automatic duplicate merge, field-by-field merge and arbitrary filesystem-wide use scans.

## Full phase frozen backlog

Bibliography Manager Full may add advanced Current Document projections, advanced filters, editable additional fields, duplicate centre, explicit field-by-field merge with multi-authority impact preview and rollback, multiple attachments/relative-path policy, and additional filtered/selected W90 export scopes. None is authorized by the Core contract.

## Hostile gates

- rapid text sequence delivers exactly one final query after quiet period;
- cancelled/stale generations never mutate the projection;
- panel destruction cancels pending work;
- true-App bounded wait proves actual query delivery and exact visible keys;
- controller-owned selected key survives row replacement and refresh;
- full-field and additional-field search;
- combined filters and deterministic sort;
- missing/present/unset local paths;
- aliases in citations and known uses;
- duplicate identifiers;
- duplicate draft never copies aliases;
- safe delete does not mutate other authorities;
- external `references.md` edit conflicts fail closed;
- simple export does not alter canonical authorities;
- same client identity through repeated activation;
- one selection-handler owner and non-reentrant render transaction;
- repeated true-App search/filter/refresh stress;
- runner prints exact profile status and complete dedicated log before propagating FAIL;
- true App/true GTK list, detail, selection, search, filters, file actions, refresh and normal-close lifecycle;
- zero-skip explicit release profiles.
