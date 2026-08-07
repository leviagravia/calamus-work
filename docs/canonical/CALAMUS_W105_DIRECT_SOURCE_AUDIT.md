# W105 Direct Calamus Source Audit

## Baseline

W104 is published at `92aa832c6b72cb7a81a5a44c656890ec602d9d41` and its finalizer certified **601 source
files**. W105 is the serial next work item.

The binding W100 roadmap assigns only **5 App methods** to
W105 (`build_menu`, `top`, `item`, `sep`, `add_shortcuts`) and zero App
attributes. That old inventory was intentionally coarse; W104 has already
migrated shortcut identity. W105 must now remove menu/UI-state coupling without
stealing W106/W107 ownership.

## 1. W104 solved command identity, not UI-state authority

W104 provides:
- one stable-ID CommandRegistry/catalog;
- explicit CommandBinding execution;
- separate CommandAvailability;
- catalog-derived shortcuts.

But `CommandAvailability` has **0 runtime
`set_enabled()` call sites outside tests**. Therefore dispatch availability is
logically separate in type only, not yet connected to real application state.

W105 is the work item that should connect logical availability to the same state
that GTK projects.

## 2. The menu is still an ambient App object graph

`calamus_ui.build_menu(app)` constructs **10 top-level menus**:
File, Edit, Research, Navigate, Writing, Revise, View, Options, Tools, Help.

It assigns **26 `app.*_item` / `app.*_menu` handles** and directly
initializes:
- **10 Gtk.CheckMenuItem controls**;
- **10 `set_active()` calls** in menu construction;
- **5 `set_sensitive()` calls** in menu construction.

The menu view therefore reads application fields while being built and leaves
long-lived widget handles on App for unrelated modules to mutate later.

## 3. Ten check-state commands have distributed synchronization

The ten stateful command IDs are:
- `research.panel`
- `navigate.navigator-panel`
- `navigate.workspace-panel`
- `writing.typewriter-mode`
- `options.word-wrap`
- `options.transparent-mode`
- `options.always-on-top`
- `options.appearance.light`
- `options.appearance.dark`
- `options.line-numbers`

Their true values come from panel/runtime or preference authorities, but menu
widgets are also read as input and repeatedly forced back into sync.

Across the repository there are 11 `_syncing_*` flag names, but several are
correctly local to list/filter widgets and are not W105 scope. The **global
menu-state synchronization** itself is still split across seven guard names/
patterns: `_syncing_appearance_items`, `_syncing_line_number_item`,
`_syncing_opacity_item`, `_syncing_typewriter_item`, `_syncing_word_wrap_item`,
the panel `_syncing_menu`, and WorkspacePanelRuntime's `_syncing`.

Those seven global guards are the W105 symptom: application menu-state
synchronization is implemented feature by feature rather than through one
projection boundary.

## 4. Shortcut toggle execution still depends on GTK widget state

`calamus_application_commands.build_application_command_layer()` uses a
`bind_toggle()` adapter. Menu invocation passes `active`, but shortcut
invocation falls back to `shortcut_toggle()`.

For Word Wrap, Transparent Mode, Always on Top and Line Numbers, the shortcut
toggle method calls `Gtk.CheckMenuItem.set_active(not get_active())`.
Thus a shortcut still treats the menu widget as the source from which the next
logical state is derived.

W105 must invert this dependency:
- current logical authority determines the requested next value;
- command executes;
- UI state is projected afterward.
A shortcut must work correctly even if no menu widget exists.

## 5. GTK-free gateways reach through host to GTK controls

The following modules import no GTK but mutate menu controls through `host`:
- `calamus_appearance_gateway.py`
- `calamus_opacity_gateway.py`
- `calamus_line_numbers_gateway.py`

They call `host.white_item.set_active`, `host.dark_item.set_active`,
`host.transparent_item.set_active`, or `host.line_item.set_active`.

This is an architectural GTK dependency hidden behind `Any`, not a real
GTK-free boundary.

W105 should remove widget synchronization from these gateways. On failure or
success they leave/commit authoritative logical state; the projector renders
that state.

## 6. Panel runtimes own menu-item objects

`ResearchPanelRuntime`, `NavigatorPanelRuntime`, and `WorkspacePanelRuntime`
accept/store `menu_item: Any` and call `get_active()/set_active()` themselves.

This couples domain/runtime panel visibility to one presentation widget and
creates three local recursion guards.

W105 should remove menu-item dependencies from those runtimes. Panel visibility
remains owned by the runtime/host; the W105 state projector observes or is
notified of the resulting boolean and updates the menu check state.

## 7. Workspace availability is duplicated

The five Workspace mutation items are made sensitive in two places:
1. during `build_menu()` from `bool(workspace_root)`;
2. in `App.on_workspace_root_changed()`.

Current behavior is coarse: all five share only the root-present predicate.
W105 should preserve this exact behavior, not silently refine it by selection or
file type. The single logical projection should drive both
`CommandAvailability` and GTK sensitivity.

Any richer selection/file-type availability is a later product/subsystem change,
not an architectural side effect.

## 8. Dynamic menus are presentation logic inside App

App directly rebuilds four dynamic menu families:
- Templates;
- Recent Files;
- Favourites;
- Recent Workspaces.

Each method creates/removes Gtk.MenuItem children and installs closures with
payloads. W104 already established parameterized stable command IDs.

W105 should represent these rows as immutable menu projection data
(`label`, command ID, payload, tooltip, enabled/placeholder) and let one GTK
adapter render them. Storage/loading remains where it is until W106/W107.

## 9. Scope exclusions are important

Not every `set_sensitive()` in the repository belongs to W105.

Dialog-local validation such as:
- enabling OK only when text is entered;
- enabling import/review buttons from a dialog session;
- per-panel filter availability;
- Document Overview local action buttons;

is local view behavior and should remain in the view/dialog module.

Likewise the Writing Workspace tree's context menu is subsystem-local and is
better left to W107/Thin GTK work unless W105 needs only to reuse W104 IDs.
W105 is primarily the application menu + global action-state projection boundary.

## Decision

### ADOPT
- immutable GTK-free `UiStateSnapshot` keyed by W104 command ID;
- one `ActionUiState(enabled, checked, visible)` value;
- a declarative GTK-free application `MenuModel`;
- one GTK projector that owns menu widgets and signal-suppression;
- W104 `CommandAvailability` driven from the same logical snapshot;
- dynamic menu rows as immutable projection data.

### ADAPT
- W104 command catalog as identity source;
- existing panel/preference/runtime booleans as temporary state facts;
- current exact menu order/labels/visibility;
- current five Workspace root-based sensitivity rules;
- current dynamic menu payload semantics.

### DEFER
- preference persistence and application-state ownership → W106;
- subsystem host-port migration and local context menus → W107;
- final GTK shell thinning → W108.

### REJECT
- widget state as source of logical truth;
- per-feature `_syncing_*` flags as the architecture;
- GTK-free modules that mutate widgets through `Any host`;
- a second command catalog;
- event bus/service locator/global mutable UI dictionary;
- silently adding new enable/disable rules in an architecture-only work item.
