# W108 — Oracle Inventory Closure Gate — FROZEN / PRE-PACKAGING BLOCKER

No post-audit W108 Candidate may be sealed until this gate is PASS on the exact source tree that will be packaged.

## Required inventory

The implementation preparation must enumerate every test method loaded by:
- W108 focused/source profiles;
- W108 current identity smoke;
- W108 current true-App/GTK smoke;
- every historical W107→W98 true-App/GTK profile executed by the T480 runner;
- full discovery real-GTK tests that contain direct `App`/window calls touched by W108 supersession.

For every assertion or direct application call affected by W108, record:
- test file + test method + line/symbol;
- assertion/call classification: STATIC / HEADLESS / BEHAVIORAL-GTK / HISTORICAL-FROZEN;
- primary authority lane;
- whether W108 changes it;
- replacement behavior if superseded;
- proof that no new private composition dependency was introduced.

## Mandatory machine gate

A dedicated headless source test must fail if the current W108 GTK test, or a W108-amended historical GTK test, contains any newly forbidden pattern:
- `docs/canonical` architecture access;
- ledger parsing;
- `_components`, `_w107_subsystems`, `_research_components` access introduced by W108;
- exact `binding_ids()` cardinality checks;
- `composition_complete` structural assertion;
- removed `App` forwarding calls listed in the supersession matrix;
- a replacement call directly through private host/runtime when a public command/event path is frozen.

The scanner must use an explicit allowlist for untouched historical architecture tests so existing W107→W98 authorities are not accidentally rewritten.

## Closure criterion

PASS requires:
- 100% of W108-affected real-GTK assertions inventoried;
- zero unclassified affected assertion/call;
- zero forbidden current-W108 structural oracle;
- zero stale removed-App-facade call in the T480-executed set;
- zero new private-composition replacement leak;
- each structural fact named by the old R2 preamble has a PASS receipt in W108/W101/W104 source/headless authority.

This gate exists specifically to prevent another sequence where the T480 discovers stale oracles one exception at a time.
