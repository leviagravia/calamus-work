# Calamus W96 — Document Overview Core Gate B contract

## Scope

Gate B projects the immutable Gate A dossier into one non-modal,
single-instance GTK window opened through `Navigate → Document Overview`.

Categories are exactly:

1. Overview
2. Structure
3. Research
4. Integrity
5. Statistics

## Ownership

- `calamus_document_dossier_app.py` loads existing authorities without GTK.
- `calamus_document_overview_runtime.py` owns selection, refresh and semantic
  routing without importing GTK.
- `calamus_document_overview_view.py` owns widgets and emits semantic signals.
- `bin/calamus` remains the composition root.

The window has no store, database, watcher, timer, polling loop, second editor,
AI/NLP path or hidden index.

## Refresh

Refresh occurs on open, explicit Refresh, Save/Save As, document replacement
and Calamus-controlled rename/detach. Buffer edits mark the projection stale
without continuously rebuilding it.

## Actions

Gate B permits navigation and opening existing Research surfaces only:
section/bookmark/link/citation navigation, Show Reference, Open Source Note,
Open Reference Set and Run Research Check. No mutation policy is duplicated.

## Lifecycle

Close destroys the auxiliary window and returns focus to the editor. Reopen
creates a fresh instance and snapshot. App shutdown destroys the window before
terminating the GTK main loop.


Gate C hardening is frozen in `CALAMUS_W96_DOCUMENT_OVERVIEW_GATE_C_CONTRACT.md`.
