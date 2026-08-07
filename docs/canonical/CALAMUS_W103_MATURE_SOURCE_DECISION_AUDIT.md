# W103 Mature Source Comparison

Direct source files inspected from the uploaded mature corpus.

## gedit — `gedit-document.c`
Replace-all disables expensive cursor/search/bracket projections, encloses all
replacements in one `gtk_text_buffer_begin_user_action()` /
`gtk_text_buffer_end_user_action()` pair, then re-enables projection.

ADAPT: one logical edit = one Undo unit; defer expensive projections until end.

## Pluma — `pluma-document.c`
Uses the same grouped-user-action boundary for bulk replacement and keeps
low-level insert/delete callbacks separate from command semantics.

ADAPT: transaction grouping and separation of low-level buffer callbacks.

## Geany — `document.c`
Uses `sci_start_undo_action()` / `sci_end_undo_action()` for grouped
replacements. Undo/Redo then updates document changed state.

ADAPT: grouped transaction boundary; dirty state after Undo/Redo.
REJECT: metadata-undo complexity and global document structures.

## NotepadNext — `ScintillaNext.cpp`, `MainWindow.cpp`
Uses Scintilla native Undo/Redo/savepoints. During loading it disables undo
collection and blocks signals, then re-enables collection and sets savepoint.

ADAPT: explicit distinction between replacement/loading and ordinary editing.

## GNOME Text Editor — `editor-document.c`
Insert/delete follow-up behavior is short-circuited while loading. A save-path
comment explicitly protects undo-stack position from unrelated lifecycle work.

ADAPT: transaction/replacement phase must protect history invariants.

## Airpad — `file.c`
Blocks insert/delete signals during bulk file operations.

ADAPT: bounded suppression during replacement; REJECT global GTK data bags.

## Convergence
- logical multi-step edits are grouped;
- loading/replacement is not ordinary editing;
- Undo/Redo and dirty state are transaction consequences;
- expensive projections are performed after logical edit completion;
- mutation is performed through an editor/buffer boundary rather than by every
  UI handler independently.
