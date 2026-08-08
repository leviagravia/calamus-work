# Calamus W108 — Thin GTK Shell — Consolidated Contract after Post-Audit FAIL 2/2

**Status:** ACCEPTED / AMENDED / RE-FROZEN AFTER SECOND VALID FAIL 2/2 STOP / IMPLEMENTATION NOT RESTARTED  
**Date:** 2026-08-08  
**Baseline:** `e16cc21b8a900298406ae8cc4776f6f1ec658e93` — W107 CLOSED/CERTIFIED/PUBLISHED

## 1. Authority and supersession

The 2026-08-07 original freeze and the first 2026-08-08 post-FAIL2 re-freeze remain immutable historical evidence. This contract supersedes them only for future W108 work after the second mandatory STOP/re-audit.

All four failed Candidate artifacts remain valid failures, RETIRED and DO NOT REUSE. No failed Candidate may be a reconstruction or patch base.

Production architecture remains the audited Thin GTK Shell direction unless explicitly amended here. The new amendments concern event/callback boundary preservation and validation closure.

## 2. Purpose

Convert W101–W107 ownership migration into a genuinely thin concrete GTK shell while preserving behavior, historical authorities and callback/event semantics. W108 is architecture-only: no product expansion, general source cleanup, savepoint redesign, post-W108 roadmap work or monolith-closure work.

## 3. Production architecture — PRESERVED

At completion:
- exact 39 W107 baseline whole-App reusable seams are removed/narrowed;
- semantic whole-App reusable seam count is zero regardless of parameter renaming;
- core composition is App-free through immutable typed root input(s), decomposed immediately;
- no reusable builder receives App or imports another builder;
- `CoreApplicationComponents` remains an ownership record and is not passed downstream;
- named `SetOnceReference` remains the only bounded late-reference mechanism;
- exact 24 W101 compatibility attributes remain until their historical removal authority;
- W104 stable command IDs and exact 117 application bindings remain;
- application command binding is App-free through explicit family ports/callables;
- W105 `MenuGtkAdapter` remains sole global menu widget-state projector;
- authorized historical whole-App gateways are narrowed/retired;
- W99 lifecycle and W102–W107 authorities remain exact;
- Character Map remains a dedicated GTK presentation boundary outside App;
- concrete shell may retain genuine top-level GTK/WM event endpoints, dialog parentage and bounded presentation callbacks;
- no `AppHost`, `ApplicationContext`, `AppServices`, service locator/registry, event bus, generic DI bag or generic command god-object.

## 4. Compatibility construction ordering — PRESERVED

1. construct W101 core owners through App-free typed composition;
2. project exact 24 W101 aliases explicitly in concrete shell;
3. perform Workspace startup-root binding after aliases exist;
4. assign final composition-complete `_components` exactly once;
5. perform initial Recent Workspaces projection only after final `_components` assignment.

No runtime may observe a partially constructed owner graph.

## 5. Root aggregate confinement — PRESERVED

`CoreApplicationCompositionInput`, `ApplicationCommandPorts` and their family records are allowed only as explicit composition-root records. They must:
- be constructed only at concrete composition root or explicit test fixture;
- never be retained by runtime/controller/view/store/model classes;
- be decomposed immediately into narrower records/owners;
- expose no string/name lookup or generic service retrieval;
- contain no behavior that turns them into methods-owning god objects.

A static/headless confinement gate is mandatory.

## 6. Event/callback shape preservation — NEW HARD ARCHITECTURAL RULE

Removing an App facade must not erase the payload contract of the event it adapted.

For every changed event-bearing or signal-bearing port:

`event payload -> shape-compatible adapter -> narrower owner operation`

Rules:
- the callable bound to an event port must be invocable with the exact event payload shape;
- a zero-argument owner operation cannot be bound directly to a one-argument event port merely because the payload is semantically unused;
- deliberate payload discard must occur in an explicit adapter whose signature accepts that payload;
- bound-method `self`, `functools.partial`, lambdas and optional parameters must be accounted for when checking compatibility;
- a newly introduced `*args`/catch-all adapter is forbidden as a way to make the gate pass;
- do not widen `refresh_ui_state` or another narrow owner API simply to absorb irrelevant event payloads;
- do not remove the event payload from `NavigatorPanelRuntime` or equivalent owner contracts merely to match a narrower callback;
- do not reintroduce a whole-App facade to restore callback shape.

The known Navigator regression is the seed example, not a special-case definition of this rule.

## 7. Dynamic lookup clarification — PRESERVED

Forbidden: `getattr`/string lookup used for command dispatch, dependency/service resolution or whole-App authority discovery.

Not W108 cleanup scope: ordinary typed-object/GTK capability inspection unrelated to dynamic DI/dispatch.

## 8. Structural budget — PRESERVED

From W107 baseline:
- `App` lines `<2355`;
- App method definitions `<296`;
- no LOC/code-shift cheating through renamed whole-App host modules.

The 24 W101 compatibility attributes remain. Obsolete forwarding methods may be removed only when narrow direct ownership replaces them without erasing event semantics.

## 9. Exclusive validation-lane ownership — AMENDED

Every completion fact has one primary authority lane.

### Source/static lane owns
- 39-seam inventory and semantic whole-App seam zero;
- absence of renamed App-equivalent host/context/service bag;
- App LOC/method budget and Character Map source extraction;
- no post-W108 delta work;
- root-aggregate confinement and dynamic-dispatch prohibition;
- declaration-level callback/event shape inventory and compatibility analysis;
- changed-binding inventory against the W107 published baseline.

### Headless executable lane owns
- exact typed composition behavior/order;
- exact W101 24 aliases/ledger interpretation;
- exact W104 stable IDs and 117 binding completeness;
- command dispatch to explicit owners/callables;
- executable callback-shape probes where static analysis is indeterminate;
- exact adapter behavior for intentionally discarded payloads;
- W102–W107 non-GTK authority behavior.

### Current W108 true-App/GTK lane owns
- stable public command/event -> live owner -> observable product effect;
- behavioral receipts for each W108-changed event-bearing binding that requires GTK/live-widget proof;
- specifically `navigate.navigator-panel` visible/hidden traversal through the real changed Navigator path;
- Character Map insert + Undo;
- clean DnD success;
- dirty DnD + deterministic Cancel + lossless fail-closed receipt;
- W108-changed panel/menu/presentation wiring;
- clean public `file.quit` after public `file.save` in the automatic lane;
- process shutdown and real-config invariance.

One representative command per W104 family may remain useful smoke coverage, but **does not satisfy changed-binding coverage** for a different command in that family.

Historical W107→W98 true-App lanes remain under their published authorities except exact physical facades W108 must remove.

## 10. Oracle Inventory Closure — PRESERVED / PRE-PACKAGING

Before Candidate sealing, inventory every W108-affected real-GTK/true-App assertion/call executed by the T480 runner and classify it as `STATIC`, `HEADLESS`, `BEHAVIORAL-GTK` or `HISTORICAL-FROZEN`.

PASS requires:
- 100% inventory closure;
- no stale App forwarding calls;
- no current-W108 structural oracle leakage;
- no replacement leak through private composition topology;
- a source/headless receipt for every structural fact removed from GTK;
- narrow allowlist only for legitimate historical architecture tests.

Candidate packaging is forbidden unless PASS.

## 11. Modal Transition Closure — PRESERVED / PRE-PACKAGING

Every modal-capable operation in the current W108 automatic GTK sequence must freeze:
- precondition state;
- whether a modal is expected;
- deterministic driver when expected;
- terminal behavioral receipt;
- owning authority.

Frozen current receipts:
1. About -> driven Close;
2. Character Map -> driven Ω insertion + Close -> Undo restores exact bytes;
3. System Info -> driven Close;
4. public `file.save` -> clean DnD -> no modal -> success;
5. deliberate public edit -> dirty DnD -> Save changes? -> driven Cancel -> failed drag + exact identity/content preservation;
6. public `file.save` -> public `file.quit` -> no modal expected in automatic lane.

Direct `DocumentSession.mark_clean`, `window.may_continue = ...` or equivalent bypasses are forbidden in current W108 true-App.

The automatic lane must not require operator intervention.

## 12. Callback Shape Closure — NEW PRE-PACKAGING BARRIER

Before Candidate sealing, machine-check all typed composition mappings and all W108-changed signal/event bindings on the exact package source tree.

PASS requires:
1. every determinable callback binding accepts the required positional payload arity after accounting for bound methods/partials/defaults;
2. every deliberate payload discard is explicit in a shape-compatible adapter;
3. no newly introduced variadic/catch-all adapter used solely to evade shape checking;
4. indeterminate changed callable shapes are classified and exercised by a headless sentinel-payload probe;
5. every mismatch is zero before package creation;
6. scanner scope cannot silently shrink: all mappings/bindings from the audited seed set must be present or explicitly classified as contract-authorized removal/replacement.

Failed post-audit R2 seed evidence:
- direct typed mappings inspected: 106;
- determinable mismatch count: 1;
- mismatch: zero-arg `CoreApplicationCompositionInput.refresh_ui_state` bound to one-bool `NavigatorCompositionInput.on_visibility_changed`.

The number 106 is evidence for scanner-scope continuity, not a permanent target count: legitimate future removals/replacements must be explicitly classified rather than silently dropped.

## 13. Changed-Binding Coverage Closure — NEW PRE-PACKAGING BARRIER

Generate an exact W107-baseline -> package-source inventory of every callback/signal/action binding whose physical wiring changes under W108.

For every entry record:
- baseline source symbol/path;
- package source symbol/path;
- event/command payload shape;
- live owner reached;
- whether an adapter discards/transforms payload;
- primary authority lane;
- exact focused/historical/GTK behavioral receipt.

PASS requires:
- 100% entries classified;
- no changed event-bearing binding covered merely by a sibling command from the same W104 family;
- every GTK-dependent changed event path traversed by its exact public command/event unless a frozen historical authority already traverses the same path;
- headless receipts may own non-GTK direct-owner rewiring;
- no duplicate competing authority for the same fact.

Mandatory known receipt:
- `navigate.navigator-panel` must be exercised through the stable command/public behavior and must show/hide the real Navigator panel without exception;
- historical W101 `NavigatorPanelRuntime.set_visible(True)` remains mandatory and unweakened because it detects the owner-level visibility callback contract.

These two receipts are complementary: current W108 proves the public path; W101 preserves the historical owner/composition behavior.

## 14. True-App oracle hygiene — AMENDED

Current W108 GTK must not:
- parse architecture documents/ledgers;
- inspect AST/source/LOC;
- count 24 aliases or 117 bindings;
- assert composition-complete topology as GTK proof;
- inspect `_components`, `_w107_subsystems`, `_research_components` merely to prove structure;
- iterate removed forwarding names with `hasattr`;
- call private host/runtime paths when a stable command/natural event exists;
- directly alter clean/dirty state or bypass unsaved gates;
- substitute a sibling command as proof of a different changed binding.

A W108-amended historical test may access a narrow owner only where the historical work item itself certifies that owner and the exception is frozen in the supersession matrix.

## 15. Historical supersession — AMENDED

W108 may modify a historical test only where a physical facade W108 is explicitly authorized to remove. Behavioral authority must remain equal or stronger.

Frozen exact cases:
- W88 Authoring Bridge removed App forwarding methods -> stable W104 Research commands;
- W105 Recent Workspaces removed App facade -> real Workspace open-root/recent-change path, never `_components.workspace.host_runtime` as replacement;
- W101 Navigator visibility test -> **NOT superseded**; it is authoritative and caught a real W108 regression.

No wholesale rewrite of W107→W98 architecture tests is authorized.

## 16. Savepoint/Undo debt boundary — NEW EXPLICIT OUT-OF-SCOPE AUTHORITY

Emacs/Vim re-audit demonstrates that savepoint-aware dirty restoration across Undo is a legitimate editor design. Current Calamus W102/W103 marks restored Undo state modified even when text returns to saved bytes.

This is recorded debt, not W108 scope.

Therefore W108 must:
- preserve current W102/W103 semantics;
- establish clean state through public `file.save` before clean-DnD testing;
- test dirty-DnD Cancel separately;
- never add private dirty overrides or redefine Undo/savepoint semantics inside W108.

No future W108 Candidate may silently absorb this debt as a product change.

## 17. Desktop validation and lifecycle — AMENDED

Automatic true-App W108 closes **cleanly** after public save and public quit. This avoids an unnecessary unpiloted modal in the automatic lane.

Manual desktop validation may separately exercise dirty Quit -> Discard as an observable user receipt. Historical W99/W102 lifecycle/unsaved authorities remain mandatory.

Real `~/.config/calamus` must remain byte/semantic unchanged and no residual process may remain after normal close.

## 18. Out of scope

- product features / Full variants;
- menu/shortcut redesign or new keybinding system;
- general `:prelight`, `override_font`, import/style/dead-code cleanup;
- removing 24 W101 compatibility attributes;
- W102/W103 savepoint-aware Undo redesign;
- post-W108 audit/contract/implementation/scheduling;
- W104 command catalog/ID redesign;
- architecture-wide rewrite of historical tests.

## 19. Completion gates — SECOND RE-FREEZE

W108 may close only if all are PASS:

1. identity exactly W108 / Thin GTK Shell, baseline `e16cc21b8a900298406ae8cc4776f6f1ec658e93`;
2. delta contains no post-W108 work;
3. exact 39 baseline whole-App seams closed and semantic whole-App seam count zero;
4. no renamed App-equivalent host/context/service bag/generic command host;
5. typed App-free composition; builders App-free; no builder imports another builder;
6. exact 24 W101 aliases/ledger preserved and alias-before-Workspace-startup order exact;
7. `_components` final assignment single/complete; initial Recent Workspaces projection only afterward;
8. W101 ownership/build topology/named SetOnce cycles preserved;
9. command builder App-free; exact W104 stable IDs and 117 bindings preserved;
10. no dynamic/string lookup for command dispatch, service/dependency resolution or whole-App discovery;
11. root aggregate confinement PASS;
12. **event/callback shape architectural rule PASS; no payload erasure through direct incompatible binding**;
13. menu/shortcut assembly narrow; W105 sole menu-state projector; Line Numbers remains without Ctrl+Alt+L;
14. authorized historical whole-App gateways retired/narrowed;
15. Character Map outside App and insert/Undo/modal behavioral equivalence;
16. clean DnD success and dirty DnD + deterministic Cancel lossless fail-closed receipts both exact;
17. all other original W108-assigned user behavior equivalent, including focus/fullscreen/current-line/bookmark/wrap/scroll;
18. W102–W107 authorities and GTK-free boundaries exact;
19. W99 lifecycle inventory/cancellation/idempotence/normal close exact;
20. App lines `<2355`, methods `<296`, no code-shift/renamed-host cheating;
21. W108 focused + historical W107→W98 headless PASS, zero unexpected skips;
22. **Oracle Inventory Closure PASS on exact package source before Candidate sealing**;
23. **Modal Transition Closure PASS on exact package source before Candidate sealing**;
24. **Callback Shape Closure PASS on exact package source before Candidate sealing**;
25. **Changed-Binding Coverage Closure PASS on exact package source before Candidate sealing**;
26. headless-core, full discovery, filesystem, Pandoc real, GIO real, provenance, GTK-boundary, Python compile, Bash syntax PASS;
27. current W108 true-App/GTK uses behavioral receipts only and includes exact `navigate.navigator-panel` show/hide traversal;
28. current W108 automatic lane contains no private dirty/may-continue bypass and ends with public save -> public quit;
29. historical W107→W98 true-App lanes PASS with only frozen supersession cases;
30. historical W101 Navigator visibility receipt PASS unchanged;
31. W105 Recent Workspaces proves real re-projection through Workspace behavior with no new private `_components` access;
32. callback-shape scan/probes report zero mismatches/unknown-unclassified changed bindings;
33. changed-binding inventory is 100% classified and every changed event-bearing binding has an exact receipt;
34. real config unchanged and no residual process;
35. manual desktop validation PASS in synchronous small batches, including any dirty-close/Discard receipt assigned to manual validation;
36. exact reconstruction from published W107 baseline + W108 patch reproduces source bytes and executable modes;
37. package authority records all four failed Candidates as retired valid failures and does not use them as reconstruction/patch bases;
38. known W102/W103 savepoint debt remains unchanged by W108 and is recorded, not hidden;
39. post-W108 roadmap remains HOLD with no post-W108 implementation introduced.

## 20. Attempt/reset rule after the second mandatory STOP

This re-freeze does not authorize implementation.

If the user later authorizes implementation:
- start from published W107 `e16cc21...` in a fresh isolated tree;
- failed Candidate artifacts are evidence only, never patch/reconstruction bases;
- audit-approved production design may be re-derived/reapplied where conforming;
- known Navigator callback-shape regression must be repaired by a shape-compatible event adapter, not by weakening owner/event contracts;
- Oracle, Modal, Callback Shape and Changed-Binding Coverage closures must all PASS before the first new Candidate is sealed;
- no Candidate attempt is consumed before sealing and T480 validation;
- the new attempt cycle follows the normal two-valid-FAIL rule, with classification before any retry.

## 21. Post-W108 roadmap hold

No W109/W110/W111 or replacement roadmap work is authorized inside W108. The user will reopen post-W108 roadmap review only after W108 is CLOSED/CERTIFIED/PUBLISHED.
