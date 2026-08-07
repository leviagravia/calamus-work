# CALAMUS MO Supplement — W107

## Authority

- Baseline: `e8befafaf7f75d958eabbd2e273f83c630042b84` (published W106).
- Contract explicitly accepted and W107 implementation explicitly authorized by Luciano.
- `Ctrl+Alt+L` Line Numbers removal explicitly authorized in W107; no replacement.
- W108 not started.

## Architectural decisions

- No generic application host/context/service locator/event bus.
- Research composition extracted to one typed bundle.
- Workspace host orchestration receives stores/state/session, the five concrete
  Workspace collaborators it directly invokes, and narrow presentation ports;
  it never retains WorkspaceComponents. GTK parent remains only in the GTK adapter.
- Search runtime owns application search orchestration, mutation remains W103.
- Spellcheck runtime is GTK-free/widget-free, mutation remains W103.
- Print lifecycle/pagination moved to GTK print runtime.
- New subsystem owners are private typed bundles; do not create a new public-alias monolith.
- `App.state` remains forbidden.

## Current measured App reduction during implementation

At the accepted W106 baseline: App ≈2898 lines.
W107 implementation currently reduces App to ≈2354 lines while retaining
compatibility delegates; final exact metrics are established at Candidate seal.
W108 remains responsible for final shell collapse.

## Known warnings/debts retained

- GTK CSS `:prelight` deprecated; use `:hover` in later cleanup.
- `Gtk.Widget.override_font` deprecated in line-number gutter.
- historical test-only GTK critical/resource warnings remain visible.
- Full feature variants remain deferred.

## Validation rule

Never use Ctrl+Alt+L as a manual Calamus shortcut on Linux Mint. In W107 it is
no longer a Calamus default accelerator at all.

## Candidate R1 desktop failure / R2 repair

R1 is FAIL 1/2 on T480. Full discovery reached two real-GTK Authoring Bridge
tests and failed during `App()` construction because `calamus_ui.build_menu()`
called `populate_recent_workspaces_menu()` before `_components` existed.
Classification: W107 construction-order/lifecycle defect, not a historical
oracle failure.

R2 repair: retain the thin Workspace App delegate and defer only the initial
Recent Workspaces dynamic-menu projection until the core composition barrier has
completed. No Workspace domain semantics or W107 host-port ownership changes.

## R1/R2 desktop failure chronology and post-FAIL2 decision

- R1 FAIL 1/2: Recent Workspaces projection occurred before `_components` was
  constructed.
- R2 FAIL 2/2: WorkspaceHostRuntime retained a pre-startup WorkspaceComponents
  record while the final core bundle contained a `replace()`d record.
- Mandatory STOP and direct source re-audit applied.
- Post-FAIL2 decision: remove aggregate ownership from WorkspaceHostRuntime; use
  direct concrete collaborators and W101 `SetOnceReference` for the bounded
  construction cycle.
- R1/R2 candidates and patches remain RETIRED / DO NOT REUSE.

## Post-FAIL2 implementation resumption

After the mandatory R2 STOP and direct ownership/mature-source re-audit, Luciano
explicitly instructed to continue work on W107. The post-audit candidate line is
therefore authorized. It is not an automatic third retry.

## R3 post-audit desktop failure / R4 test-authority repair

R3 POST-AUDIT is desktop FAIL 1/2 in the resumed post-audit retry pair.
The T480 passed current identity and reached the subsystem true-App lane after
full automated regression. Search replace-all completed and changed the buffer,
then the test attempted the nonexistent `DocumentSession.dirty` attribute.

W102 freezes `DocumentSession.modified` as the sole dirty-state authority.
Direct mature-source review also favors querying the concrete document/editor
modified/save-point authority instead of adding a duplicate compatibility
state alias. Classification: true-App oracle/API-name defect, not W107 product
runtime defect.

R4 changes no product/runtime module relative to R3. The true-App oracle uses
`DocumentSession.modified` plus `requires_save_confirmation()`, and the existing
headless W107 contract test rejects `document_session.dirty` so this mistake is
caught without GTK.

Luciano's current retry authority: R3 = FAIL 1/2; R4 is the one remaining valid
retry. A valid R4 desktop FAIL is FAIL 2/2 and triggers mandatory STOP, with no
automatic R5 and a return to direct Calamus + user-supplied mature-source audit.
