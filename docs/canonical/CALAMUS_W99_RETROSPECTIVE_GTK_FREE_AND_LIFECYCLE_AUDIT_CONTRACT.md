# Calamus W99 — Retrospective GTK-free and Lifecycle Audit

Status: **Candidate R1 — headless certified; real GTK validation pending**
Published baseline authority: `fb54cd3bb96bbea024966db2a059c755aef45d95` (`W98: close research panel core`)
Runtime identity: `W99` / `Retrospective GTK-free and Lifecycle Audit`

## 1. Purpose

W99 is an architectural closure, not a product feature. It audits the W98 source
as a whole and corrects only defects in toolkit boundaries, asynchronous-source
ownership, close routing and deterministic shutdown. No editor command, Research
client, persistence format, menu item, file format or user-facing workflow is
added.

## 2. Frozen non-goals

W99 does **not**:

- migrate Calamus to `Gtk.Application`;
- introduce a plugin registry, generic event bus, worker supervisor or service container;
- add a database, watcher, cache authority, background index or cloud component;
- revive any deferred Full feature;
- redesign panels, menus, dialogs or the editor;
- change the published package version;
- perform commit or push.

## 3. Binding architecture

### 3.1 One application lifecycle authority

`calamus_application_lifecycle.ApplicationLifecycleCoordinator` is GTK-free and
owns two ordered phases:

1. **pre-destroy** — callbacks may block interactive close by returning exactly
   `False` or raising; a failed callback is retriable;
2. **final** — every remaining owner is attempted exactly once; failures are
   aggregated and never prevent later owners from receiving shutdown.

Successful pre-destroy callbacks are not repeated during final shutdown. Final
shutdown is idempotent and exposes an immutable report.

The fixed owner inventory is:

- pre-destroy: `pandoc-export`;
- final: `application-sources`, `navigator-panel`, `research-panel-view`,
  `research-coordinator`, `document-overview`, `typewriter`, `history`,
  `viewport`.

Registration is named, ordered and duplicate names are forbidden.

### 3.2 One close gateway

Every interactive close path delegates to `App.request_application_close()`:

1. reject re-entrant close duplication;
2. execute the existing save/discard/cancel decision once;
3. run lifecycle preflight;
4. keep Calamus open and report the exact blocking owner on failure;
5. save settings and destroy only after successful preflight.

`App.on_destroy()` owns final lifecycle shutdown and terminates the raw
`Gtk.main()` loop only when one is active. It contains no direct subsystem
shutdown list.

### 3.3 Every GLib source has an explicit owner

The W99 gate inventories every direct `idle_add`/`timeout_add` site and freezes
its cancellation owner:

| Scheduling site | Owned source | Cancellation owner |
|---|---|---|
| `bin/calamus` | wrap reflow, word count, search highlight | `application-sources` |
| `calamus_history_runtime.py` | delayed snapshot | `SnapshotHistoryRuntime.shutdown()` |
| `calamus_navigator_panel_view.py` | refresh and cursor sync | `NavigatorPanelRuntime.shutdown()` → `cancel_pending()` |
| `calamus_pandoc_runtime.py` | worker poll | modal session registration + Pandoc pre-destroy shutdown |
| `calamus_reference_panel.py` | coalesced bibliography search | dispatcher `dispose()` |
| `calamus_research_panel_view.py` | selector reset | view `shutdown()` → selector `dispose()` |
| `calamus_tags_panel.py` | deferred selection | existing deferred-action cancellation |
| `calamus_viewport_runtime.py` | projection and layout guard | viewport `shutdown()` |

Search highlight cancellation increments a generation token so a callback that
races with removal is still stale and cannot mutate the view.

### 3.4 GTK-free role rule

Modules whose names end in `_controller`, `_gateway`, `_store`, `_model`,
`_planning`, `_operations`, `_coordination`, `_lifecycle` or `_results` must not:

- import `gi` or any `gi.repository` namespace;
- reference `Gtk`, `Gdk`, `GLib` or `Gio` names;
- import concrete Calamus `_view`, `_dialogs`, `_panel`, `_gio` or `_gtk`
  boundaries.

The gate scans the complete current module set; it is not a historical allowlist.

### 3.5 Boundary repairs

- `WorkspaceMutationController` receives its filesystem adapter from the
  launcher composition root. It no longer imports or constructs
  `WorkspaceGioAdapter`.
- `WorkspaceOperationResult` lives in the GTK-free
  `calamus_workspace_results.py` module; the GIO adapter imports the result,
  never the reverse.
- opacity preference semantics remain in GTK-free `calamus_opacity.py`;
  concrete widget opacity application lives in `calamus_opacity_view.py`;
  the gateway calls an injected host protocol.
- `ResearchPanelCoordinator.shutdown()` is fail-complete across all seven fixed
  clients and records exact child failures while remaining idempotent.
- `ResearchClientSelector.dispose()` owns its deferred reset source.
- `NavigatorPanelRuntime.shutdown()` owns pending Navigator view work.

## 4. Preserved authorities

W99 does not rewrite already-correct subsystem boundaries. Bibliography keeps
its W97 GTK-free search/model/controller plus view-owned coalesced dispatcher.
Document Overview, Typewriter, History, Viewport and Pandoc keep their existing
runtime implementations and are only registered with the central lifecycle.

## 5. Required gates

A W99 candidate may reach desktop validation only after all of these pass:

1. exact source and executable-mode verification;
2. Python compile gate without leaving bytecode in the source tree;
3. release-profile inventory with every discovered test assigned;
4. W99 headless-focused profile, zero skips;
5. complete unittest discovery; only environment-gated GTK/Pandoc/GIO lanes may skip;
6. exact global GLib-source inventory and cancellation-owner proof;
7. exact GTK-free role scan;
8. current W99 identity true-App lane;
9. true-App normal-close lifecycle lane with pending App sources;
10. no residual Calamus process after the GTK lane.

The two true-App lanes are ordered: identity first, lifecycle second. A skip,
watchdog termination, missing marker or unavailable display is not a PASS.

## 6. Certification boundary

Headless success authorizes only a desktop candidate bundle. W99 remains
**DESKTOP VALIDATION PENDING** until the GTK lanes run on the real T480 desktop.
Publication remains forbidden until Luciano explicitly reports PASS and then
runs the separately prepared fail-closed publication procedure himself.
