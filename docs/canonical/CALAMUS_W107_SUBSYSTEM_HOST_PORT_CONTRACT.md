# CALAMUS W107 — Subsystem Host-Port Migration Contract

Status: **FROZEN / IMPLEMENTATION AUTHORIZED**  
Baseline: `e8befafaf7f75d958eabbd2e273f83c630042b84`  
Accepted by Luciano: 2026-08-07  
W108 Thin GTK Shell: **OUT OF SCOPE**

## 1. Core invariant

After W107 no subsystem controller/runtime may receive or retain the whole `App`
object, directly or indirectly. A GTK presentation adapter may retain the parent
window only where GTK parentage/modal presentation requires it.

Forbidden architectural substitutes:
- `AppHost`;
- `ApplicationContext` / `AppServices`;
- service locator/service registry;
- generic dependency dictionary;
- global event bus;
- plugin framework or dynamic dependency lookup.

Ports are explicit, typed, immutable and subsystem-scoped.

## 2. Authorities preserved

W107 does not redefine existing authorities:
- W102 `DocumentSession`: document path/text/dirty/session identity;
- W103 `EditorTransaction`: programmatic editor mutation/undo/rollback;
- W104 command catalog/stable command IDs: user-intent authority;
- W105 `UiStateSnapshot`: logical check/sensitivity authority;
- W106 typed Preferences/ApplicationState + persistent collections: persistence authority.

No raw `settings` dictionary and no `App.state`/StateManager authority may return.

## 3. Research

Move the W106 `build_research_panel` composition hotspot to
`calamus_research_composition.py`.

`ResearchSubsystemComponents` is the typed subsystem bundle. Application-facing
research orchestration is owned by GTK-free `ResearchApplicationRuntime` using
`ResearchApplicationPorts`.

The runtime receives narrow capabilities for:
- document text and selection/cursor offsets;
- W103 command execution;
- document-range navigation/focus;
- clipboard copy;
- quick-cite choice/error presentation;
- W105 UI-state refresh.

The runtime must not retain `Gtk.TextView` or `App`.
Historical public compatibility aliases may remain only where existing lifecycle,
command or historical true-App contracts require them.

## 4. Workspace

Preserve Workspace controller/application/mutation owners.

`WorkspaceHostRuntime` is GTK-free and receives only:
- canonical recent/favourite/workspace stores;
- W106 application-state controller;
- W102 document session;
- `WorkspaceHostPorts` for presentation/document/research/UI projection.

GTK dialog/menu parenting belongs to `WorkspaceHostGtkAdapter` only.
The Workspace runtime must not retain the application/window.

## 5. Search

`SearchApplicationRuntime` owns application-level Find/Replace orchestration.
It receives SearchController, W103 transaction authority, buffer adapter and
narrow presentation/projection ports.

Replace Current and Replace All remain transactionally owned by W103. Search
semantics, current-query/repeat behavior and selection behavior remain unchanged.

## 6. Spellcheck / Language

`SpellcheckApplicationRuntime` is GTK-free. It receives W103 transaction,
buffer adapter and narrow language/dialog/range/projection ports.

It must not retain `Gtk.TextView`, the misspelling tag widget or `App`.
Hunspell command and suggestion semantics remain unchanged.

## 7. Print

GTK PrintOperation/PangoCairo pagination belongs to `PrintRuntime`, a GTK adapter
boundary. It receives only parent window, printable document text provider,
font provider and error presentation.

No document mutation is permitted.

## 8. Application shell ownership

App may keep compatibility forwarding methods, but W107-owned methods must be
bounded delegates with no domain mutation logic. New W107 subsystem authority is
stored in private typed bundles (`_w107_subsystems`, `_research_components`) rather
than proliferating public runtime aliases.

Final deletion/collapse of harmless compatibility delegates belongs to W108.

## 9. GTK boundary

GTK-free:
- `calamus_search_runtime.py`
- `calamus_spellcheck_runtime.py`
- `calamus_workspace_host_runtime.py`
- `calamus_research_application.py`

GTK adapters/composition may import GTK only where presentation requires it:
- `calamus_workspace_host_gtk.py`
- `calamus_clipboard_gtk.py`
- `calamus_print_runtime.py`
- `calamus_research_composition.py` may wire GTK-facing existing views but the
  runtime ports it constructs are narrow.

## 10. Lifecycle

Existing W99 lifecycle authority remains binding. Subsystem components with
shutdown/timer/process ownership must still be registered through the existing
lifecycle composition. No duplicate shutdown owner.

## 11. Authorized Linux Mint shortcut repair

Luciano explicitly authorized this repair as part of W107:
- remove `Ctrl+Alt+L` from the authoritative default accelerator for Line Numbers;
- therefore it must disappear from GTK shortcut binding, menu shortcut display,
  Help/Keyboard Shortcuts and tests;
- the Line Numbers command/menu item remains;
- **no replacement shortcut is introduced**.

This repair is logically isolated from host-port migration.

## 12. Out of scope

- W108 Thin GTK Shell;
- broad source cleanup/deprecation cleanup;
- Research/Workspace/Search/Spellcheck feature expansion;
- Full Scratchpad/Document Overview/Bibliography/Markdown Preview;
- tabs, plugins, service locator, database, cloud, AI, WebKit/JS;
- replacement shortcut for Line Numbers.

## 13. Completion gates

W107 closes only if:
1. no W107 core runtime/controller receives whole `App`;
2. no generic host/context/service locator/event bus exists;
3. Research composition is outside App and bundle-owned;
4. Workspace host runtime is GTK-free and parent-window-free;
5. Search orchestration is outside App and W103-owned for mutation;
6. Spellcheck orchestration is outside App and widget-free;
7. Print orchestration is outside App except GTK adapter boundary;
8. compatibility delegates contain no W107 domain logic;
9. W104/W105/W106 authorities remain intact;
10. `Ctrl+Alt+L` is absent from authoritative projections with no replacement;
11. W107 focused and W106→W98 historical headless gates pass zero-skip;
12. headless-core and full discovery pass;
13. source provenance/GTK boundary/compile/Bash/capability lanes pass;
14. exact baseline+patch reconstruction passes;
15. true-App/true-GTK W107 identity and product lanes pass;
16. historical W106/W105/W104/W103/W102/W101/W99/W98 true-App lanes pass;
17. real `~/.config/calamus` remains unchanged;
18. desktop validation passes with synchronous authority receipts.

## Amendment 01 — Core-composition construction-order barrier (R2)

Candidate R1 exposed a real true-GTK construction-order defect: the GTK menu
builder projected the dynamic Recent Workspaces family before
`compose_core_application_components()` had constructed and bound the W107
`WorkspaceHostRuntime`.

The frozen repair is:

- `calamus_ui.build_menu()` may construct/register the dynamic
  `recent-workspaces` slot but MUST NOT invoke the Workspace host runtime;
- the initial Recent Workspaces projection occurs immediately after
  `compose_core_application_components()` returns and `_components` is assigned;
- every subsequent refresh continues through
  `WorkspaceHostRuntime.populate_recent_workspaces_menu()`;
- no fallback path, partially initialized host, whole-App dependency, or
  duplicate Workspace menu authority is permitted.

This is a lifecycle/order repair only. Workspace semantics and persistence are
unchanged.

## Amendment 02 — Workspace ownership-bundle prohibition after R2 FAIL 2/2

Candidate R2 exposed a deeper ownership defect in the W107 Workspace host.
`WorkspaceHostRuntime` retained the pre-startup `WorkspaceComponents` ownership
record through `bind_components()`.  `bind_workspace_startup()` then used
`dataclasses.replace()` to create the final immutable record stored in
`CoreApplicationComponents`.  The concrete collaborators were identical, but
the aggregate record identity diverged.

This design also violated the older W101 invariant that a top-level ownership
bundle is never passed to a controller/runtime.  The post-FAIL2 repair is
therefore architectural, not an assertion workaround:

- `WorkspaceHostRuntime` MUST NOT receive, retain or expose `WorkspaceComponents`;
- `bind_components()` / `components` authority is removed;
- the runtime receives only the concrete collaborators it actually invokes:
  Workspace application runtime, mutation controller/runtime, panel view/runtime;
- the bounded callback cycle is constructed with the W101 named
  `SetOnceReference("workspace-host-runtime")` inside the Workspace builder;
- `WorkspaceComponents` remains the immutable composition-owner record stored by
  `CoreApplicationComponents`, but is never a runtime dependency;
- startup binding may continue to replace the immutable owner record because no
  subsystem runtime retains that record;
- the true-App gate verifies direct collaborator identity and explicitly rejects
  a `components` / `_components` back-reference on WorkspaceHostRuntime.

No Workspace feature, persistence rule, command identity, GTK presentation, or
W108 shell cleanup is changed by this amendment.
