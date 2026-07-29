# Calamus W94 Tags — direct source audit and frozen contract

## Baseline and status

W94 starts only from the published W92 commit
`1e8cd2c584eb3f28c814f0dee433aaf7ae580f51`. W93 Scratchpad Full remains
frozen until after W96. W94 implements the Tags client already required by
canonical Entry 061; it does not absorb W93 relationships, Concepts, Themes or
Research Check expansion.

## Current Calamus source audit

The implementation was derived from the actual W92 source, especially:

- `calamus_tag_integrity.py`: pure logical identity, deterministic variants,
  exact uses and immutable mutation plans;
- `calamus_tag_integrity_controller.py`: preview token, stale detection,
  atomic store writes and compensation across authorities;
- `calamus_reference_store.py`, `calamus_source_note_store.py` and
  `calamus_scratchpad_store.py`: the three canonical Markdown stores and their
  `FileToken` compare-before-write contracts;
- `calamus_reference_panel.py`, `calamus_source_note_panel.py` and
  `calamus_scratchpad_panel.py`: compact GTK list idioms;
- `calamus_research_panel_view.py` and `calamus_research_panel.py`: one shared
  right-panel host, semantic client selection and single activation;
- `bin/calamus`: the real App wiring and cross-client navigation methods;
- `share/doc/calamus/USER_GUIDE.md`: command map and mandatory learning path.

Measured architectural conclusion: Calamus already had a safe two-authority
Tag Integrity transaction and all three Markdown stores. W94 should extend that
transaction to Scratchpad and expose a persistent derived client, not introduce
another tag authority.

## Direct mature-source audit

### Tags (Vala/GTK)

Read:

- `src/tag/tag-row.vala`, class `TagRow`, including the visible `hitcounter`;
- `src/tag/tags-view.vala`, class `TagsView`, including previous/next-hit
  controls and compact list ownership;
- `src/tag/tag-store.vala`, class `TagStore`, including `hitcounter_reset_all`,
  `add_tag`, `remove_tag`, `to_file` and `from_file`.

ADOPT: compact rows, explicit hit counts and exact previous/next occurrence.
ADAPT: Calamus shows exact Research uses grouped by authority and opens the
owning item. REJECT: the separate JSON tag store and colour/style persistence,
because Calamus tags remain embedded in Markdown authorities.

### Zettlr

Read `test/replace-tags.spec.ts` and the tested `replaceTags` contract. It
protects Markdown links and replaces only parser-recognised tags, including
case and multi-word cases.

ADOPT: exact identity replacement, explicit impact and tests for misleading
text contexts. ADAPT: Calamus replaces structured `Tags:` fields, not document
text, and therefore plans record mutations before writing. REJECT: scanning and
rewriting an entire workspace file-by-file without one multi-authority
transaction.

### QOwnNotes

Read `src/managers/tagmanager.cpp`, especially `reloadTagTree`,
`buildTagTreeForParentItem`, `addTagToTagTreeWidget`,
`on_tagLineEdit_textChanged`, `jumpToTag`, selection handlers and bulk
rename/remove paths.

ADOPT: direct search filtering, visible use counts, keyboard/mouse selection
and opening the selected use. ADAPT: a flat list with per-authority counts
R/N/S. REJECT: SQLite ownership, parent tags, hierarchy, notebook-wide global
state and semantic colour authority.

### Zim 0.76.3

Read `zim/notebook/index/tags.py`, especially `TagsView.list_all_tags_by_n_pages`,
`list_intersecting_tags`, `list_tags`, `list_pages` and the tag tree models.

ADOPT: deterministic counts and a tag-to-owning-items view. ADAPT: transient
projection over the current three Calamus authorities. REJECT: SQLite index,
notebook-wide background indexing and tag cloud/tree semantics.

### Gnote

Read `src/tagmanager.cpp`, especially `get_tag`, `get_or_create_tag`,
`remove_tag` and `all_tags`. Gnote separates normalized identity from display
and removes a tag explicitly from every owning note.

ADOPT: normalized lookup identity with preserved display spelling and explicit
remove-everywhere semantics. ADAPT: immutable plans over Markdown records.
REJECT: central Tag objects, internal/system tags and a persistent tag manager
as authority.

### TagSpaces

Read `src/renderer/hooks/TaggingActionsContextProvider.tsx`,
`components/dialogs/AddRemoveTagsDialog.tsx`, `components/TagLibrary.tsx` and
`services/taglibrary-utils.ts`.

ADOPT: deduplication, clear add/remove intent, sidecar-aware mutation and
explicit failure reporting. ADAPT: Calamus uses its own managed Markdown
sidecars and rollback protocol. REJECT: Tag Library, local-storage/group
metadata, filename tags, search index, smart tags, geotags and AI tagging.

### Trilium Notes

Read the attribute model and bulk label actions under
`apps/client/src/entities/fattribute.ts`, `services/attributes.ts` and
`widgets/bulk_actions/label/`.

REJECT for W94: database-backed attributes, inheritance, promoted attributes,
relations, templates and automation. These are incompatible with Calamus'
plain-text, explicit and non-inferential boundary.

### nemo-tags — explicit file toggles, derived views and weak persistence

Read directly:

- `src/database.py`, class `TagDatabase`, especially `_load`, `_save`,
  `reorder_tags`, `assign_tag`, `unassign_tag`, `files_by_tag` and
  `tags_for_file`;
- `src/manager.py`, class `TagManager`, which acts as a narrow façade over the
  store and creates a temporary tagged-file view;
- `src/extension.py`, class `NemoTagsExtension`, especially `get_file_items`,
  `apply_tag`, `remove_tag`, `_delayed_invalidate` and
  `refresh_all_visible_files`;
- `src/ui.py`, class `TagLocationWidget`, including explicit refresh, reorder,
  rename, colour and delete commands.

Architecturally, nemo-tags owns one JSON authority containing both the tag
catalogue and a tag-to-file index.  The Nemo extension builds checked context
menu rows (`✓ name`) from that authority, mutates selected files explicitly,
then refreshes and invalidates the visible file information.

ADOPT: immediate visible action state; explicit assign/remove intent; a derived
focused list of owners; clear empty-state feedback; invalidating a derived view
only after the mutation.  ADAPT: Calamus uses exact-use rows and derived Name /
Most-used ordering instead of manual persistent ordering.  REJECT: JSON tag
authority, colour/emblem semantics, symlink views, global file refresh and
direct document-file tags.

Failure finding NEMO-01: `TagDatabase._load` catches every exception and silently
replaces unreadable state with an empty dictionary.  Failure finding NEMO-02:
`_save` writes directly to the authority path without temporary-file replace or
rollback.  Calamus therefore keeps fail-closed parsing, immutable preview, stale
tokens and atomic Markdown stores; it must never imitate silent empty recovery.

### Tagsistant — query tree, reasoner and explicit transaction outcome

Read directly:

- `src/path_resolution.h` and `src/path_resolution.c`, including the query-tree
  structure, path parsing, AND/OR/negation handling and query-tree destruction;
- `src/sql.h` and `src/sql.c`, including transaction helpers and query execution;
- `src/reasoner.c`, including the reasoner cache and expansion of inclusion,
  equivalence and exclusion relations.

Tagsistant is a semantic FUSE filesystem.  A path is parsed into a query tree,
resolved through SQL, optionally expanded by a relation reasoner, and finally
committed or rolled back when the query tree is destroyed with an explicit
transaction outcome.  This is a strong example of separating parse state,
query state and final mutation ownership.

ADOPT: one owner decides commit versus rollback; malformed requests fail before
mutation; derived caches/views are invalidated only after a successful change.
ADAPT: W94 uses an immutable `TagMutationPlan`, three `FileToken` stale checks
and reverse compensation rather than SQL.  REJECT: FUSE, SQL, reasoner, aliases,
autotagging, plugins, relation inference, archive/export semantics and caches.
The reasoner is specifically incompatible with Calamus' explicit-only Research
model and with postponed W93.

### TagStudio — ranked search and clean controller separation

Read directly:

- `src/tagstudio/core/library/alchemy/models.py`, especially `Tag`, `TagAlias`,
  parent relationships, shorthand and entry ownership;
- `src/tagstudio/core/library/alchemy/library.py`, especially `search_tags`,
  add/update/remove operations, session commit/rollback and migrations;
- `src/tagstudio/core/query_lang/ast.py` and `parser.py`, which model AND/OR/NOT
  search expressions separately from the UI;
- `src/tagstudio/qt/controllers/tag_suggest_box.py` and
  `tag_box_controller.py`, which separate suggestion, selected-tag actions, edit
  modals and search navigation;
- `src/tagstudio/qt/mixed/build_tag.py`, which owns the full tag edit form.

TagStudio is a database-backed media library with a rich Tag entity: name,
shorthand, aliases, parents, colour, hidden/category state and disambiguation.
Its useful narrow lesson is not that ontology, but its search ordering and
controller boundaries: exact and prefix matches are privileged over broad
contains matches, while selection, editing and searching remain separate
interactions.

ADOPT: exact/prefix/contains ranking; explicit edit mode; deterministic result
ordering; controller-owned selection.  ADAPT: W94 ranks exact logical tag names
first, then prefix matches, then other tag/owner matches; it adds derived Name
and Most-used sorting without a persistent order authority.  REJECT: SQLite,
aliases, hierarchy, colours as data, hidden/category tags, shorthand,
disambiguation, migrations and the full query language.

Failure finding TAGSTUDIO-01: several operations are robustly wrapped in
session rollback, but the broad model also performs some logically related
updates in multiple commit stages.  Calamus must preserve one approved
multi-authority plan and never expose success after only part of a rename or
merge has persisted.

### TMSU — separate rename/merge semantics and explicit-only usage

Read directly:

- `entities/tag.go`, including `Tag`, case-aware lookup helpers, `TagFileCount`
  and name validation;
- `storage/tag.go`, including exact/cased lookups, `RenameTag`, `DeleteTag` and
  `TagUsage`;
- `storage/filetag.go`, especially `explicitOnly`, assignment deduplication,
  copy and delete operations;
- `storage/storage.go`, type `Tx`, `Commit` and `Rollback`;
- `cli/rename.go` and `cli/merge.go`, which deliberately expose rename and
  merge as different commands;
- `cli/imply.go` and `query/parser.go`, inspected to define what Calamus must
  reject: implications and an AND/OR/NOT query language.

ADOPT: distinguish rename from merge before execution; count explicit uses;
merge by copying assignments with deduplication and then removing the source;
keep inferred and explicit assignments distinguishable.  ADAPT: the single
Calamus `Rename / Merge…` entry reports a live mode and the confirmation button
changes to `Rename Tag`, `Merge Tags` or `Normalize Spelling`.  REJECT: database,
VFS, tag values, implications and query grammar.

Failure finding TMSU-01: `renameExec` and `mergeExec` use `defer tx.Commit()`
immediately after `Begin`; an error returned after a partial sequence can still
reach commit.  Calamus explicitly rejects this pattern.  Its operation succeeds
only after all selected authorities persist; otherwise it compensates completed
writes in reverse order and returns failure.

## Failure-driven R2 decisions

W94 Candidate R1 reached the real T480 GTK lanes but failed the historical W92
Help contract.  The `Tag Integrity` topic had been shortened and no longer
contained the published worked-example sentence ``Only the logical variants of `Faith` become `doctrine```.  This was not a Tags model failure, but it proved
that Help history is part of the product contract and cannot be erased by a new
client.  R1 is retired; no commit or push occurred.

Candidate R2 is rebuilt as one unit and makes four evidence-based changes:

1. restores the complete historical Tag Integrity worked example while keeping
   the new Tags learning path;
2. adds derived `Sort: Name` and `Sort: Most used`, adopting usage-count views
   without creating a persistent tag order;
3. ranks exact logical tag-name matches before prefixes, then broader tag/owner
   matches;
4. classifies the requested operation before preview as Rename, Merge or
   Normalize spelling and exposes that mode in the dialog and confirmation
   action.

R2 deliberately does not copy nemo-tags manual persistent order, Tagsistant
reasoning, TagStudio ontology, or TMSU implications.

## Frozen W94 product contract

W94 adds one persistent `Tags` client to the Research Panel. It is a transient
projection over:

1. global `references.md`;
2. current-document `.source-notes.md`;
3. current-document `.scratchpad.md`.

The client contains:

- incremental Search with exact/prefix/contains ranking;
- derived sort: Name or Most used;
- scope: All, References, Source Notes, Scratchpad;
- `Variants only` filter;
- tag list with canonical display, total uses, R/N/S counts and warning state;
- exact-use list with authority, owner and stored spelling;
- Open, Rename / Merge, Remove, Normalize All and Refresh;
- explicit pre-preview mode: Rename, Merge or Normalize spelling;
- double-click/keyboard navigation to the owning Reference, Source Note or
  Scratchpad entry.

Rename, merge, remove and normalize must use a previewed immutable plan, stale
checks for every selected authority, canonical store writes and compensation in
reverse write order. The active manuscript is never rewritten by a tag
maintenance operation.

The historical `Tag Integrity…` dialog remains available as a compatibility
workflow. The normal W94 workflow is the Tags client and includes Scratchpad.

## Explicit exclusions

W94 does not add:

- a tag database, JSON inventory or hidden authority;
- hierarchy, parent tags, aliases as a second semantic system or tag groups;
- automatic extraction from document text;
- Add Tag to Selection in the manuscript;
- AI, inferred topics, ontology, graph, clustering or ranking;
- workspace-wide scanning, daemon or permanent watcher;
- W93 Related Entries, References/Source Notes links, Concepts, Themes or
  expanded Research Check.

## Acceptance contract

W94 requires:

- pure-model and three-authority transaction tests;
- failure/rollback and stale-sidecar tests;
- command/provenance wiring tests;
- Help topic and current-menu tests;
- real GTK panel ownership;
- true-App inventory, exact-use navigation and three-authority mutation;
- historical W90/W91/W92 GTK lanes without skips;
- compile, complete headless regression, source provenance and `diff --check`;
- manual desktop validation from an isolated copy under `~/Applications`.

## Second real-desktop failure and Candidate R3 reconstruction

Candidate R2 was not accepted. The real T480 GTK run again stopped in the
published W86/W92 Help lane, before any W94 panel lane. R2 had restored the
first asserted sentence but had rewritten the second invariant from
``unrelated tags`` to ``unrelated fields``. The GTK dialog therefore contained
semantically similar prose but no longer preserved the exact published worked
example. The failure markers were:

- `W92_HELP_HISTORICAL_GUIDE=FAIL`;
- assertion missing `unrelated tags`;
- `W94_R2_FAILURE_PHASE=real GTK and GIO lanes`;
- `W94_R2_OUTER_COMMAND_EXIT=1`.

This proves two process faults, not a GTK fault:

1. R1 deleted a published Help contract;
2. R2 repaired only the first observed assertion instead of restoring the
   authoritative W92 topic verbatim;
3. the headless Help gate checked one sentence, so it could not detect partial
   preservation;
4. the desktop runner spent time on many historical lanes before reaching the
   known high-risk Help lane.

Candidate R3 is therefore reconstructed from the published W92 source, not
patched in the desktop copy. It carries the W94 implementation as one unit but
uses the complete W92 `Tag Integrity` topic as an immutable compatibility
prefix. W94 explanation is appended under a subordinate heading rather than
rewriting the old topic.

R3 adds three defensive contracts:

- `test_published_tag_integrity_contract_is_preserved_verbatim` compares the
  parsed Help topic with the complete published W92 body, not isolated words;
- `prove-w94-scope.sh` repeats the same parsed-topic compatibility check and
  requires the full worked-example invariants, including `unrelated tags` and
  byte-identical manuscript language;
- `prove-w94-gtk-lanes.sh` runs the exact historical Help GTK lane first, then
  the two new W94 lanes, and only afterward the complete historical suite.

This order is evidence-driven and fail-fast. It does not weaken historical
coverage; it prevents another long run from discovering a known compatibility
risk only at the end.

### Mature-source conclusions applied after both failures

The newly audited software does not justify expanding W94. Instead, it
strengthens the transaction and presentation boundaries already selected:

- **nemo-tags** confirms that action state and owner visibility belong in the
  view, but its catch-all load recovery and direct JSON overwrite are explicit
  anti-patterns for Calamus. R3 keeps fail-closed parsing and never turns a
  damaged authority into an empty inventory.
- **Tagsistant** confirms that the component owning the operation must choose
  commit or rollback explicitly. R3 keeps one approved immutable plan and
  reverse compensation; no view callback can commit independently.
- **TagStudio** confirms exact/prefix ranking and controller-owned selection,
  while its aliases, parents and database migrations remain outside scope.
  R3 retains derived ranking only.
- **TMSU** confirms that rename and merge are different semantic operations,
  but its `defer tx.Commit()` pattern is rejected. R3 exposes the mode before
  confirmation and reports success only after all selected Markdown
  authorities have persisted.

The repeated Help failure does not require a different tag engine. It requires
preserving published user-facing contracts with the same discipline used for
Markdown authorities. R3 therefore changes no W94 production tag model beyond
R2; it repairs the delivery contract, test oracle and validation order.

## Third desktop run: gate false negative and Candidate R4 reconstruction

Candidate R3 did not reach the W94 GTK panel. The risk-first historical Help
lane itself passed (`Ran 1 test ... OK`, with the expected W86 markers), but the
new W94 wrapper immediately reported `W94_HELP_COMPATIBILITY_PREFLIGHT=FAIL diagnostics`.
The lane log contained none of the configured blocking diagnostics.

The root cause was exact shell return semantics in `scan_blocking()`:

- R3 used `grep ... && { return 1; }` inside a loop;
- on a clean log, every `grep` correctly returned 1 (not found);
- after the loop, the function inherited the status of the final clean `grep`;
- the caller interpreted that non-zero status as a blocking diagnostic.

The mature historical W90/W91/W92 gate scripts use an `if grep; then ... fi`
form whose completed `if` does not leak a clean `grep` status. Candidate R4 is
therefore reconstructed from published W92 with the complete W94 unit and an
explicit scanner contract:

- `scan_blocking()` returns 1 only after printing the exact blocking token;
- it ends with explicit `return 0` for a clean log;
- `--self-test-diagnostics` proves both clean-log acceptance and synthetic
  critical-log rejection without requiring GTK;
- `test_w94_gtk_gate_contract.py` executes that real shell self-test during the
  full headless suite;
- the scope gate requires the self-test contract;
- the expected full suite becomes 1387 tests.

This is a validation-gate defect, not evidence against the Tags architecture.
No Tags production module is changed from R3. No mature-source feature is added
in response: nemo-tags, Tagsistant, TagStudio, TMSU and the earlier corpus do
not illuminate a Bash status-propagation bug better than the already certified
Calamus W90/W91/W92 scripts. The relevant mature implementation for this
boundary is therefore Calamus's own published gate family.

## Third desktop attempt boundary — R4 failure and R5 reconstruction

The R4 desktop run reached the W94 Tags panel lane after the diagnostic scanner and
published Help compatibility lanes had passed.  The lane stopped before inspecting
production widgets because the test called the certified helper as
`named_widget(view.widget, name)`, while `calamus_gtk_test_driver.named_widget` has
the typed contract `named_widget(widget, name, widget_type)`.  The resulting
`TypeError` is a test-contract failure, not evidence that the Tags panel itself failed.

R5 is reconstructed from the published W92 baseline, not patched in the disposable
R4 desktop copy.  Production Tags modules remain unchanged.  The GTK test now uses
an explicit semantic-name to concrete-GTK-type map (`SearchEntry`, `ComboBoxText`,
`CheckButton`, `TreeView`, and `Button`).  A headless AST/inspection test and the
scope gate reject every W94 `named_widget` invocation that omits the widget type.
This moves the desktop-only failure boundary into the ordinary headless gate.

The user authorizes this as the final W94 desktop attempt before a mandatory new
full direct audit.  If R5 fails, W94 must be suspended and reconstructed only after
re-reading the relevant Calamus source and mature tag-management source corpus; no
further one-error-at-a-time candidate is permitted.

## Post-R5 suspension audit and unitary reconstruction

Candidate R5 reached the true-App Tags lane for the first time. Package,
scope, compile, typed widget lookup, diagnostic scanner, published Help
compatibility, 1389 headless tests, source provenance, the real Help dialog and
the isolated Tags panel all passed. The true App then aborted under
`G_DEBUG=fatal-criticals` with:

`gtk_range_get_adjustment: assertion 'GTK_IS_RANGE (range)' failed`

The failure occurred during the first `show_tags()` activation after the
Research shell had attached the `Gtk.Stack` child. Direct source tracing found
this synchronous path:

`App.show_tags -> ResearchPanelRuntime.show -> ResearchPanelViewAdapter.show_client
-> TagsRuntime.activate -> TagsController.refresh -> TagsPanelViewAdapter.render_tags`.

The R5 adapter replaced a `Gtk.ListStore`, selected a `Gtk.TreePath` and called
`Gtk.TreeView.scroll_to_cell()` in the same render transaction. The stack child
could be visible by name while mapping/allocation and its scrolled-window
adjustments were not yet stable. This is the only new W94 call that explicitly
requested viewport movement during first activation and is the primary
root-cause finding. The exact native C frame is not claimed without a native
backtrace; the design is nevertheless rejected because it violates the
mature-source and existing-Calamus lifecycle patterns below.

### Mature-source evidence reread after suspension

- **Tags `src/tag/tags-view.vala`** binds a `GLib.ListModel` to `Gtk.ListBox` and
  reacts to selected rows. It does not force a viewport reveal while rebuilding
  the tag collection. ADOPT: ListBox rows, row-owned identity and model/view
  separation. REJECT: forced scroll in render.
- **Calamus References, Source Notes, Scratchpad and Clip clients** already use
  `Gtk.ListBox`, replace rows, select a row and leave viewport ownership to GTK.
  ADOPT as the nearest certified architectural pattern.
- **QOwnNotes `TagManager::buildTagTreeForParentItem`** wraps selection changes
  in `QSignalBlocker`; its source explicitly leaves `processEvents()` disabled
  because it can crash sporadically during rebuild. ADOPT: suppress callbacks
  during rebuild and never pump/re-enter the toolkit to make a half-built view
  appear ready.
- **TagStudio search-panel controllers** separate result projection from widget
  visibility and perform visibility-dependent work in show-event boundaries.
  ADAPT: rendering is synchronous and viewport-free; optional focus/reveal is a
  cancellable post-map action.
- **Zim tag models** separate inventory/query projection from the GTK model and
  do not combine model replacement with adjustment access. ADOPT the same
  readiness boundary.
- **Gnote** keeps tag identity and ownership outside GTK. **TMSU** and
  **Tagsistant** remain transaction references only; they provide no reason to
  couple tag persistence with viewport lifecycle.

### Reconstructed view contract

The post-suspension candidate is rebuilt from published W92, not patched in the
R5 desktop copy. It preserves the GTK-free inventory and three-authority
transaction engine, but replaces both W94 `Gtk.TreeView` surfaces with custom
`Gtk.ListBoxRow` presentations:

- one tag row owns logical identity, canonical spelling, total count, R/N/S
  counts, derived colour and variant warning;
- one use row owns the exact immutable `TagUse` value and presents authority,
  owner and stored spelling;
- render removes/adds/selects rows only; it contains no `scroll_to_cell`, no
  `GtkAdjustment` lookup and no viewport mutation;
- selection callbacks are suppressed while rows are rebuilt;
- `TagsController.activate()` refreshes data only and remains GTK-free;
- `TagsRuntime.activate()` requests focus only after a successful refresh;
- the view queues focus through `GLib.idle_add` only after the stack child is
  mapped, and cancels pending map/idle work on unmap or destroy.

The true-App gate is strengthened to exercise the exact lifecycle boundary:
show Tags, refresh, switch to References, return to Tags, hide the Research
panel, show Tags again, refresh, navigate to an exact owner, return and perform
the three-authority mutation. `G_DEBUG=fatal-criticals` remains mandatory.

### Acceptance consequence

This is not an incremental R5 repair. R1-R5 remain retired. The new candidate is
one unitary reconstruction from W92 after the mandated direct audit. It may be
accepted only if the risk-first true-App lifecycle lane, the complete historical
GTK/GIO suite and manual desktop validation all pass without criticals or
skips.

## Rebuilt R1 True-App constructor failure and Rebuilt R2 contract repair

The post-R5 unitary Rebuilt Candidate R1 removed the unsafe TreeView viewport
path and passed all headless, Help, provenance and lifecycle-static gates, but
the first true-App lane failed before rendering any Tags data:

- `bin/calamus: App.__init__()` called `build_research_panel()`;
- `TagsRuntime.__init__()` built a valid `TagsPanelViewAdapter`;
- `TagsController.__init__()` rejected that adapter with
  `TypeError: view must implement TagsView`.

Direct source inspection found a stale interface duplicated across layers.
`calamus_tags_controller.TagsView` and its manual `required` tuple still
required `focus_search`, inherited from the pre-rebuild synchronous-focus
architecture. The rebuilt concrete adapter intentionally removed
`focus_search` and exposes `queue_activation_focus()` instead, because map/idle
focus is owned by `TagsRuntime` plus the GTK adapter. The pure `FakeView` in
`test_w94_tags_controller.py` still carried the obsolete method, so headless
controller tests accepted a surface that the real adapter correctly did not
provide.

This is classified as a product-boundary contract failure, not a GTK rendering
failure and not a test-wrapper failure. Rebuilt R1 is retired; no commit or push
occurred.

### Calamus source conclusions

Files and symbols read directly:

- `calamus_tags_controller.py`: `TagsView`, `TagsController.__init__`,
  `activate`, `refresh`, `_render`;
- `calamus_tags_panel.py`: `TagsPanelViewAdapter`,
  `queue_activation_focus`, `cancel_deferred_actions`, `_on_map_for_focus`;
- `calamus_tags_runtime.py`: `TagsRuntime.__init__`, `activate`;
- `test_w94_tags_controller.py`: `FakeView`;
- `test_w94_tags_view_lifecycle_contract.py`;
- `test_w94_tags_app_desktop_e2e.py`;
- mature Calamus view protocols in `calamus_reference_controller.py`,
  `calamus_source_note_controller.py`, `calamus_scratchpad_controller.py`,
  `calamus_reference_set_controller.py` and `calamus_clip_collection.py`.

The accepted design is consumer-driven interface segregation:

1. `TagsView` contains only members actually consumed by `TagsController`;
2. GTK map/focus/cancellation methods are excluded from the GTK-free controller
   protocol;
3. `TagsRuntime` owns lifecycle affordances and calls the concrete adapter;
4. the fake controller view deliberately lacks `focus_search` so a stale
   requirement fails headless;
5. diagnostics name every missing member rather than emitting a generic type
   error;
6. AST gates compare controller consumption, Protocol members and concrete
   adapter surface.

### Mature-source re-audit for the interface boundary

**Tags (Vala/GTK)** — `src/tag/tags-view.vala` and
`src/window/main-window.vala`: `TagsView` is a concrete GTK component whose
`Gtk.ListBox` exposes selection signals; the main window connects application
actions directly. Its data-facing model binding does not pretend that focus or
window lifecycle is a tag-domain operation. **ADOPT:** concrete view owns GTK
signals and lifecycle; domain/controller consumes only tag state. **REJECT:**
expanding the data contract with unrelated window affordances.

**QOwnNotes** — `src/managers/tagmanager.cpp`, especially
`TagManager::reloadTagTree()`: tree rebuild, selection restoration and widget
signals remain inside the UI manager, with reentrancy explicitly controlled.
**ADOPT:** view/UI manager owns focus, selection and signal suppression;
controller contract remains limited to semantic operations. **REJECT:** a
single manually duplicated interface that combines semantic and lifecycle
members.

**TagStudio** — Qt controller and modal/view sources, including
`tag_color_manager.py::showEvent`: visibility-dependent initialization is
performed in the concrete widget lifecycle, while controller/model APIs stay
separate. **ADAPT:** Calamus keeps map/idle focus in `TagsPanelViewAdapter` and
`TagsRuntime`; it does not expose that method to `TagsController`.

**Zim 0.76.3** — `zim/notebook/index/tags.py`: `TagsView` is an index/query
object, not a GTK widget contract, and contains only tag-domain lookup/list
operations. **ADOPT:** name interfaces by the consumer and keep domain
surfaces narrow. **REJECT:** mixing viewport or focus into tag projection APIs.

**Gnote** — `src/itagmanager.hpp`: `ITagManager` enumerates only tag-domain
operations (`get_tag`, `get_or_create_tag`, `remove_tag`, `all_tags`). UI
signals and focus live elsewhere. **ADOPT:** explicit interface segregation and
one owner per responsibility.

TMSU, Tagsistant, nemo-tags and TagSpaces were checked again but do not provide
a stronger UI-interface lesson for this failure; their prior transaction,
explicit-action and rejection decisions remain unchanged.

### Rebuilt Candidate R2 changes

Rebuilt R2 is reconstructed from published W92, not patched in the failed
desktop copy. It preserves the ListBox/two-phase architecture and changes only
the proven interface boundary:

- removes `focus_search` from `TagsView`;
- defines `TAGS_VIEW_REQUIRED_MEMBERS` from the controller consumer surface;
- emits a missing-member diagnostic listing exact names;
- removes `focus_search` from the pure `FakeView`;
- adds headless AST contracts proving Protocol == controller consumption and
  adapter satisfaction;
- adds a real-GTK runtime-construction lane before the full true-App scenario;
- keeps true-App lifecycle, exact-use navigation and three-authority mutation
  as the next risk-first lane.

No database, hidden authority, hierarchy, inference, AI, watcher or W93 scope is
introduced.

## Rebuilt R2 persistent GtkRange failure and Rebuilt R3 staged selection redesign

### Evidence from the second rebuilt desktop failure

Rebuilt R2 passed the package manifest, source checksum, W94 scope gate,
compilation, consumer-driven view contract, diagnostic scanner self-test,
published Help compatibility, 1395 headless tests, source provenance, the real
Help lane and the concrete `TagsRuntime` construction lane.  The true App lane
then aborted under `G_DEBUG=fatal-criticals` with:

```text
Gtk-CRITICAL: gtk_range_get_adjustment: assertion 'GTK_IS_RANGE (range)' failed
status=133
```

This is decisive negative evidence against the earlier narrow hypothesis that
`Gtk.TreeView.scroll_to_cell()` alone caused the failure: Rebuilt R2 had already
removed `Gtk.TreeView`, `Gtk.ListStore`, explicit viewport access and
`scroll_to_cell()`, yet the same GtkRange critical survived.  Rebuilt R2 is
retired; no commit or push occurred.

The remaining W94-specific lifecycle operations not shared by the standalone
runtime lane were:

1. visual row selection performed synchronously while the newly selected
   `Gtk.Stack` child was still being rendered;
2. automatic search focus scheduled immediately after the child mapped;
3. the full App shell attaching/detaching the Research widget through
   `RightPanelHost`.

Without a native backtrace it would be unsound to claim which internal GTK
frame called `gtk_range_get_adjustment`.  Rebuilt R3 therefore does not make a
single unobservable one-line fix.  It removes both W94-owned triggers that can
ask GTK to reveal or focus content during stack activation, and it splits the
true-App proof into process-isolated stages so a future abort is attributed to
construction, mapping, document opening, Tags activation or the later
multi-authority workflow.  When `gdb` is available, a status 133/134 lane is
rerun automatically and its native backtrace is retained beside the lane log.

### Direct Calamus source findings

Read again:

- `calamus_tags_panel.py`, especially `render_tags`, `render_uses`,
  `queue_activation_focus`, `_run_deferred_focus` and row selection;
- `calamus_tags_runtime.py`, especially `activate`;
- `calamus_research_panel.py`, `ResearchPanelRuntime.show`;
- `calamus_research_panel_view.py`, `show_client`, selector/stack signal guards
  and `_activate`;
- `calamus_right_panel.py`, `show`, `hide`, `_detach_active` and
  `_configure_widget`;
- `calamus_reference_panel.py`, `calamus_source_note_panel.py` and
  `calamus_scratchpad_panel.py` for established ListBox rendering;
- `tests/test_w94_tags_app_desktop_e2e.py` and
  `scripts/prove-w94-gtk-lanes.sh` for the exact order of true-App operations.

The R2 view still called `select_row()` inside both render methods and later
called `SearchEntry.grab_focus()` from an idle callback.  Either operation can
cause GTK to reveal a descendant through its scrolled ancestor.  The isolated
runtime constructor did not map or activate the client, so it could not exercise
that path.  The full true App did.

Rebuilt R3 freezes these boundaries:

- `render_tags()` and `render_uses()` may create/remove rows and store pending
  logical selection only; they may not call `select_row`, scroll, adjustment or
  focus APIs;
- visual selection is applied from one cancellable post-map idle callback;
- activation does not move keyboard focus;
- pending logical selection remains readable before the idle runs, so the
  controller stays deterministic without using GTK timing as data state;
- unmap and destroy cancel the callback;
- each true-App stage is a separate process and publishes an explicit marker.

### Mature-source comparison after the persistent failure

#### Tags (Vala/GTK)

`TagsView` and `TagRow` keep tag identity and hit counts in rows, but do not make
search focus or viewport movement part of the tag-domain contract.  ADOPT the
row-owned identity and explicit user selection.  ADAPT by delaying Calamus'
visual selection until the stack child is mapped.  REJECT automatic focus as an
activation requirement.

#### QOwnNotes

`TagManager::reloadTagTree` blocks selection-related signals while rebuilding
and intentionally avoids event-loop pumping because reentrant UI work can
produce sporadic crashes.  ADOPT the non-reentrant rebuild rule.  Rebuilt R3
sets pending state during render and applies one guarded selection afterward.

#### TagStudio

Visibility-dependent work is performed from widget lifecycle hooks rather than
from the data controller.  ADOPT the separation between model refresh and
post-show visual state.  Calamus uses map plus one idle callback, cancelled on
unmap/destroy.

#### Zim 0.76.3

Tag projections and counts are model operations; tree/list selection is a view
concern.  ADOPT the strict boundary.  The Calamus controller never receives a
focus or map API.

#### Gnote

`TagManager` remains independent of focus, scroll and viewport ownership.
ADOPT the lifecycle-free domain interface.

#### TMSU and Tagsistant

These remain transaction references only.  Their plan/commit/rollback lessons
continue to govern the three Markdown authorities, but they provide no reason
to entangle tag mutation with GTK selection or focus.

### Rebuilt R3 acceptance boundary

The next desktop run must pass, in separate processes and in this order:

1. concrete Tags runtime construction;
2. true App construction;
3. true App map with Research still detached;
4. document opening before Tags activation;
5. Tags activation with no focus steal and post-map row selection;
6. refresh/switch/hide/show/navigation/rename across all three authorities;
7. standalone panel semantics;
8. the full historical W92 GTK/GIO suite.

A failure at status 133 or 134 must retain a native `gdb` log when `gdb` exists.
No commit or push is permitted before all automatic lanes and the manual desktop
check pass.

## Rebuilt R3 resize validation failure and Rebuilt R4 responsive closure

Rebuilt R3 passed every automatic W94 lane and every manual functional Tags
check. The document remained byte-identical and the process closed normally.
Manual desktop validation nevertheless found one blocking lifecycle defect: the
Research Panel could be resized on first use, but after closing it with the
panel X and reopening it, the divider became effectively locked by the populated
Tags client. W94 therefore remained open; no commit or push was permitted.

### Direct Calamus source audit

The failure is explained by the composition of two independent width
constraints:

- `calamus_right_panel.py`, `RightPanelHost.show`, `_detach_active` and
  `_configure_widget`, reattached the Research widget with
  `Gtk.Paned.pack2(widget, False, False)`, reapplied a positive
  `set_size_request(panel_width, -1)`, and reset the divider to the default on
  every show;
- `calamus_tags_panel.py`, `build_tags_panel_view`, placed Scope, Sort and
  Variants in one horizontal row and placed three command buttons in another
  horizontal row. Populated owner labels and button labels increased the
  child's natural requisition.

With `shrink=False`, Gtk.Paned was not allowed to reduce the child below that
requisition. Reattaching the already populated stack child recalculated a large
natural width, so the visible handle no longer behaved as a usable resize
boundary. This is a container/layout defect, not a tag-domain or transaction
defect.

Calamus already contains the correct local precedent in
`calamus_left_panel.py`, `LeftPanelHost._configure_widget`: it explicitly uses
`widget.set_size_request(-1, -1)` and documents that a positive request can turn
a side pane into a top-level minimum-width constraint. `LeftPanelHost.show`
also packs its child with shrink enabled. Rebuilt R4 adopts the same geometry
principle for the right panel.

Rebuilt R4 changes the boundary as follows:

- `RightPanelHost` packs the right child with `shrink=True`;
- the child always has size request `(-1, -1)`;
- Gtk.Paned remains the sole width authority;
- the last user-selected panel width is captured before detach and restored
  after show;
- a remembered width is bounded only when the window becomes too small to keep
  the editor viewport floor;
- calling show for an already visible section never resets the divider;
- the Tags controls and actions are stacked vertically, long labels are
  ellipsized and width-bounded, and both scrollers disable natural-width
  propagation.

### Mature-source comparison for splitter and responsive-panel ownership

#### Zim 0.76.3

Read `zim/plugins/tags.py`,
`TagsNotebookViewExtension.__init__`. The Tags plugin restores
`uistate['vpane_pos']`, applies it with `set_position`, and updates the stored
value from `notify::position`. ADOPT the principle that pane position is user
state and must survive hide/show; ADAPT it to session-local state inside
`RightPanelHost` because W94 does not add a new persistent settings authority.

Read `zim/plugins/tags.py`, `on_preferences_changed`: the tag tree switches
between ellipsized labels and horizontal scrolling rather than forcing a wider
side pane. ADOPT ellipsis and bounded row content. REJECT a horizontal scrollbar
for Calamus because the compact Research client should remain readable without
sideways scrolling.

#### QOwnNotes

Read `src/dialogs/settingsdialog.cpp`, `SettingsDialog` splitter construction
and close persistence, and `src/dialogs/dictionarymanagerdialog.cpp`, where
`QSplitter::restoreState()` and `saveState()` preserve user geometry instead of
reapplying a hard-coded size on every show. ADOPT preservation of the user
chosen divider state. ADAPT to one numeric right-panel width because Gtk.Paned
has one divider and Calamus needs no serialized Qt-style splitter blob.

#### TagStudio

Read `src/tagstudio/qt/views/main_window.py`, `MainWindowView` construction of
`content_splitter`: the splitter is the layout authority, children are added
with stretch factors, and no child is given a fixed width equal to the current
pane width. Read `src/tagstudio/qt/views/preview_panel_view.py`, where a nested
splitter owns preview/info allocation. ADOPT splitter ownership and flexible
children. REJECT database and ontology features unrelated to the resize defect.

Read `src/tagstudio/qt/mixed/file_attributes.py` and other descriptive widgets:
long labels use word wrapping rather than defining a wider window. Calamus
adapts this with line wrap for status text and ellipsis/tooltips for compact
owner rows.

#### Tags (Vala/GTK)

Read `src/tag/tags-view.vala`, `TagsView`, and `src/tag/tag-row.vala`, `TagRow`.
The tag inventory is a `Gtk.ListBox` inside a `Gtk.ScrolledWindow`; rows own
compact title, subtitle and hit-count widgets, while the scroller owns overflow.
ADOPT compact row ownership and derived counts. Calamus additionally disables
natural-width propagation because its list is embedded in a detachable narrow
Research Panel.

### All tags A–Z discoverability

The upper W94 list already represented the complete logical vocabulary when
Search was empty, scope was All authorities, Variants only was off and sorting
was by name. Desktop validation showed that this was not discoverable enough.
Rebuilt R4 adds one explicit `All tags A–Z` action that resets those four
presentation settings without writing any authority. The status line then says
`All tags A–Z`, and the sort label is `Name (A–Z)`. No duplicate list, tag file
or hidden inventory is introduced.

### Tutorial acceptance

The existing Help topic was a correct command reference but did not provide the
learning curve requested in desktop validation. Rebuilt R4 preserves that
reference and adds a separate progressive tutorial containing:

- the logical-tag / stored-variant / exact-use mental model;
- a realistic article, Reference, Source Note and Scratchpad scenario;
- the complete A–Z inventory and count interpretation;
- Search, scope and ranking exercises;
- exact-use navigation;
- Normalize versus Rename versus Merge;
- a safe mutation walkthrough;
- stale detection, rollback and byte-identical document guarantees;
- morning, source-work and end-of-session workflows;
- common stopping rules and recovery guidance.

### Rebuilt R4 acceptance boundary

W94 can close only if a real-App lane proves:

1. open Tags and populate the client;
2. drag the divider to a medium width;
3. close Research through the normal runtime boundary;
4. reopen Tags and recover that width;
5. drag narrower and wider after reopen;
6. close and reopen once more and preserve the latest width;
7. complete all existing Tags, transaction, Help and historical GTK/GIO lanes;
8. pass manual review of resize, All tags A–Z, tutorial and normal close.

No production tag-domain or multi-authority mutation code is changed by this
resize closure.
