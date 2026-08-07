# W102 Test Migration and Gate Plan

## A. GTK-free session tests

- initial untitled clean session;
- restored path without implicit read;
- immutable snapshots and revision;
- nested guard unwinds after exceptions;
- normal change marks modified and synchronizes text;
- guarded change does not mark modified;
- New replacement failure preserves prior snapshot;
- Open read/replacement failure preserves prior snapshot;
- successful Open commits path/text/clean;
- untitled Save requests destination without mutation;
- Save As cancellation performs no mutation;
- write failure preserves path/modified;
- Save As path commits only after write success;
- trailing-space normalization success and failure preserve historical behavior;
- rename rebinds affected active identity only;
- trash detaches affected active identity and marks modified;
- failed save/cancel blocks close readiness.

## B. Static architecture gates

- session modules import no GTK;
- domain imports no composition module;
- no App assignments to current_file/modified/loading;
- no Document path/modified writes outside session;
- no Workspace lambda over app.current_file;
- typed frozen session inputs/components;
- explicit build order;
- no new settings key;
- no tabs/global document registry/WebKit/cloud/AI/database.

## C. Test migration

Replace mutable App fixtures with a real DocumentSession or typed session stub.
Retain and strengthen model, lifecycle-plan, quit, Workspace identity, and
true-App tests.

## D. Release gates

Zero-skip explicit profiles:
- W102 GTK-free focused;
- W102 true-App identity;
- W102 true-App document session;
- W101 composition;
- W100 contract;
- W99 lifecycle;
- W98 Research.

Full discovery remains mandatory.

## E. Hostile injection

Inject chooser cancellation, read/decode failure, buffer replacement failure,
undo reset failure, write failure, store/settings failure, invalidation failure,
and title refresh failure. Distinguish committed session transition from
post-commit presentation errors.

## F. Desktop validation

Isolated HOME; startup restore; New; Open; edit/dirty; Save; Save As; cancelled
Save As; close cancel/save; active Workspace rename/trash; normal exit; no
residual process; real config unchanged.

Desktop authority: cryptographic Candidate/launcher identity plus `EXIT=0`,
`ERR=NONE`, `FINAL_PHASE=RUNNER_RETURNED_PASS`.

## G. Historical true-App fixture authority gate

All real-App fixtures must mutate document state through `DocumentSession`.
Assignments to App projections `modified`, `current_file`, `loading`, or
`document` are forbidden and enforced by AST. This barrier was added after
Candidate R1 FAIL 1/2 in the historical W98 product-smoke lane.
