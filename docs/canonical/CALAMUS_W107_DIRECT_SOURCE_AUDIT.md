# W107 Direct Calamus Source Audit

## 1. W107 is the largest remaining ownership block

W100 froze 266 App methods. Ownership distribution:

- W101: 1 methods / 238 original method lines
- W102: 18 / 164
- W103: 51 / 598
- W105: 5 / 10
- W106: 53 / 580
- W107: 117 / 918
- W108: 21 / 271

W107 alone owns **117/266 = 44.0%**
of the original W100 App method inventory and **918/2779 =
33.0%** of its method lines.

This is why counting completed roadmap items overstates actual monolith removal.

## 2. Current W106 App shape

W100:
- `bin/calamus`: 3298 lines
- `App`: 3066 lines
- 266 frozen methods

W106:
- `bin/calamus`: 3100 lines
- `App`: 2898 lines
- 295 methods including later compatibility/delegation methods

Physical line reduction is only
**5.5%** for App.

That is not architectural failure: prior work items intentionally left
compatibility delegates in App. But it means W107/W108 must now convert the
architectural extraction into a genuinely thin shell.

## 3. W107 methods are already partly delegating

Of 117 original W107 methods:
- 116 remain;
- `build_clip_collection` has already moved out;
- 75 of the 116 current methods are <=4 lines;
- current W107-owned App surface totals 858 lines.

The remaining complexity is concentrated, not evenly distributed.

### Research + Clip family
52 current methods,
445 App lines,
42 delegates <=4 lines.

`build_research_panel` alone remains 246 lines and touches 44 distinct App
attributes/methods. It is the single strongest W107 extraction target.

### Workspace family
24 methods,
138 lines.

Workspace already has `WorkspaceCompositionInput`, controller, application
runtime, mutation controller/runtime and panel runtime. The remaining App layer
mostly supplies callbacks and reconciliation functions. W107 should replace
those callbacks with explicit narrow ports/components, not rewrite Workspace.

### Navigator family
7 methods,
22 lines.

Navigator composition is already narrow. Remaining App callbacks should become
command-shell delegates to Navigator/navigation ports.

### Search family
10 methods,
84 lines.

Search has a controller and dialogs, but App still owns find/replace orchestration
and transaction coupling. W107 should create a Search application runtime/port
that receives explicit document/editor transaction dependencies.

### Print family
4 methods,
35 lines.

Printing is GTK-facing and may remain in a GTK adapter, but it should consume a
narrow printable-document snapshot/title port instead of App methods/state.

### Spell/Language family
12 methods,
120 lines.

`on_check` remains 64 lines and coordinates Hunspell, ranges, dialog, editor
replacement, status/info and title. This needs a dedicated spellcheck
application runtime plus narrow text-edit/dialog ports.

### Help/dialog family
All 7 methods are <=4-line
delegates. They are already shell-like and should not receive new abstraction
machinery. W107 may route them through a narrow dialog/help adapter; W108 can
remove final facade noise.

## 4. W107 attributes

W100 assigned 41 App attributes to W107.

W106 still assigns 23:
authoring_bridge_runtime, bibtex_controller, bibtex_runtime, citation_controller, pandoc_export_controller, pandoc_export_runtime, reference_panel_runtime, reference_set_runtime, reference_set_store, reference_store, research_coordinator, research_export_controller, research_export_runtime, research_integrity_controller, research_integrity_runtime, research_panel_runtime, research_panel_view, scratchpad_runtime, source_note_panel_runtime, tag_integrity_controller, tag_integrity_runtime, tags_runtime, workspace_paned.

These are overwhelmingly Research subsystem runtimes/controllers/stores plus
`workspace_paned`.

W107 should group subsystem instances into typed component records rather than
projecting every internal object as an App attribute.

Compatibility aliases may remain only where the frozen W101 ledger or explicit
historical contracts require them.

## 5. Existing architecture to preserve

W107 must build on, not undo:

- W101 composition root and set-once local construction references;
- W102 DocumentSession authority;
- W103 EditorTransaction authority;
- W104 stable Command IDs/bindings;
- W105 UiStateSnapshot and GTK projector;
- W106 typed Preferences/ApplicationState and narrow persistence stores.

`calamus_application_components.py` already proves that typed immutable
composition-input records work. W107 should extend this technique to subsystem
host ports instead of creating an ApplicationContext/service locator.

## 6. No generic host

A single `AppHost` protocol exposing dozens of methods would merely rename the
monolith.

Required shape:
- ResearchHostPort
- WorkspaceDocumentPort / WorkspaceDialogPort / WorkspaceReconcilePort
- SearchDocumentPort / SearchDialogPort
- SpellcheckDocumentPort / SpellcheckDialogPort
- PrintDocumentPort
- HelpDialogPort

Ports may be dataclasses of explicit callables or Protocols. Each must be
minimal, stable and subsystem-scoped.

## 7. Product behavior is frozen

W107 is architectural:
- no Research feature expansion;
- no Workspace feature expansion;
- no search semantics change;
- no spellcheck semantics change;
- no print redesign;
- no new panel;
- no menu reorganization;
- no W108 thin-shell cleanup beyond what is required to establish ports.

The deferred `Ctrl+Alt+L` removal may be included only if explicitly accepted
as the small coordinated shortcut debt; it must not be confused with host-port
migration.

## Post-R2 FAIL 2/2 focused ownership re-audit

The R2 true-App failure was traced through `WorkspaceComponents`,
`WorkspaceHostRuntime`, `build_workspace_components()`,
`bind_workspace_startup()` and `compose_core_application_components()`.

Finding: the host runtime retained the first immutable Workspace owner record,
while startup binding created a second record via `dataclasses.replace()`.  This
was not merely a test-identity issue: W101 already forbids passing an ownership
bundle to a runtime.

Direct mature-source comparison reinforced the repair: GNOME Text Editor builds
pages with the concrete `EditorDocument` dependency; NotepadNext passes the
`RecentFilesListManager` directly to the recent-menu builder; gedit/Pluma keep
explicit concrete collaborators.  None of these useful patterns require a
runtime to retain the aggregate record that also owns that runtime.

Decision: ADOPT direct concrete collaborators plus the existing W101 set-once
cycle pattern; REJECT WorkspaceComponents back-reference and generic aggregate
reachability.
