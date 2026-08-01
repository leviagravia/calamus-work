# Calamus W96 — Editor-Handoff Rebuild Contract

**Lineage:** Editor-Handoff Rebuild Candidate R2
**Published baseline:** `792ca0f76db39525a9052bd61e43fe929988af2e`
**Product scope:** Document Overview Core — Gate C
**Repository rule:** the canonical repository remains read-only until complete desktop PASS.

## 1. Independent-line identity

This line is not Profile-Owned Rebuild R3.
Profile-Owned Rebuild R1/R2 remain retired after FAIL 2/2. Editor-Handoff Candidate R1 had one INVALID desktop run,
then its Desktop-Isolated Reissue produced valid FAIL 1/2 because the transient
Document Overview window still covered the correctly navigated editor.

Candidate R2 is the second and final attempt of the Editor-Handoff line. The
complete source is reconstructed as one unit from the published baseline.

## 2. Navigation handoff contract

A Document Overview action that targets the document is complete only when one
App/runtime-owned operation performs all of these effects:

1. validate the destination or source range;
2. hide the non-modal Document Overview tool window without destroying it;
3. move the insert mark or exact selection;
4. reveal the target in the editor viewport;
5. present the main editor window and focus its text view.

The tool window is transient for the main Calamus window. On GTK/X11 window
managers such as Linux Mint, a visible transient can remain stacked above its
parent even after `parent.present()` and `Gtk.TextView.grab_focus()` succeed.
Therefore a widget-focus request and a parent presentation are insufficient as
a user-visible handoff while the transient remains visible.

Classification:

`CALAMUS-DOCUMENT-OVERVIEW-TRANSIENT-STACKING-01`

Observed failure:

- Editor-Handoff R1 Reissue 1 selected the exact Markdown source range;
- `Go to Destination` reached the exact Method offset and viewport;
- all automatic W96 profiles passed;
- the visible transient Document Overview window still covered the editor;
- manual Test 8 therefore failed and consumed FAIL 1/2.

Candidate R2 behavior:

- direct document navigations hide Document Overview before invoking the App
  navigation callback;
- the runtime and its single view instance remain alive;
- `Navigate → Document Overview` presents the same instance again;
- a failed or exceptional navigation restores Document Overview immediately;
- delegated Research actions keep their existing tools and are not converted
  into document handoffs.

Barriers:

- headless runtime tests prove hide-before-action, preserved single instance,
  reopen of the same instance, and restore-on-failure;
- source tests require the view `hide()` boundary and forbid a handoff that
  leaves the transient visible;
- the true-App GTK profile verifies that Document Overview is neither visible
  nor mapped after section, link-source and link-destination navigation;
- the same profile reopens the identical overview instance between actions;
- the manual checklist requires the overview to disappear and the editor target
  to be visibly unobstructed.

## 3. Desktop window-manager oracle

The OS/WM global active application is diagnostic only. An unrelated program
can take focus after Calamus calls `present()`. Automatic gates therefore assert
only product-owned invariants:

- exact cursor or selection;
- mapped and visible main editor window;
- internal TextView focus;
- target intersection with the viewport;
- hidden/unmapped Document Overview transient during editor handoff.

`Gtk.Window.is_active()` may be logged but never used as a PASS/FAIL oracle.

Classification:

`CALAMUS-DESKTOP-WM-ACTIVE-ORACLE-01`

## 4. Stale-state observability contract

Editing while Document Overview is open performs only `mark_stale()`. It does
not refresh, clear the selected item or run a navigation action.

The stale action itself is fail-closed:

1. the old action is blocked;
2. the dossier is refreshed at that moment;
3. the old selection is cleared;
4. a notice states `Action blocked` and `has now been refreshed`;
5. the user must select the item again.

Classification:

`CALAMUS-DOCUMENT-OVERVIEW-STALE-OBSERVABILITY-01`

The Candidate R1 Reissue manual evidence confirms this behavior as PASS.

## 5. Retained anti-recurrence barriers

All barriers from `CALAMUS_W96_PROFILE_OWNED_REBUILD_CONTRACT.md` remain
binding, including exact package topology, profile-owned capabilities, separate
inventory/profile interpreters, zero skips in release gates, persistent
category rows, no embedded Python in Bash, no simulated desktop evidence, and
fresh extraction of the final ZIP followed by the identical preflight runner.

Every profile log must be surfaced before failure propagation.

## 6. Product architecture retained

```text
DocumentDossierInputs
→ immutable DocumentDossierSnapshot
→ DocumentDossierController
→ GTK-free DocumentOverviewRuntime/model
→ App-owned navigation and delegated-action boundary
→ GTK-only DocumentOverviewViewAdapter
```

No database, watcher, background index, AI, new authority, automatic repair,
plugin framework or project-management layer is introduced.

## 7. Failure accounting

Editor-Handoff Candidate R1 Reissue 1 is valid FAIL 1/2. Candidate R2 is attempt 2/2 and the final permitted candidate in this line. Any valid desktop failure
retires the entire Editor-Handoff line. No Candidate R3 or narrow patch is
permitted.
