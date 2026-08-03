# Calamus W100 — Monolith Decomposition Contract

Runtime identity: `W100` / `Monolith Decomposition Contract`
Published baseline: `9a80b266cbdb41b499efdb296ff2a312cf85656f`

## Purpose

W100 is a contract-and-gate work item. It freezes the complete decomposition
plan before any major extraction. It must not change user-visible product
behavior or move operational responsibilities merely to reduce line count.

## Binding outputs

- exact baseline metrics;
- complete App method responsibility inventory;
- complete App assigned-attribute inventory;
- complete whole-App parameter inventory;
- mature-source ADOPT/ADAPT/REJECT decisions;
- binding W100–W111 roadmap;
- executable anti-regression tests.

## W100 prohibited changes

- no feature implementation;
- no Workspace/Research/Search/Navigator redesign;
- no document-session extraction (W102);
- no editor-transaction extraction (W103);
- no menu rewrite (W105);
- no generic service locator, event bus, plugin framework or dynamic DI container;
- no weakening of W99 lifecycle/GTK-free gates;
- no declaration that moving code to `*_app.py` alone constitutes decomposition.

## Baseline growth barriers

Until W101 supersedes these exact metrics, W100 must not increase:

- `App` lines above 3066;
- App methods above 266;
- distinct Calamus imports in the launcher above 92;
- assigned App attributes above 94;
- distinct `app.*` attributes in `calamus_ui.py` above 156;
- functions accepting a whole `app` parameter above the frozen inventory count.

## Sequential ownership

- W101 composition root;
- W102 document session;
- W103 editor transactions;
- W104 command/action surface;
- W105 menu and UI state;
- W106 preferences/application state;
- W107 subsystem host ports;
- W108 thin GTK shell;
- W109 closure certification;
- W110 semantic-preserving cleanup;
- W111 functional roadmap rebaseline.

## Acceptance

W100 is complete only when all inventories match the source exactly, no item is
unassigned, focused gates pass with zero skips, current W100 identity passes on
the real App, historical W99 lifecycle remains green and no product behavior
has changed.
