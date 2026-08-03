# Calamus architectural roadmap after W99

Status: **binding from W100 onward**
Published baseline: `9a80b266cbdb41b499efdb296ff2a312cf85656f`

This roadmap supersedes every earlier prospective sequence for W100 and later.
Historical documents remain historical evidence and are not rewritten.

1. **W100 — Monolith Decomposition Contract**
2. **W101 — Application Composition Root Extraction**
3. **W102 — Document Session Extraction**
4. **W103 — Editor Transaction Extraction**
5. **W104 — Command and Action Architecture**
6. **W105 — Menu and UI-State Decoupling**
7. **W106 — Preferences and Application State Extraction**
8. **W107 — Subsystem Host-Port Migration**
9. **W108 — Thin GTK Shell**
10. **W109 — Monolith Closure Gate**
11. **W110 — Source Code Cleanup**
12. **W111 — Product Roadmap Rebaseline**

## Serial rule

No work item may begin before the preceding item is CLOSED/CERTIFIED/PUBLISHED.
W111 is the first point at which Navigator, Search, Markdown Preview, missing
commands or deferred Full variants may be newly scheduled.

## Architectural end state

- a thin concrete GTK shell;
- one explicit composition boundary;
- document/session and editor transaction authorities outside the window;
- stable command IDs and narrow action bindings;
- menu state projected from explicit authorities;
- no runtime/controller receives the entire `App` object;
- no generic service locator, global event bus, plugin framework or dynamic DI container;
- every asynchronous source has a lifecycle owner;
- source cleanup only after the monolith closure gate.
