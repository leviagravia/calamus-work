# Calamus W97 — Bibliography Manager Core Search/Model Rebuild audit

Published baseline: `199459fb023e4862407f7eb60318192f276d3239`
Rebuild line: Candidate R1, valid attempt 1/2

## Exact trigger

The dedicated Candidate R1 and Candidate R2 product logs fail at the same assertion after `search.set_text("patristics")`. The test performs one immediate GTK pump and expects the filtered list, but `Gtk.SearchEntry.search-changed` has not yet delivered its delayed notification. The original three rows remain and cleanup completes normally. This is a false-negative test oracle, not evidence of an application crash.

## Choice: explicit delayed/coalesced search

Immediate search would be simpler, but it would recompute complete-field projection and rebuild list/detail once per keystroke. Calamus targets modest hardware and libraries that can grow to hundreds or thousands of records. Explicit coalescing is therefore the better product contract.

The implementation no longer delegates timing semantics implicitly to `Gtk.SearchEntry.search-changed`. It uses `changed` only as an input event and owns a GTK-free `CoalescedQueryDispatcher` with an injected scheduler:

- fixed quiet period: 150 ms;
- one pending source;
- generation counter;
- cancel older source on newer text;
- deliver only the latest query;
- cancel on panel destruction;
- expose pending/delivery diagnostics for true-App evidence.

## Model and selection correction

`ReferenceController` now owns `_selected_key`. The GTK row is only a presentation object. User selection is synchronized into the controller; filtering and refresh decide whether the key remains visible and derive a new row selection afterward. Programmatic navigation cancels pending search and clears the entry before resetting filters.

This is an incremental GTK3 adaptation of the persistent model/selection separation observed in GNOME Builder, GNOME Text Editor, GNOME Citations, JabRef, KBibTeX, Zotero, Referencer and coBib. A full GtkTreeModel migration remains deferred to W99.

## True-App completion oracle

The true-App gate now distinguishes request from completion:

1. rapid partial texts are submitted;
2. marker `search-requested` is flushed;
3. a bounded loop pumps GTK and sleeps briefly;
4. completion requires both `last_delivered_query == "patristics"` and exact visible keys;
5. exactly one delivery must have occurred;
6. only then is marker `search-delivered` emitted.

Every later search transition uses the same bounded completion rule. A single `pump()` is prohibited as a search completion oracle.

## Runner correction

The package runner executes logged commands inside an `if ...; then ... else ... fi` condition. This prevents inherited `ERR` handling from pre-empting status capture. It always records status, prints the complete dedicated log, and only then returns non-zero to the outer fail report. A deliberate exit-7 self-test verifies this contract during package preflight.

## Anti-recurrence decisions

ADOPT:
- explicit coalescing;
- generation cancellation;
- controller-owned semantic selection;
- bounded true-App completion;
- complete log before FAIL.

ADAPT:
- 150 ms GTK3 timeout;
- existing ListBox render transaction retained under controller selection ownership.

REJECT:
- implicit toolkit delay treated as synchronous;
- one-pump assertion;
- row widget as canonical selected identity;
- `set +e` plus inherited ERR trap as profile capture.

DEFER:
- configurable delay;
- persistent GtkTreeModel/TreeView migration;
- performance telemetry and very-large-library virtualization.
