# W105 Test and Gate Plan

## GTK-free menu-model tests

- exact top-level order;
- exact current static item order and separator positions;
- every command item references an existing W104 command ID;
- check items are exactly the ten current stateful command IDs;
- no duplicate menu-node identity;
- dynamic slots exist exactly for Templates, Recent Files, Favourites,
  Recent Workspaces.

## GTK-free state tests

For every global check command:
- authoritative fact -> exact checked state;
- state changes are immutable snapshots;
- unrelated state remains unchanged.

Workspace:
- no root -> five current mutation commands disabled;
- root present -> all five enabled;
- do not add selection/file-type refinement.

Availability:
- migrated logical enabled state and CommandAvailability are identical.

## Toggle source-of-truth tests

- shortcut toggle works with no GTK menu widget constructed;
- menu request and shortcut request reach the same logical transition;
- failed persistence restores projected checked state from authority;
- projector `set_active()` does not recursively dispatch a command;
- no feature-specific `_syncing_*` flag needed for global menu projection.

## Static gates

- GTK-free UI-state/menu-model modules import no gi/Gtk/Gdk/Pango;
- Research/Navigator/Workspace runtime constructors contain no menu-item
  parameter;
- appearance/opacity/line-number GTK-free gateways contain no `*_item` widget
  reach-through;
- `CommandAvailability.set_enabled()` has a real runtime producer from W105;
- global application menu `set_active/set_sensitive` calls are confined to the
  GTK projector/adapter;
- no whole-App W105 controller dependency;
- no W106 persistence extraction;
- no W107 subsystem migration.

## Dynamic menu tests

For each dynamic family:
- empty state produces exact disabled placeholder;
- populated state produces exact labels/tooltips/payloads;
- activation uses existing stable parameterized W104 command ID;
- repeated refresh removes old rows exactly once;
- storage ordering and limits unchanged.

## Historical regression

Preserve:
- W104 command/action true-App;
- W103 editor-transaction true-App;
- W102 document-session true-App;
- W101 composition true-App;
- W99 lifecycle true-App;
- W98 Research true-App;
- full release inventory.

## Desktop validation

Runner opens an isolated fixture automatically.

Manual checks should be limited to:
1. exact W105 System Info identity;
2. Research panel menu check follows shortcut open/close;
3. Navigator menu check follows shortcut open/close;
4. Workspace panel check follows menu/shortcut and root-state sensitivity is
   coherent;
5. Typewriter check follows Shift+F9;
6. Word Wrap check follows Alt+Z;
7. opacity/transparent, appearance and line-number checks do not become stale
   after changing via alternate command paths;
8. Recent/Favourites/Workspace dynamic menu refresh does not duplicate rows;
9. Quit normally; no residual process; real config unchanged.

Instructions must use exact paths and explicit expected visual states.
