# Calamus W96 — Document Overview Core Gate C contract

## Status

Gate C freezes the final Core behavior before the unitary desktop candidate.
The published baseline remains
`792ca0f76db39525a9052bd61e43fe929988af2e`.

## Fail-closed action rule

Every primary or secondary action must:

1. re-read the current authority stamp;
2. compare it with the displayed snapshot;
3. re-resolve the selected semantic row in the current snapshot;
4. dispatch only when both checks pass.

A changed buffer, document token, Source Notes token, References token or
Reference Sets token causes an immediate refresh, selection clearing and a
notice requiring explicit reselection. No stale action is dispatched.

## Core action boundary

Allowed delegates:

- section/bookmark/link/citation navigation;
- Show Reference;
- Open Source Note;
- Open Reference Set;
- Run Research Check.

Document Overview owns none of those policies and performs no direct mutation.

## Hostile requirements

- removed/renamed headings, links and citations fail closed;
- externally changed or removed Source Notes, References and Reference Sets
  fail closed;
- malformed and empty authorities remain readable and byte-identical;
- untitled documents degrade without a sidecar;
- long documents use deterministic iterative projections;
- repeated open/refresh/close and App shutdown release the window, selection,
  row projection and snapshot;
- no watcher, timer, polling source, database, graph, AI/NLP or hidden index.

## Desktop acceptance

The final candidate must prove on the real App:

- exact Navigate menu wiring;
- non-modal single instance;
- five categories and real details/actions;
- current navigation;
- stale-action block, automatic refresh and reselection requirement;
- close/reopen and normal App shutdown;
- no document or authority mutation merely by browsing;
- no residual Calamus process.
