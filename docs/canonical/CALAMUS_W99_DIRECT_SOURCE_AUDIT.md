# Calamus W99 — Direct Source Audit

Date: 2026-08-02
Audited source: verified W98 candidate snapshot corresponding to published commit
`fb54cd3bb96bbea024966db2a059c755aef45d95`
Method: direct reading of the bundled Calamus source; no web substitution.

## 1. Initial lifecycle topology

### `bin/calamus`

The W98 launcher contained multiple independent ownership paths:

- `request_application_close()` directly stopped Pandoc and Research before
  destroying the window;
- `on_destroy()` separately stopped Research, Document Overview, Typewriter,
  History and Viewport;
- wrap reflow and word-count sources were scheduled in the App;
- search highlighting owned another pending source in `SearchController`;
- the owner list was implicit and could drift when a new runtime was added.

This made ordering non-auditable, allowed one failing callback to interrupt
later cleanup and gave no immutable final report.

**Decision:** replace the duplicated lists with one injected, named lifecycle
coordinator and thin application-boundary registration.

## 2. Complete asynchronous-source inventory

Direct scanning found fourteen scheduling calls across eight source files:

- `bin/calamus`: three;
- `calamus_history_runtime.py`: one;
- `calamus_navigator_panel_view.py`: two;
- `calamus_pandoc_runtime.py`: one;
- `calamus_reference_panel.py`: one;
- `calamus_research_panel_view.py`: one;
- `calamus_tags_panel.py`: one;
- `calamus_viewport_runtime.py`: four.

Existing cancellation was generally local, but App wrap/search ownership,
Navigator shutdown and Research-selector reset disposal were incomplete or not
part of one final owner inventory.

**Decision:** freeze the exact scheduling-file/count inventory in a test and
require an explicit cancellation marker and lifecycle owner for every site.
Any future scheduling call changes the inventory and fails the gate.

## 3. Search cancellation race

### `calamus_search_gateway.py::SearchController`

W98 stored a pending highlight source but exposed no lifecycle cancellation
method. Removing a GLib source alone was also insufficient protection against a
callback already selected for dispatch.

**Decision:** add `cancel_pending_highlight(cancel)`, clear ownership, increment
a generation token and make the callback reject obsolete generations.

## 4. Research shutdown

### `calamus_research_coordination.py::ResearchPanelCoordinator.shutdown`

The W98 loop could stop at the first exception and did not preserve exact child
failure evidence.

**Decision:** attempt all seven fixed clients, record `(client_id, detail)` for
`False` returns and exceptions, mark every client attempted once and keep the
operation idempotent.

### `calamus_research_panel_view.py::ResearchClientSelector`

The selector scheduled a reset-to-top idle callback without persistent disposal
ownership.

**Decision:** track `_reset_source`, cancel it before replacement and cancel it
in idempotent `dispose()`; the Research view exposes `shutdown()`.

## 5. Navigator lifecycle

### `calamus_navigator_panel_view.py`

The view already tracked `_refresh_source` and `_cursor_source` and had a local
`cancel_pending()` operation.

### `calamus_navigator_panel.py::NavigatorPanelRuntime`

The runtime lacked a final lifecycle method.

**Decision:** keep scheduling in the GTK view and add a thin runtime
`shutdown()` that invokes the existing cancellation boundary.

## 6. Workspace boundary leak

### `calamus_workspace_mutation.py`

`WorkspaceMutationController` imported `calamus_workspace_gio` and constructed
`WorkspaceGioAdapter` by default. Therefore a controller role depended on a
concrete GIO boundary and importing the controller could import toolkit-facing
code.

**Decision:** require adapter injection, validate only the method needed by the
selected operation, construct `WorkspaceGioAdapter()` in `bin/calamus`, and move
`WorkspaceOperationResult` to `calamus_workspace_results.py`.

## 7. Opacity boundary leak

### `calamus_opacity.py` and `calamus_opacity_gateway.py`

The preference model module also contained the concrete GTK widget adapter, and
the gateway imported that adapter directly.

**Decision:** retain percent validation and preference planning in
`calamus_opacity.py`; move widget application to `calamus_opacity_view.py`; have
the gateway call the App host protocol `apply_opacity_percent()`.

## 8. Global GTK-free audit

The previous `scripts/prove-gtk-boundary.sh` encoded a small historical module
list and token-presence checks. It could not detect a new controller importing a
view or GIO adapter.

**Decision:** W99 dynamically scans every current module matching the frozen
pure-role suffixes. The scan rejects GI imports, toolkit names and concrete
boundary imports.

## 9. Files deliberately not redesigned

Direct inspection found no W99 justification for broad rewrites of:

- Bibliography model/controller/view separation and coalesced search dispatcher;
- Document Overview snapshot/controller/runtime boundaries;
- Typewriter/Viewport geometry policy;
- Pandoc process/session ownership;
- Tags deferred-action semantics.

These systems gain lifecycle registration or inventory coverage only.

## 10. Result

The W99 change is a unitary ownership repair: one lifecycle authority, one exact
owner inventory, complete final attempts, explicit cancellation of every App
source, and enforceable toolkit boundaries. It contains no product expansion.
