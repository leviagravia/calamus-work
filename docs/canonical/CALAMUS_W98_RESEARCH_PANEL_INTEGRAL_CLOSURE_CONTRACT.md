# Calamus W98 — Research Panel Integral Closure — frozen Core/Basic contract

Baseline: `f7fd70b4ffc7c756b83b8bfa102d224823244092` (`W97: add bibliography manager core`).

W98 closes the seven existing built-in Research clients as one coherent Core/Basic subsystem: Clips, Scratchpad, Bibliography, Tags, Reference Sets, Source Notes and Authoring Bridge. All Full variants remain frozen until the Calamus Core Completion Gate.

## Binding architecture

- one fixed GTK-free `ResearchPanelCoordinator` and one `ResearchClientSpec` per built-in client;
- typed reasons: `DOCUMENT_IDENTITY`, `DOCUMENT_CONTENT`, `REFERENCES`, `SOURCE_NOTES`, `SCRATCHPAD`, `REFERENCE_SETS`, `CLIPS`;
- active dependent projection refreshes exactly once; hidden dependent projections become dirty and refresh once on activation;
- document-content invalidation uses a Calamus-owned bounded 150 ms quiet period and generation cancellation;
- document identity changes cancel pending content work;
- New, Open, Save As, New from Template and Workspace identity reconciliation use one document-context gateway;
- successful mutations publish one exact invalidation set; failed and cancelled mutations publish none;
- Research shutdown runs before top-level destroy, cancels pending work, calls all seven shutdown hooks once and is idempotent;
- the existing single selector/stack remains the only activation owner;
- the executable Research command catalog contains the panel check item plus all 25 actions and uses the public name Bibliography.

## Exact product gates

Switching document A to B while Bibliography, Tags, Source Notes, Scratchpad or Authoring Bridge is visible must never retain A-derived state. Editing citations or headings while Bibliography or Authoring Bridge is visible refreshes once after the quiet period. Authority mutations update the active dependent projection and mark hidden dependants dirty. Activating all seven clients, creating pending Bibliography search and Tags selection work, and closing normally leaves no Research callback, window or process alive.

## Explicit exclusions

No Full feature, second panel, tabs, new authority, database, filesystem watcher, thread, graph, plugin system, generic event bus/service locator, `Gtk.Application` migration or general App decomposition beyond the Research seam.
