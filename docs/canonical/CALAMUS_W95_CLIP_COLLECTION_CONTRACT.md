# Calamus W95 — Clip Collection Completion Contract

**Published baseline:** `541804f8ff361b3afacb58f18e1e429c70b3a2f9`
**Candidate identity:** W95
**Authority:** global UTF-8 Markdown `clips.md`
**Status:** implemented in rebuilt Candidate R3; desktop certification pending

## Scope adopted

W95 completes the existing Clip Collection as a small keyboard-first library of reusable text. It does not create a second Scratchpad, clipboard manager, taxonomy, database, watcher, cloud service or automatic expansion daemon.

The adopted scope is:

1. Markdown authority v2 with stable IDs, timestamps and optional mnemonic shortcut;
2. v1 Markdown and legacy JSON migration, with JSON retained read-only;
3. list/detail client with shortcut, title and body preview;
4. deterministic search over shortcut, title and body;
5. New, Capture Selection, Edit, Duplicate and Delete with explicit dialogs;
6. Insert, Copy Body, Refresh and Open Clip File;
7. `Research → Insert Clip…` with application shortcut `Ctrl+Alt+K`;
8. the quick selector doubles as the complete list of mnemonic shortcuts;
9. one optional `{{cursor}}` marker for the caret position after insertion;
10. backward-compatible numeric quick slots `Ctrl+Alt+1…9` based on canonical file order;
11. stale detection, persist-first state changes and atomic replacement;
12. complete User Guide and Keyboard Shortcuts documentation.

Fillable parameters such as `{{name}}` are not part of W95. They remain deferred. W93 Scratchpad Full remains frozen until Calamus is complete and the user gives a separate explicit authorization.

## Candidate history

- Candidate R1 passed its complete source self-test on the T480 but the validation runner stopped before exercising the product in the True GTK/App phase. The gate attempted to load the extensionless production launcher `bin/calamus` with `importlib.util.spec_from_file_location`, which returned no loader. R1 is retired as a validation-harness failure; it established no desktop product PASS or FAIL.
- Candidate R2 was rebuilt from the published baseline and repaired extensionless launcher loading with `SourceFileLoader`. It reached the real production App and New Clip dialog, but its validation gate addressed Title and Shortcut by incidental `Gtk.Entry` traversal order. GTK returned the reverse order, the gate supplied an invalid shortcut, and the production dialog correctly blocked it. R2 is retired as a second validation-harness failure; manual validation was not started.
- Candidate R3 is rebuilt from the same published baseline. Editor fields expose stable semantic widget names and the gate requires exact type/name matches, with a headless regression forbidding positional field lookup. Product scope and user-visible behavior are unchanged.

## Mnemonic shortcut contract

A clip has zero or one mnemonic shortcut. It is not a tag and does not classify the clip.

- length: 1–32 characters;
- allowed characters: lowercase ASCII letters, digits, `-`, `_`;
- first character: letter or digit;
- uniqueness: global, case-insensitive;
- stable ID remains the technical identity;
- Duplicate creates a new ID and an empty shortcut.

## Markdown v2 record

````text
# Calamus Clip Collection v2

## Signature

ID: clip-0123456789abcdef0123456789abcdef
Shortcut: firma
Created: 2026-07-29T20:00:00+02:00
Updated: 2026-07-29T20:00:00+02:00

```text
Cordiali saluti,

{{cursor}}
```
````

Unknown `Key: Value` metadata is retained. Dynamic backtick fences prevent bodies containing Markdown fences from corrupting the authority. The maximum remains 200 records and is enforced without silent truncation.

## Search order

For a non-empty query results are ordered by:

1. exact shortcut;
2. shortcut prefix;
3. title prefix;
4. shortcut substring;
5. title substring;
6. body substring;
7. stable alphabetical tie-break.

For an empty query, clips with shortcuts are listed first in shortcut order, followed by clips without shortcuts in title order. This is a view order only and never rewrites the authority.

## UI contract

The Research Panel client contains:

- Search;
- result count;
- single-selection list;
- read-only body detail;
- full-width New, Capture Selection, Insert and Copy Body actions;
- Manage menu with Edit, Duplicate, Delete, Refresh and Open Clip File.

Enter on an activated row and double-click insert the selected body. Destructive operations require confirmation. Capture Selection refuses empty selections and opens a reviewable draft before persistence. No control may restore the W94 panel-width regression.

The quick selector opened by `Ctrl+Alt+K` provides Search, shortcut/title/body rows, Up/Down navigation, Enter or double-click activation and Esc cancellation. Typing an exact shortcut alone never mutates the document.

## Document mutation contract

Insertion:

- re-reads the authority before use;
- selects by stable ID;
- removes at most one `{{cursor}}` marker;
- inserts through Calamus’s production command gateway;
- creates one coherent Undo step;
- places the caret at the marker, or at the end when absent;
- does not rewrite `clips.md`.

## Persistence and failure semantics

Every authority mutation follows:

1. validated immutable candidate state;
2. expected SHA-256 revision token;
3. temporary file in the authority directory;
4. UTF-8 write, flush and `fsync`;
5. second revision check;
6. atomic `os.replace`;
7. runtime state update only after disk success.

Malformed Markdown, duplicate/malformed IDs, shortcut collision, over-limit collections, failed migration, failed write or external modification fail closed. The previous authority and active document remain unchanged. No implicit merge or overwrite is permitted.

## Architecture

GTK-free:

- `calamus_clips.py`
- `calamus_clip_search.py`
- `calamus_clip_expansion.py`
- `calamus_clip_collection.py`

GTK/application boundary:

- `calamus_clip_panel.py`
- `calamus_clip_dialogs.py`
- `calamus_clip_runtime.py`
- `bin/calamus` wiring only

## Required gates

Headless gates cover parsing, migration, stable identity, shortcut validation, search ordering, dynamic fences, duplicate handling, stale conflict, atomic failure, 200-record limit, `{{cursor}}`, controller selection and document-command gateway wiring.

Desktop gates must cover the real App, real Gtk.ListBox, real dialogs, `Ctrl+Alt+K`, Enter, double-click, Undo, clipboard copy, Open Clip File, external modification, resize/hide/show/client switching, Help, normal close and absence of residual processes.

No commit or push is authorized until all desktop gates pass.


## R4 desktop repair addendum

The final W95 candidate must explicitly place the GtkTextBuffer insertion mark after expanding `{{cursor}}`; a collapsed selection is not accepted as a portable caret gateway. Undo/Redo restoration must defer a scroll-to-insert request until after GtkTextView relayout. The Research client selector must use a downward `Gtk.MenuButton`/`Gtk.Popover` list beginning with the first registered client, not a `GtkComboBoxText` popup aligned around the active row.
