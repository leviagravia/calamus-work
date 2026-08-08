# W108 Callback Shape Closure — frozen pre-packaging gate

## Purpose
Prevent loss of event semantics when W108 replaces whole-App facade callbacks with narrow typed composition ports.

The post-audit R2 failure proves that type/naming narrowness is insufficient if callback arity is silently changed.

## Scope
On the exact source tree to be packaged, inspect:
1. every typed composition input/port callable mapping;
2. every signal/event binding physically changed from the published W107 baseline;
3. every new lambda/partial/adapter introduced by W108 at those boundaries.

## Compatibility rule
For an event that supplies N required positional values, the bound callable must accept those N values under ordinary Python call semantics after accounting for bound `self`, partial application and defaults.

A narrow downstream operation with fewer parameters requires an explicit shape-matching adapter.

## Static determinable cases
The scanner must understand at least:
- plain functions;
- bound methods;
- lambdas;
- `functools.partial` with statically resolvable pre-bound arguments;
- dataclass `Callable[...]` field annotations;
- optional/default positional parameters.

## Indeterminate cases
If exact compatibility cannot be established statically for a W108-changed binding, the entry is not automatically PASS. It must have:
- explicit classification in the callback inventory; and
- an executable headless sentinel-payload probe proving the callback accepts the event payload and invokes the intended narrow owner behavior.

## Forbidden gate evasion
- newly adding `*args`/`**kwargs` merely to absorb event payloads;
- widening a downstream owner method signature for irrelevant event context;
- removing payload from the event owner to match a narrower callback;
- reintroducing whole-App facade;
- excluding an offending mapping from scanner scope without contract-authorized classification.

## Seed evidence from failed post-audit R2
Audited scan:
- 106 direct typed composition mappings inspected;
- 1 determinable mismatch;
- `CoreApplicationCompositionInput.refresh_ui_state` accepts zero required positional args;
- `NavigatorCompositionInput.on_visibility_changed` requires one `bool` payload.

The future scanner may report a different total only if every seed mapping removed/replaced is explicitly classified. Silent scope shrink is FAIL.

## PASS receipt
- zero determinable mismatches;
- zero unclassified indeterminate changed bindings;
- all sentinel probes PASS;
- explicit report stored in Candidate authority before package sealing.
