# Calamus W101 — Core Composition Boundary and Dependency Enforcement

Published baseline: `fb003223643d9da5f81ddaa3f3e0e4a9304f3903`  
Candidate: `W101 Core Composition Boundary and Dependency Enforcement — Candidate R1`  
Publication subject: `W101: extract core composition boundary`

## Purpose

W101 extracts construction ownership for editor infrastructure and Search,
Navigator, Writing Workspace, the shared panel hosts, and Clip Collection from
`App`. It establishes executable import-direction, ownership, callback-cycle,
and ambient-authority barriers without changing product behavior or persistence.

## Authority and scope

The existing local UTF-8 document, Research stores, settings, history semantics,
command gateway, and GTK widgets remain authoritative. W101 changes only where
the non-Research object graph is constructed and owned.

The exact W101 builders are:

- `calamus_editor_composition.py`;
- `calamus_navigator_composition.py`;
- `calamus_workspace_composition.py`;
- `calamus_clip_composition.py`;
- stateless orchestration in `calamus_application_composition.py`;
- frozen ownership records and narrow inputs in
  `calamus_application_components.py`.

## Binding API

The only new whole-App entry is:

```python
compose_core_application_components(app, *, clip_invalidation_reason)
```

No local builder accepts `App`. Cross-builder dependencies are explicit inputs.
The top-level bundle is an ownership record and is never passed to a controller,
runtime, view, store, or model.

## Ownership bundles

- `EditorInfrastructureComponents` owns history, viewport/history/typewriter
  runtimes, Search, three editor tags, and the exact GTK signal-connection
  inventory.
- `NavigatorComponents` owns the navigation controller, left-panel host,
  Navigator view/client/runtime.
- `WorkspaceComponents` owns the Workspace controller, view, application and
  mutation runtimes/controllers, client host, runtime, and startup visibility
  result.
- `ClipCollectionComponents` owns Clip view/controller/runtime.
- `CoreApplicationComponents` owns the four local bundles, right-panel host,
  exact build order, and composition-complete marker.

## Dependency and ambient-authority rules

- root imports only components/input records and builder modules;
- no builder imports another builder;
- no product/domain/store/controller imports composition;
- no mutable module global, singleton, default lookup, service locator,
  application context, generic event bus, plugin infrastructure, dynamic
  dependency lookup, string-key service map, or generic alias projection;
- local callback cycles use only named set-once references;
- `App` stores exactly one `_components` bundle;
- the 24 legacy aliases are explicit and frozen in the W111 ledger.

## Resource ownership

- 12 editor GTK signal connections are built together and owned by the editor
  bundle; GTK widget destruction is their lifetime authority;
- viewport, history, typewriter, Search highlight, Navigator pending work and
  Research client shutdown retain their existing cancellation/lifecycle owners;
- W99 lifecycle registration remains byte-for-byte semantically unchanged;
- Workspace and panel-view connections remain widget-lifetime bound;
- startup-root binding occurs only after all W101 core owners and aliases exist.

## Exclusions

W101 does not move or redesign Research composition, Document Overview,
application lifecycle registration, document/file session, editor transactions,
commands/actions, menu/UI state, preferences/application state, broad host-port
migration, persistence, help, or visible features. Those remain assigned to
W102–W108.

## Frozen structural budgets

- launcher direct Calamus imports: exactly 74 and never above 74;
- App methods: exactly 265 and never above 265;
- App lines: exactly 2923 and strictly below W100's 3066;
- launcher lines: exactly 3137 and strictly below W100's 3298;
- whole-App functions: W100's 35 plus exactly one authorized W101 root entry;
- ambient-authority count in new modules: zero;
- local builder App inputs: zero;
- cross-builder imports: zero;
- unowned W101 resources: zero;
- changed-path ceiling: 30 source-tree paths.

## Required gates

The W101 focused profile must prove source identity, exact moved constructors,
exact bundle fields, exact aliases, AST import direction, no ambient authority,
set-once cycles, signal/resource ownership, startup topology, compatibility,
W100 historical contract continuity, W99 lifecycle continuity, W98 Research
continuity, true-App/true-GTK core wiring, normal close, and no residual process.

No desktop PASS authorizes Git mutation. Stage, commit, push, and remote
verification remain Luciano's actions on the T480.
