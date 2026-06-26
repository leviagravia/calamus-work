# Calamus W13 — Status-bar Word Count Canonicalization

Status: implemented  
Risk: low  
Runtime behaviour change: status-bar word-count semantics only

## Problem

After W11 desktop validation, Document Statistics and the status bar disagreed:

```text
Document Statistics dialog: Words 41
Status bar:                 words 34
Chars:                      250 in both visual paths
Lines:                      7 in both visual paths
```

W12 showed that the numbered-list sample counts as 41 words under `document_statistics`, while an alpha-only count gives 34.

## Decision

Use `calamus_writing.document_statistics(text)["words"]` as the canonical displayed word-count source.

## Change

`App.text_stats()` now uses `document_statistics(text)["words"]` for words, while preserving `calc_text_stats(text)` for chars and lines.

## Non-goals

W13 does not change CommandLayer dispatch surface, add dispatches, wire text transforms, touch open/save, undo/redo, dirty state, session lifecycle, Gtk.TextBuffer lifecycle, or UI layout.

## Acceptance

```text
source provenance PASS
targeted W13 tests PASS
full source selftest PASS
exactly one dispatch in bin/calamus
dispatch target remains writing.statistics
no text-transform command ids wired in bin/calamus
installed Calamus unchanged
```
