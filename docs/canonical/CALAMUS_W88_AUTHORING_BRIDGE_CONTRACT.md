# Calamus W88 — Authoring Bridge and Derived Backlinks Contract Freeze

Baseline authority: `d862fbdf1f7a084fa70115bd76316f927e476021`
Approved scope: **Perimeter B**
Status: **REFROZEN AFTER WITHDRAWAL OF R0 AND R1**

W88 R0 and R1 are diagnostic history only. Both were withdrawn before desktop
validation because their true-App GTK test contract was defective. This unitary
candidate is reconstructed from the certified W87 source archive, not patched
incrementally from either withdrawn tree.

## 1. Visible scope

W88 adds three visible Research actions:

1. **Research → Authoring Bridge**
   - opens a fourth client in the canonical Research panel;
   - shows derived, on-demand relationships for References, explicit heading IDs, and broken Research links;
   - every row is navigable to its concrete source.

2. **Research → Create Source Note from Selection…**
   - requires a saved document and a non-empty editor selection;
   - captures the complete document snapshot and selection offsets before opening any modal dialog;
   - opens the existing Source Note dialog with the captured text prefilled;
   - preselects the currently selected Reference when available;
   - preselects the owning heading only when it has one explicit, unique Pandoc-compatible ID;
   - persists only through the canonical Source Note controller and atomic Markdown sidecar store.

3. **Research → Insert Link to Heading…**
   - captures the complete document snapshot and replacement range before opening the dialog;
   - offers only explicit, unique heading IDs derived from that same snapshot;
   - inserts or replaces the captured range with `[label](#heading-id)`;
   - rejects multiline/empty labels and invalid or stale targets;
   - mutates the editor only through `App.execute_command()` as one Undo unit.

## 2. Authorities and ownership

No new authority is introduced.

- active document text: canonical editor buffer / document file;
- References: `references.md` through `MarkdownReferenceStore`;
- Source Notes: `<document>.source-notes.md` through `MarkdownSourceNoteStore`;
- heading structure: transient `DocumentStructure` derived from an immutable editor snapshot;
- Authoring Bridge results: immutable transient projection rebuilt on demand.

The Authoring Bridge never writes a cache, count, index, graph, database, JSON
file, or new sidecar.

## 3. Required architecture

- pure model/planner module:
  - immutable `EditorSelectionSnapshot` owning document text and exact offsets;
  - citation occurrences by canonical Reference;
  - Source Notes by Reference;
  - internal Markdown links and Source Notes by explicit heading ID;
  - broken citation keys, broken heading links, and broken Source Note links;
  - exact offsets, one-based lines, context excerpts, stable occurrence identities;
  - heading-link insertion plan;
- GTK-free controller:
  - owns mode/subject selection and one projection snapshot;
  - receives selected result identity directly from the view;
  - dispatches navigation without rescanning the GTK model;
- GTK view:
  - compact mode selector, subject selector, explicit Refresh, count/status, single result list;
  - row activation equals Open;
- GTK dialogs:
  - each semantically important field has a stable widget name;
  - tests address `source-note-text`, `source-note-reference`, `source-note-target`, `heading-link-target`, `heading-link-label`, and `heading-link-preview` directly;
  - no test or runtime logic may infer semantics from child order or “first widget of type”;
- runtime:
  - captures selection before modal focus changes;
  - derives the exact structure from the captured document text;
  - coordinates typed snapshots, dialogs, plans and callbacks;
  - does not mutate files directly;
- `App`:
  - composition and thin gateway methods only.

## 4. Projection modes

### References
For one canonical Reference key:

- Pandoc citation occurrences in the current document;
- Source Notes linked to that Reference, including aliases resolved to the canonical key.

### Headings
For one explicit, unique `{#heading-id}`:

- Markdown links in the current document targeting `#heading-id`;
- Source Notes whose `Target` is `#heading-id`.

### Broken Links
Navigable problems derived on demand:

- citation key missing or ambiguous in References;
- Markdown heading link missing or ambiguous in the current structure;
- Source Note Reference missing or ambiguous;
- Source Note Target missing or ambiguous;
- malformed, multiple, or duplicate heading-ID diagnostics already emitted by `DocumentStructure`.

## 5. Navigation rules

- document occurrence: select the exact stored range and reveal it;
- Source Note occurrence/issue: open Source Notes and select the known stable note ID;
- heading diagnostic: navigate to the stored heading/diagnostic offset;
- no text search is rerun to relocate a result;
- no GTK list/tree scan is used to recover a known model item.

A stale document occurrence must fail closed if its stored snapshot no longer
matches the current text. The user must Refresh.

## 6. Modal selection contract

The editor may move focus, place the insertion cursor, or visually clear a
selection while `Gtk.Dialog.run()` owns a nested event loop. Therefore:

- text and offsets are captured before the dialog opens;
- the dialog receives values derived from the captured snapshot;
- changing the live cursor during the dialog cannot move the planned insertion;
- Source Note text remains the captured selection;
- heading context is determined from the captured selection start;
- document mutation is rejected if the current document no longer equals the captured snapshot.

This follows the mature Zim/ghostwriter pattern and is mandatory for W88.

## 7. Controlled failures

W88 must fail without mutation when:

- document is unsaved for Source Note creation;
- selection is empty for Source Note creation;
- selection/link label is multiline or empty;
- no explicit unique heading IDs exist;
- selected target disappeared or became ambiguous before apply;
- Source Notes sidecar has blocking diagnostics;
- external sidecar token changed and the user cancels/reloads;
- current document snapshot differs from the plan or projection used for navigation;
- any provider returns an unexpected type.

## 8. Atomicity and Undo

- document link insertion is one `begin_user_action()/end_user_action()` unit through `execute_command()`;
- no-op does not dirty the document or finalize an edit;
- Source Note creation uses persist-first save and existing stale-token conflict handling;
- the Authoring Bridge itself is read-only;
- `App.on_undo()` is a UI callback whose return value is not a semantic success flag;
- tests certify Undo by comparing the document buffer before insertion, after insertion and after one Undo operation.

## 9. Explicit exclusions

- Related References and named sets: **DEFER W89**;
- external Pandoc/citeproc handoff: **DEFER W90**;
- heading-ID rename and multi-location rewrite: **DEFER separate contract**;
- Back/Forward history: **DEFER**;
- direct Source Note link syntax in the document: **DEFER**;
- DB, graph, LSP, watcher, background scan/index, plugin framework: **REJECT**;
- automatic document creation or implicit synchronization: **REJECT**.

## 10. Bloat ceilings

- no dependency additions;
- no subprocess;
- no persistent schema;
- App additions remain thin wrappers/composition;
- pure projection and planner remain GTK-free;
- one fourth Research client, not a second panel or window;
- no W89/W90 capability may enter W88.

## 11. Mandatory tests

- pure parsing/projection tests:
  - Unicode;
  - code fences and inline code exclusion;
  - multi-key citations;
  - aliases;
  - duplicate/missing heading targets;
  - deterministic ordering and stable identities;
  - empty documents and malformed inputs;
- selection snapshot:
  - exact immutable text slice;
  - cursor-only state;
  - invalid offsets and foreign provider values rejected;
- heading-link planner:
  - insertion and selection replacement;
  - escaping;
  - multiline/empty rejection;
  - stale/ambiguous target gate;
- controller:
  - direct selected-object dispatch;
  - on-demand rebuild;
  - stale snapshot navigation gate;
  - empty states;
- Source Note bridge:
  - saved/unsaved document;
  - captured selection/reference/target;
  - existing persist-first and FileToken semantics preserved;
- true App/GTK:
  - real named Source Note fields;
  - visible editor selection deliberately moved after dialog opens;
  - captured Source Note text and target remain correct;
  - real named heading-link fields and immutable preview;
  - live cursor deliberately moved after dialog opens;
  - insertion still replaces the captured original range;
  - one Undo restores the exact original document, regardless of callback return value;
- source wiring and bloat tests;
- complete regression suite;
- source provenance on the real desktop Python/GTK environment;
- strict gate;
- true App and true GTK interaction tests, externally timeout-protected;
- final manual desktop validation with click-by-click checklist before publication.

## 12. Repeated-failure rule

A failure of this unitary candidate must not be followed by another incremental
repair. The candidate is suspended, the repository is returned to the
published W87 baseline through a protected exact-path rollback, and a new audit
is required before further implementation.

## 13. Publication rule

No commit or push before explicit desktop PASS. W88 remains a candidate until
all automated gates and final desktop validation pass.
