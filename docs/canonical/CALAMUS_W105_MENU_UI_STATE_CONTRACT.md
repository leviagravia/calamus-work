# Calamus W105 — Menu and UI-State Decoupling Frozen Contract

Status: ACCEPTED / FROZEN / IMPLEMENTATION AUTHORIZED
Baseline: `92aa832c6b72cb7a81a5a44c656890ec602d9d41` (W104 CLOSED/CERTIFIED/PUBLISHED)


## Identity

Work item: W105
Name: Menu and UI-State Decoupling
Baseline: `92aa832c6b72cb7a81a5a44c656890ec602d9d41`
Nature: architecture-only, behavior-preserving
Visible feature additions: none
Persistence changes: none

## 1. GTK-free menu model

Create a GTK-free application menu model, for example:

- `MenuBarSpec`
- `MenuSpec`
- `MenuItemSpec(command_id, presentation_label, kind)`
- `MenuSeparatorSpec`
- `DynamicMenuSlotSpec(slot_id)`

It owns exact hierarchy/order/presentation of the application menubar and
references W104 stable command IDs.

It does not own execution, persistence, or subsystem logic.

Exact current top-level menu order is frozen:
File, Edit, Research, Navigate, Writing, Revise, View, Options, Tools, Help.

## 2. GTK-free UI-state values

Introduce immutable values such as:

`ActionUiState(enabled: bool = True, checked: bool | None = None,
               visible: bool = True)`

`UiStateSnapshot(states: mapping[command_id, ActionUiState])`

A pure projector/controller derives states from explicit facts. No GTK import.

## 3. Explicit state facts

W105 may temporarily read facts from current authorities while W106 is not yet
implemented. It must not become their owner.

Minimum checked-state facts:
- `research.panel` ← ResearchPanelRuntime.is_visible
- `navigate.navigator-panel` ← NavigatorPanelRuntime.is_visible
- `navigate.workspace-panel` ← WorkspacePanelRuntime.is_visible
- `writing.typewriter-mode` ← TypewriterRuntime.enabled
- `options.word-wrap` ← App.word_wrap (pre-W106)
- `options.transparent-mode` ← App.opacity_percent < 100 (pre-W106)
- `options.always-on-top` ← App.always_on_top (pre-W106)
- `options.appearance.light` ← App.appearance_mode == light (pre-W106)
- `options.appearance.dark` ← App.appearance_mode == dark (pre-W106)
- `options.line-numbers` ← App.line_numbers_enabled (pre-W106)

Minimum enabled-state fact currently required:
- Workspace root present → current five Workspace mutation command states.

All other command enabled states remain exactly as W104 behavior unless a
pre-existing rule is explicitly migrated. W105 must not add convenience
disablement for Undo, selection transforms, Save, etc. unless it already exists
as product behavior.

## 4. One projection adapter

A GTK-only adapter owns the menu widgets and maps them by stable command ID.

It is the only application-menu component allowed to call:
- `set_sensitive()`
- `set_active()`
- global menu `set_visible()` when applicable.

Projection is idempotent and guarded centrally so programmatic `set_active()`
does not re-dispatch commands.

The rest of Calamus does not store or mutate menu widgets.

## 5. Same state drives dispatch availability

For commands with a migrated `enabled` rule, the same `UiStateSnapshot` updates
W104 `CommandAvailability`.

Therefore:
logical enabled state == command-dispatch availability == GTK sensitivity.

No second availability predicate may be maintained in the GTK layer.

## 6. Check/toggle invocation

Menu click:
- GTK adapter reads the requested active value as input only;
- dispatches the W104 command with `active=<bool>`;
- authoritative runtime/preference state commits or rejects;
- projector re-renders from logical truth.

Shortcut:
- must not flip a Gtk.CheckMenuItem;
- obtains/toggles the logical authority through an explicit binding/request;
- projector updates the menu afterward.

On persistence failure the logical authority remains/reverts as today; the
projector restores the menu state. Per-feature widget rollback code disappears.

## 7. Panel runtimes

Remove `menu_item` dependencies from:
- ResearchPanelRuntime;
- NavigatorPanelRuntime;
- WorkspacePanelRuntime.

They own panel visibility and notify the application UI-state boundary. They do
not synchronize menu widgets.

## 8. Preference gateways

Remove direct menu-widget reach-through from:
- appearance gateway;
- opacity gateway;
- line-number gateway;
- Word Wrap flow;
- Always on Top flow.

W105 does not redesign how these values are saved. That remains unchanged until
W106.

## 9. Dynamic application menus

Convert Template, Recent Files, Favourites and Recent Workspaces menu contents
to immutable projection rows using existing W104 parameterized command IDs.

One GTK renderer owns child replacement, placeholder disabled rows and tooltip
application.

Data loading/storage stays in existing owners.

## 10. Local-view exclusion

The W105 global projector does not absorb:
- dialog-local button validation;
- list/filter sensitivity inside Research panels;
- Document Overview local buttons;
- BibTeX dialog state;
- Workspace context-menu capability logic;
- arbitrary widget visibility inside subsystem views.

Those remain local view/controller concerns unless a stable global command state
is involved.

## 11. Composition

Add a typed W105 component boundary, e.g.:
- `MenuModel`
- `UiStateController`
- `UiStateProjectorPort`
- `MenuGtkAdapter`

No W105 controller receives the whole `App`.
No generic service bag.

The composition root may temporarily collect explicit fact suppliers from
existing owners until W106/W107 extract them further.

## 12. Completion criteria

W105 is complete only when:
1. application menu structure is declared outside ambient `App`;
2. App does not own long-lived global menu item handles for state projection;
3. all 10 global check-state commands project from logical authorities;
4. shortcuts never toggle GTK widgets to determine state;
5. three panel runtimes no longer accept/store menu items;
6. GTK-free gateways no longer mutate menu widgets through `Any host`;
7. the five Workspace root-sensitive commands have one logical rule;
8. W104 CommandAvailability is updated from the same logical state where rules
   exist;
9. four dynamic menu families render from immutable menu projection rows;
10. no new product enable/disable semantics are introduced;
11. W106 preference ownership is not implemented;
12. W104/W103/W102/W101/W99/W98 gates and full regression pass;
13. desktop validation proves menu/shortcut parity and stale-state prevention.
