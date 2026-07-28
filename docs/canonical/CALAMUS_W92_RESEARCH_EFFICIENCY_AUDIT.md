# Calamus W92 — Research Efficiency Audit and Contract

## Status and baseline

- Work item: **W92 — Research efficiency pass**.
- Published baseline: **W91**, commit `42b3c052e23ba3da0072984f40b2afd4f569c1d2`.
- Method: read-only audit of the published Calamus source followed by a narrow implementation against measured duplication and user-visible friction.
- Commit and push: outside this candidate; publication requires a separate authorization after desktop validation.

W92 is not a speculative rewrite. Its purpose is to reduce complexity that became observable after the addition of Scratchpad Basic and to complete the canonical Help coverage requested after W91.

## Measured findings in Calamus W91

### F1 — A Research client could be activated twice

Relevant W91 source:

- `calamus/calamus_research_panel.py`, `ResearchPanelRuntime.show()`;
- `calamus/calamus_research_panel_view.py`, `ResearchPanelViewAdapter.show_client()`;
- `calamus/calamus_research_panel_view.py`, `ResearchPanelViewAdapter.focus_active()`;
- `calamus/calamus_research_panel_view.py`, selector and stack signal callbacks.

The runtime called `show_client(target)`, which already invoked the client activation callback, and then called `focus_active()`, invoking it a second time. A selector change could likewise activate through both the selector callback and the stack `notify::visible-child-name` callback.

For Scratchpad, activation includes document binding, sidecar loading, projection refresh and focus transfer. The duplicated activation did not corrupt data, but it repeated work and enlarged the GTK signal surface.

**Decision: ADOPT one activation owner.** The view updates selector and stack under one guard, then invokes the activation callback exactly once. The runtime no longer performs a second focus/activation pass.

### F2 — Managed sidecar identity was repeated in multiple modules

In the W91 baseline the two suffix literals appeared **14 times** in production source:

- `.source-notes.md`;
- `.scratchpad.md`.

They were repeated across the two stores and the Workspace scan, planning, mutation and GIO layers. This was a real maintenance risk: a future document-owned sidecar could be recognized by one operation but omitted by another.

**Decision: ADOPT one GTK-free registry.** `calamus_managed_sidecars.py` owns names, labels, suffixes, path construction and filename recognition. Production source now contains the suffix literals only in this registry.

The transaction plans remain typed and explicit. W92 does not replace the existing Source Notes and Scratchpad fields with generic dictionaries, because that would trade a small amount of repetition for weaker contracts and a larger migration.

### F3 — Scratchpad external refresh existed in the controller but lacked a direct control

Scratchpad already used a file token and fail-closed stale handling, but ordinary daily use had no visible `Refresh` action. Reload was mainly reached through conflict handling or reopening the client.

**Decision: ADOPT explicit refresh.** The Scratchpad client receives a compact `Refresh` button and `F5` while the list has focus. Refresh forces a new document binding/read and never merges or silently overwrites external changes.

### F4 — High-frequency Scratchpad actions had no shortcuts

W91 exposed Scratchpad and Capture Selection only through menus. Continuous use makes these high-frequency actions.

**Decision: ADAPT keyboard-first access.** W92 adds:

- `Ctrl+Alt+S` — open Scratchpad;
- `Ctrl+Alt+Shift+S` — Capture Selection in Scratchpad;
- `Insert` — new entry while the Scratchpad list is focused;
- `Delete` — delete selected entry, still with confirmation;
- `F5` — Refresh.

The canonical shortcut registry remains conflict-free.

### F5 — Help contained a standalone Scratchpad topic but the Research tutorial still described the pre-W91 system

The W91 guide included a separate `Scratchpad Basic` topic. However, the learning tutorial and the canonical Research guide still taught the Research apparatus primarily as document, References, Source Notes and Reference Sets. Backup, workflow, object distinctions and the end-to-end example did not consistently include the Scratchpad sidecar.

**Decision: ADOPT one integrated explanation.** W92 updates both the English learning tutorial and the canonical Italian Research guide. It distinguishes Source Notes from Scratchpad Entry, documents both sidecars, adds the Basic workflow and shortcuts, covers Refresh and Workspace behavior, and preserves the separate detailed Scratchpad topic.

## Direct mature-source audit

The following decisions derive from the uploaded source code, not from websites or README-only comparison.

### Zim desktop wiki — ADAPT

Files and functions inspected:

- `zim/gui/widgets.py`, `WindowSidePaneMixin.set_pane_state()`;
- `zim/gui/widgets.py`, pane-state restore and active-tab handling.

Observed sequence: make the pane visible with `show_all()`, restore the active tab, then transfer focus. This directly supports Calamus’s order: show Research host, select the requested client, activate/focus once.

Adopted principle: **visibility → active client → focus**.

Rejected: notebook-wide indexing, plugin infrastructure and generalized wiki backlinks.

### Text Pieces — ADAPT

Files and functions inspected:

- `src/widgets/action_search.rs`, `set_search_entry()`;
- `src/widgets/action_search.rs`, `disconnect_entry()`;
- `src/widgets/action_search.rs`, search-change callback and keyboard forwarding.

The source disconnects old signal ownership before rebinding, updates filter/sorter and selection before switching stack pages, and deliberately returns focus after keyboard navigation.

Adopted principle: guard signal synchronization and update model/selection before changing presentation.

Rejected: transformation-plugin surface and unrelated text-tool architecture.

### Boop-GTK — ADAPT

Files and functions inspected:

- `src/ui/command_palette.rs`, command model setup;
- `src/ui/command_palette.rs`, first-row selection after filtering;
- `src/ui/app.rs`, editor focus restoration.

The palette keeps a compact searchable list, deterministic selection and keyboard-first activation.

Adopted principle: compact controls and predictable keyboard behavior for frequent Scratchpad actions.

Rejected: arbitrary script execution and a global scratch buffer.

### QOwnNotes — ADAPT / REJECT

Files and functions inspected:

- `src/managers/noteindexmanager.cpp`, external modification handling;
- external-change paths for Reload, Overwrite and no-op/Cancel.

The source makes external state visible and distinguishes reload from overwrite. This supports a visible Refresh action and explicit stale conflict choices.

Adopted principle: external changes are explicit user decisions.

Rejected: permanent watcher/index infrastructure, global note folders, cloud, scripting and database-backed note management.

### LinNote — ADAPT

Files/classes inspected directly in the uploaded source:

- `ui/SearchModal.cpp`, `SearchModal::showAndFocus()`;
- `ui/MainWindow.cpp`, `MainWindow::showAndFocus()`;
- note storage and dirty-state classes.

The sequence `show() → raise() → setFocus()` independently confirms that focus follows visibility and selection.

Rejected: SQLite, OCR, timers, encryption and utility-suite expansion.

## Explicit non-goals

W92 does **not**:

- remove a Research feature because it appears complex;
- redesign the Research Panel;
- introduce lazy client construction without measured startup evidence;
- add a Tags client or tag database;
- add Scratchpad Full links to References or Source Notes;
- add watchers, background indexing, AI, cloud or a knowledge graph;
- alter the W91 Scratchpad Markdown format;
- change the published document or sidecar authorities.

The proposed Tags client remains audit-gated for a later work item. Scratchpad Full remains W93.

## W92 implementation contract

### Production changes

1. `ResearchPanelRuntime.show()` shows the host and selects the client once.
2. `ResearchPanelViewAdapter` owns selector/stack synchronization under one guard and activates exactly once per semantic selection.
3. `calamus_managed_sidecars.py` is the sole production authority for managed document-sidecar descriptors.
4. Source Notes, Scratchpad and Workspace use the shared registry without changing their public behavior.
5. Scratchpad has a visible Refresh control and list-local Insert/Delete/F5 keys.
6. Global Scratchpad and Capture Selection shortcuts are registered, visible and conflict-free.
7. User Guide integrates Scratchpad into the Research tutorial, authority map, workflow, backup, troubleshooting, glossary and checklist.
8. Runtime identity reports W92 against published W91 baseline `42b3c052e23ba3da0072984f40b2afd4f569c1d2`.

### Safety invariants

- Models, stores and controllers remain GTK-free.
- No sidecar format migration.
- No implicit overwrite after external modification.
- Workspace Rename, Duplicate and Move to Trash continue to carry both managed sidecars transactionally.
- User document text is unchanged by opening, refreshing or filtering Scratchpad.
- Historical W90/W91 GTK/GIO lanes remain passing.

## Required gates

- source provenance;
- `git diff --check`;
- Python compilation;
- W92 focused unit tests;
- full headless regression with GTK workflows isolated;
- real GTK Research activation lane without duplicate callback;
- real Scratchpad Refresh and shortcut lane;
- historical W90 and W91 GTK/GIO lanes without skips;
- manual desktop validation of Help, shortcuts, Refresh, panel switching and normal shutdown.

## Final architectural decision

W92 removes measured duplication while preserving the visible Research architecture. The central rule is:

> One semantic action has one activation owner; one document-sidecar identity has one canonical registry; one user-facing feature has one coherent Help narrative.

## Candidate R3 — complete command guide and default Help Navigator

Desktop validation of Candidate R1 confirmed the W92 runtime and GTK/GIO changes, but user review rejected the Help surface as incomplete. Candidate R2 expanded the Scratchpad learning path; subsequent review identified two remaining structural defects:

1. the guide did not enumerate the complete current menu and every static submenu;
2. the guide navigator exposed only level-two chapters, so the user could not see topics and subtopics immediately.

R3 corrects both defects from the actual source and the canonical roadmap rather than by adding an isolated prose appendix.

### Current menu authority

The current command map was audited directly against `calamus/calamus_ui.py`. It records the visible W92 order and all static submenus, including the transitional `Options` menu. Dynamic rows such as recent files, templates, workspaces and favourites are identified as dynamic data rather than fabricated menu items.

### Final target authority

The future map is based on Operational Memory Entry 061, then reconciled with later certified decisions: Writing Workspace, Clip Collection, Reference Sets, Authoring Bridge, BibTeX/BibLaTeX, Pandoc/citeproc, Scratchpad Basic, the post-W96 freeze of Scratchpad Full, and the final Tags client. Current and future commands are never conflated: every future item is labelled Available, Planned, Frozen or Retired.

### Help Navigator boundary

`calamus_help.py` now owns a GTK-free `HelpTopic` hierarchy derived from real Markdown H2-H4 headings outside fenced examples. `calamus_help_dialogs.py` renders that hierarchy through a dedicated GTK `TreeStore`/`TreeView`. The Guide Navigator:

- is visible whenever User Guide opens;
- selects the current W92 command map by default;
- expands chapter roots to expose their direct subtopics;
- never reuses or mutates the document Navigator, current manuscript, caret or left-panel state;
- preserves the legacy flat H2 section API for existing command wiring and regression tests.

### R3 verification contract

R3 adds pure tests for current-menu completeness, final-target preservation, hierarchy and fenced-example exclusion; it also adds a real GTK lane proving default visibility, selection, expansion and navigation to current and final menu topics. Historical User Guide and BibTeX navigation GTK tests are rerun because the dialog implementation changed.
