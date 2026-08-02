# Calamus W97 — direct source audit for Bibliography Manager Core

Date: 2026-08-02
Baseline audited: `199459fb023e4862407f7eb60318192f276d3239`

## Existing authority and data model

`calamus/calamus_references.py` already defines immutable `ReferenceRecord` values with key, aliases, type, authors, editors, title, date, publication fields, identifiers, URL, language, tags, annotation, one local-file path and preserved unknown fields. `suggest_reference_key()` already owns deterministic key proposals. The existing `ReferenceRecord.search_text` is insufficient for W97 because it omits some publication, file and additional fields; W97 therefore adds a complete projection without changing the record authority.

`calamus/calamus_reference_store.py` already defines `MarkdownReferenceStore`, parser/serializer diagnostics, collision checks, `FileToken` stale detection and atomic UTF-8 replacement. The store is retained unchanged as the only persistence boundary. Its preservation guarantee is semantic canonicalization, not arbitrary byte-for-byte retention of comments or layout.

## Existing mutation controller

`calamus/calamus_reference_controller.py` already owns load, add, update, delete, replace, conflict Reload/Overwrite/Cancel and persist-first state update. Generic edit already refuses citation-key and alias mutation. W97 extends this same controller with immutable `BibliographyFilters`, `BibliographyContext`, full-field projection, detail refresh and selection preservation. No second controller writes `references.md`.

## Existing UI/runtime boundary

Before W97, `calamus/calamus_reference_panel.py` presented a search field, flat list and CRUD/Quick Cite/Copy Key/Related buttons. It had no detail, filters, sort, file actions, duplicate action, Show Uses or current-context integrity. W97 replaces only this view projection with a compact list/read-only detail and explicit filters/actions.

`calamus/calamus_reference_runtime.py` remains the coordinator outside App. It receives providers for the current document, Source Notes and Reference Sets; derives context; owns duplicate/safe-delete/file/export dialogs; and delegates persistence to the controller. `bin/calamus` remains composition and visible command routing.

## Existing integrations reused

- `calamus/calamus_citations.py` and `calamus/calamus_citation_controller.py`: citation parsing/resolution and Quick Cite.
- `calamus/calamus_related_references.py` and related dialogs: explicit symmetric relationships.
- `calamus/calamus_reference_sets.py` and set runtime/store: named ordered sets.
- `calamus/calamus_reference_integrity.py`: key/alias resolution, identifier duplicates and controlled multi-authority rename.
- `calamus/calamus_bibtex*.py`: W87 import/export, collision decisions and probable duplicate logic.
- `calamus/calamus_pandoc*.py`: W90 formatted bibliography and citeproc products.
- `calamus/calamus_workspace_external.py`: OS open/reveal boundary.
- `calamus/calamus_research_file.py`: atomic derived export.

## Implemented W97 boundary

New GTK-free `calamus/calamus_bibliography.py` owns only:

- complete search text;
- available filter values;
- combined search/filter/sort projection;
- current-document/Source-Note/Reference-Set context;
- derived integrity severities;
- duplicate draft construction;
- known-authority delete impact;
- read-only detail text;
- simple Markdown/plain bibliography renderers.

It imports no GTK and persists nothing.

## Direct source decisions

ADOPT:

- existing Markdown authority, immutable records, atomic stale-aware store and persist-first controller;
- existing Research Panel client identity `references`;
- W87/W90 integration rather than replacement;
- current authority providers already exposed by App.

ADAPT:

- visual client label changes from References to Bibliography;
- old flat list becomes compact list/detail;
- old query-only controller refresh becomes combined immutable filters/context;
- old destructive confirmation becomes known-use impact preview;
- existing one `file_path` gains chooser/open/reveal and state filtering;
- current visible projection becomes the scope of simple Markdown/text export.

REJECT:

- new store/controller, second manager, database/index, background watcher, direct GTK scans of domain objects, App-owned CRUD, web/AI retrieval, PDF indexing and silent cascades.

DEFER:

- duplicate centre, field merge, multiple attachments, relative paths, batch editing, advanced query language and extra W90 scopes.

## Risks and barriers

1. Selection/filter drift: controller always reselects a visible canonical key or the first visible item.
2. Empty/missing sort values: deterministic keys place missing values last.
3. alias use: context and delete impact resolve every identity to one canonical key.
4. external edit: mutations remain stale-token guarded.
5. false safety claim: Delete describes only current document, current Source Notes, Related References and Reference Sets; no global filesystem scan is claimed.
6. file ownership: open/reveal expands `~` but never copies or indexes the file.
7. identity collision: W97 current identity has a separate true-App gate; historical W95/W96 functional gates remain unchanged.
8. export authority: simple exports use atomic write to a user-selected destination and never target internal persistence implicitly.

## Result

The published W96 source supports W97 Core without architectural reset. Bibliography Manager is correctly implemented as a richer projection and action surface over the already mature References subsystem. The high-risk duplicate/merge programme remains outside Core.


## Candidate R1 desktop failure follow-up

R1 reached the true-App W97 product profile after all preceding profiles passed, then exited before manual validation without a product traceback. Direct re-audit identified that `ReferencePanelViewAdapter.render()` removed the selected `Gtk.ListBoxRow` while `row-selected` remained connected to controller detail refresh. That allowed callbacks to observe a destroyed or partial row tree.

R2 corrects the whole lifecycle contract rather than only changing one assertion: selection callbacks are blocked for the complete row-replacement transaction; rendering is non-reentrant; the stable selected key is restored before callbacks resume; hostile fake-GTK tests reproduce removal-time selection emission; and the true-App gate repeatedly exercises search, filters and refresh. The release harness is also unbuffered and faulthandler-enabled so native failure evidence cannot disappear again.

Canonical failure classes:

- `CALAMUS-BIBLIOGRAPHY-LISTBOX-ROW-LIFECYCLE-01`
- `CALAMUS-PROFILE-NATIVE-CRASH-EVIDENCE-02`
