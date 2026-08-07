# W102 Mature Source Comparison

## Method

The comparison was performed directly on uploaded source archives. The audit
uses classes and functions actually read, not README summaries or web pages.

## 1. GNOME Text Editor

Files inspected:
- `src/editor-document.c`;
- `src/editor-document.h`;
- `src/editor-session.c`;
- `src/editor-session.h`.

`EditorDocument` owns the buffer-facing document state, file, loading flag,
external-modification state, save/load completion, and modified behavior.
`editor_document_changed()` suppresses normal dirty/autosave handling while
loading. `editor_document_new_for_file()` binds file identity to the document.
`EditorSession` owns document/page creation and opening.

Decision:
- ADAPT one document/session authority;
- ADAPT explicit loading state and completion-driven transitions;
- REJECT tabs, drafts, autosave, asynchronous complexity for W102;
- DEFER external modification monitoring.

## 2. gedit

Files inspected:
- `gedit-document.c/.h`;
- `gedit-tab.c/.h`;
- `gedit-commands-file.c`.

`GeditDocument` owns location and document signals. `GeditTab` exposes explicit
operational states including loading, saving, closing, and error states.
The file-command layer retains dialogs and coordinates save-before-close.

Decision:
- ADAPT explicit transition state;
- ADAPT close only after successful save;
- ADAPT UI prompt outside the document core;
- REJECT full tab/multi-document state machine.

## 3. Pluma

Files inspected:
- `pluma-document.c/.h`;
- `pluma-tab.c/.h`;
- `pluma-commands-file.c`.

Pluma confirms the gedit lineage: document identity belongs to the document,
operational state belongs to the tab/session layer, and UI commands own
interactive prompts.

Decision:
- use as independent cross-check;
- ADAPT the same ownership split;
- REJECT tab architecture.

## 4. NotepadNext

Files inspected:
- `src/ScintillaNext.cpp/.h`;
- `src/EditorManager.cpp/.h`;
- `src/dialogs/MainWindow.cpp`.

`ScintillaNext` owns file information, save/reload/Save As, savepoint, and
rename/saved signals. File identity and clean state are updated only after
successful persistence. `EditorManager` owns editor creation and lookup.
`MainWindow` owns user-facing prompts and delegates to editor/session behavior.

Decision:
- ADAPT identity commit after successful write;
- ADAPT UI prompt outside session;
- ADAPT manager-owned lifecycle;
- REJECT Qt/Scintilla and multi-tab details.

## 5. Geany

Files inspected:
- `src/document.c`;
- `src/document.h`;
- `src/documentprivate.h`.

`GeanyDocument` co-locates file name, canonical real path, changed state,
read-only state, and editor association. `document_set_text_changed()`
centralizes dirty-state transition and associated UI updates.
`real_path` is established after a successful open/save path resolution.

Decision:
- ADAPT centralized dirty transition;
- ADAPT successful-open/save identity commit;
- REJECT global document array, global ambient state, and C data-bag coupling.

## 6. Kate

Files inspected:
- `apps/lib/katedocmanager.cpp/.h`;
- `apps/lib/kateapp.cpp`.

`KateDocManager` owns document creation/opening, URL deduplication, the document
list, modified-document close handling, and close success. `KateApp` delegates
document closure to the manager before application shutdown.

Decision:
- ADAPT session/manager ownership;
- ADAPT document close success as prerequisite for application close;
- REJECT multi-window/session persistence complexity.

## 7. Airpad

Files inspected:
- `src/file.c`;
- `src/file.h`;
- `src/quit.c`.

Airpad is structurally simpler and GTK-coupled, but it contains an important
failure invariant. During Open and Save As it retains previous file and encoding
state and restores them when the operation fails. Buffer modified signals are
blocked during bulk replacement.

Decision:
- ADAPT rollback of prior identity after failed Open/Save As;
- ADAPT guarded signal suppression;
- REJECT global data bags and direct GTK ownership.

## 8. Micro

Files inspected:
- `internal/buffer/buffer.go`;
- `internal/buffer/save.go`.

Micro's Buffer co-locates path, content, undo, settings, modification time, and
shared-view state. It demonstrates why buffer identity should be cohesive, but
also why W102 must avoid turning the session into an oversized universal object.
The global `OpenBuffers` registry is unsuitable for single-document Calamus.

Decision:
- ADAPT cohesive identity only;
- REJECT global registry and giant-buffer responsibility.

## 9. Neovim

Files inspected:
- `src/nvim/buffer_defs.h`;
- `src/nvim/globals.h`.

Neovim is used as a negative control. Its mature but process-global
current-buffer/current-window architecture is appropriate to its historical C
editor core, not to Calamus' desired explicit typed composition.

Decision:
- REJECT ambient global current-document authority.

## 10. Convergent mature-source rule

Across GNOME Text Editor, gedit, Pluma, NotepadNext, Geany, Kate, and even
Airpad, the same stable rule appears:

1. document identity and dirty state belong to one document/session owner;
2. open/save identity changes occur only after the relevant operation succeeds;
3. loading or replacement suppresses ordinary edit handling;
4. UI prompts stay at the window/command adapter;
5. application shutdown waits for document-close success;
6. multi-document, autosave, monitoring, and recovery are separable concerns.

W102 should ADAPT this rule to a single-document, synchronous, GTK3, plain-text
Calamus implementation.
