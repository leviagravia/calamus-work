# W97 R1/R2 Exact Product Log and Search-Signal Audit

## Scope

Read-only audit only. No candidate was changed, no test was rerun, and the
published baseline remains W96 commit
`199459fb023e4862407f7eb60318192f276d3239`.

## Exact evidence

The dedicated product logs prove that R1 and R2 failed at the same assertion:

- R1: `tests/test_w97_bibliography_app_desktop_e2e.py`, line 144.
- R2: the same test, line 165 after added diagnostic markers.
- Expected visible keys: `['alpha2020']`.
- Actual visible keys: `['beta2021', 'alpha2020', 'gamma2019']`.

R2 markers terminate as follows:

1. `initial-state-verified`
2. `search-applied`
3. assertion failure
4. orderly `cleanup-enter`
5. orderly `cleanup-complete`

There is no segmentation fault, GTK critical, Python exception in product code,
row-destruction frame, or lifecycle crash in the exact failing execution.

## Exact source chain

Production binding in `calamus_reference_panel.py`:

```python
self.search.connect("search-changed", lambda entry: callback(entry.get_text()))
```

True-App test sequence:

```python
search.set_text("patristics")
pump()
_marker("search-applied")
self.assertEqual([...], ["alpha2020"])
```

Test helper `pump()`:

```python
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
```

`pump()` drains events already pending at the instant of the call. It does not
wait for a future delayed search notification or poll until a semantic
postcondition becomes true.

Gtk.SearchEntry's `search-changed` contract is deliberately suitable for search
UI and may be emitted after a short delay rather than synchronously with
`set_text()`. The logs are exactly consistent with that contract: the entry text
was set, but the callback had not yet refreshed the list when the assertion ran.
The marker name `search-applied` was therefore inaccurate: it meant only
`set_text + immediate pump completed`, not `search projection committed`.

## Mature-source corroboration

GNOME Text Editor uses immediate `changed` / `notify::text` bindings where it
needs direct propagation from text mutation. GNOME Builder also distinguishes
immediate text notifications from deliberately delayed/coalesced search work
and uses explicit timeout or model-update boundaries. These patterns confirm
that a test must wait for the semantic result appropriate to the selected
signal; it must not equate a single main-loop drain with completion.

## Correct classification

The exact failing condition is:

`CALAMUS-W97-SEARCH-CHANGED-DELAYED-TEST-ORACLE-01`

Both R1 and R2 desktop runs are engineering-invalid product runs caused by a
false-negative true-App timing oracle. They do not prove that interactive
Bibliography search is defective. They also do not prove the earlier
ListBox-row lifecycle hypothesis.

The earlier lifecycle audit remains useful as a source-level architectural risk
and future hardening direction, but it must not be cited as the cause of these
two failures.

## External editor

Working in another editor did not cause this assertion. The test calls
`Gtk.SearchEntry.set_text()` programmatically and does not use global active
window state, OS-level keyboard injection, `is_active()`, or window stacking as
an oracle.

## Runner evidence correction

The dedicated product log did exist. The main runner failed to print it because
its ERR-trap/error-propagation design intercepted the profile failure before the
normal `run_profile()` evidence-reporting path completed. The initial
"no such file" report resulted from looking in the Downloads root before
locating the per-run directory. The evidence file itself was preserved.

## Stop policy

The user's stop remains binding:

- no Candidate R3;
- no narrow patch;
- no unchanged rerun;
- no Git mutation;
- no implementation work.

A future resumption, only after explicit authorization, must begin from the
published W96 baseline and must first freeze a corrected validation contract.
At minimum the future contract must choose one of these explicit strategies:

1. bind an immediate `changed` signal if immediate filtering is the product
   requirement; or
2. keep `search-changed` and use a bounded `until()` helper that waits for the
   expected projected keys/detail state; and
3. test that the callback actually ran, rather than relying on a marker placed
   after `set_text()`.

The architecture should still move toward controller-owned semantic selection
and a persistent model, as documented by the GNOME Builder/Text Editor audit,
but that is a separate redesign decision rather than the fix for the exact
false-negative assertion.
