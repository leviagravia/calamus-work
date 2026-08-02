# Calamus W97 — Bibliography Manager direct mature-source audit

Date: 2026-08-02
Published Calamus baseline: `199459fb023e4862407f7eb60318192f276d3239`
Method: direct inspection of the uploaded source archives only; no web substitution.

## Audited source archives

- GNOME Citations `citations-master(1).zip`, SHA-256 `2ab04a778ef9dc9c4e681ebb006f25adb71e685f038c6f58af679b1c6263f89c`
- JabRef `jabref-main(5).zip`, SHA-256 `aa62a954f5206a3f300d21de68f0a3027a860e15413aed95ae17db6323f99cfb`
- KBibTeX `kbibtex-master(5).zip`, SHA-256 `f65701b654d0db4b797fcd6ccdca4d244dcc7189ddf894ec409b80d4b11a9ee1`
- Zotero `zotero-main(3).zip`, SHA-256 `68e4dd7af5d666adc0b9bad8c44484e55672c2fe7fae7fc136176a1f85c4d93a`
- Pandoc `pandoc-main(1).zip`, SHA-256 `d813fbb68007a697358c515f434ae951ae6d5ee8a4cca66c611acf63bf45083e`
- Referencer `referencer.tar(1).bz2`, SHA-256 `1351fbe200a1742c1bd89ae97145245c27d11d06e3925af786d62918c7c7c75f`
- coBib `cobib-master(1).zip`, SHA-256 `1d74456354d6be52abe8dbd10193396159bbb84a0a56fb086f437cc849f867a3`

## GNOME Citations

Directly inspected:

- `src/entry_list.rs`: `EntryList::filter`, `set_selected`, `show_selection`, `unselect`, `navigate_next`; GTK filter model, one selection model and row factory.
- `src/entry_list_row.rs`: `set_entry`, compact list-row projection and context-menu boundary.
- `src/entry_page.rs`: `set_entry`, `setup_other_entry_row`, `setup_abstract_and_notes`, `setup_pdf`, `open_pdf_action`, `set_pdf_action`.
- `src/selection.rs`: explicit model ownership, selection change handling and selected-item projection.
- `src/window.rs`: `open`, `delete_entry`; delete removes the selected entry, clears selection, changes the visible detail and offers an explicit Undo toast.

Adopted:

- one selection authority connecting compact list and record detail;
- list/detail split instead of rendering every field in each row;
- deterministic search projection separated from the source collection;
- explicit empty state;
- local-file action at the selected-record boundary.

Adapted:

- Citations searches author/title/year/key only; Calamus extends search to every canonical and extra field;
- Citations is a standalone GTK4/libadwaita application; Calamus keeps one GTK3 Research client and the existing controller/store;
- Citations' delete/Undo is replaced by Calamus persist-first save plus known-use impact preview.

Rejected:

- standalone bibliography window and standalone file lifecycle;
- web-search actions and PDF content preview;
- replacement of Calamus' Markdown authority with a BibTeX document model.

## JabRef

Directly inspected:

- `jabgui/.../maintable/MainTable.java`, `MainTableDataModel.java`, `BibEntryTableViewModel.java`, `MainTableColumnModel.java`: filtered/sorted table projection and selected-entry ownership.
- `jabgui/.../entryeditor/EntryEditor.java`, `EntryEditorViewModel.java`, `FieldsEditorTab.java`, `AllFieldsTab.java`, `SourceTab.java`: separation between selection, field presentation, validation and source representation.
- `jabgui/.../linkedfile/OpenSelectedEntriesFilesAction.java`, `LinkedFileEditDialogViewModel.java`, `OpenFolderAction.java`: local-file open/reveal behavior belongs to actions over the selected entry.
- `jabgui/.../mergeentries/threewaymerge/FieldRowViewModel.java`, `ThreeWayMergeViewModel.java`, `MergeEntriesDialog.java`, and `fieldsmerger/*`: field-by-field comparison and explicit merged-result construction.
- `jabgui/.../mergeentries/multiwaymerge/MultiMergeEntriesViewModel.java`: duplicate review is a separate high-complexity workflow.

Adopted:

- search/filter/sort as a rebuildable projection, not a second authority;
- detail/editor separation;
- explicit selected-entry actions;
- file open/reveal as commands, not embedded document ownership;
- field-by-field merge only as a separately contracted Full feature.

Adapted:

- Calamus uses compact rows plus a vertical detail because the Research Panel is narrower than JabRef's main table;
- Core offers simple deterministic filters rather than configurable columns and query syntax;
- safe delete checks Calamus authorities instead of JabRef groups/database relations.

Rejected:

- JavaFX table architecture, database-like library state, web fetchers, AI tabs, automatic metadata lookup and background file management;
- automatic/batch merge in Core.

Deferred to Bibliography Manager Full:

- duplicate centre;
- field-by-field merge with impact preview and rollback;
- advanced query/filter language and batch operations.

## KBibTeX

Directly inspected:

- `src/gui/file/fileview.cpp` and `basicfileview.cpp`: selected-element list view and action dispatch.
- `src/gui/file/sortfilterfilemodel.cpp`: dedicated sort/filter proxy rather than mutating the file model.
- `src/gui/widgets/filterbar.cpp`: visible filter state separated from the bibliographic file.
- `src/gui/element/elementeditor.cpp`: `setElement`, `addTabWidgets`, `apply`, `validate`, `reset`, `setReadOnly`; editor validates before applying.
- `src/gui/element/associatedfilesui.cpp`: local-file association, path presentation and preview of the operation.

Adopted:

- proxy/projection model for search and sort;
- validation before mutation;
- explicit read-only state;
- local-file state shown separately from bibliographic metadata.

Adapted:

- Calamus keeps a single local-file path in Core and delegates opening/revealing to the OS;
- Calamus' dialog remains small and type-independent, while preserving unknown fields.

Rejected:

- Qt/KDE UI dependencies;
- file copying/renaming/association management inside Calamus;
- multi-attachment ownership in Core.

Deferred:

- multiple attachments and relative-path policy.

## Zotero

Directly inspected:

- `chrome/content/zotero/itemTree.jsx`, `itemTreeRow.js`, `itemTreeColumns.jsx`: large-library list, stable selection and derived row state.
- `elements/itemPane.js`, `itemPaneHeader.js`, `itemPaneSidenav.js`: selected-item detail composed from sections.
- `elements/attachmentsBox.js`, `attachmentRow.js`: attachments as a separate section/action surface.
- `elements/relatedBox.js`: explicit related-item display.
- `xpcom/duplicates.js`, `elements/duplicatesMergePane.js`, `mergeItems.mjs`: duplicate detection and merge are separate workflows with an explicit master/result.

Adopted:

- selected-item detail as a derived view;
- clear separation of files, related records and core metadata;
- duplicate merge must be an explicit review workflow, never an implicit side effect.

Adapted:

- Calamus shows one text detail rather than extensible pane sections;
- current-document context replaces Zotero collections/database scopes.

Rejected:

- database, sync, plugins, browser integration, background indexing, attachment storage, full-text indexing and cloud services;
- Zotero-scale tree/column customization.

Deferred:

- duplicate centre and reviewed merge for Full.

## Pandoc

Directly inspected:

- `src/Text/Pandoc/Readers/BibTeX.hs`;
- `src/Text/Pandoc/Writers/BibTeX.hs`;
- `src/Text/Pandoc/Citeproc/BibTeX.hs`;
- `src/Text/Pandoc/Citeproc/CslJson.hs`;
- `src/Text/Pandoc/Citeproc.hs`.

Adopted:

- Pandoc/citeproc remains an external deterministic formatter/converter;
- bibliographic output is derived from the canonical Calamus library;
- CSL/BibTeX representations never become Calamus' authority.

Adapted:

- W97 Core merely exposes gateways and simple Markdown/text projection; existing W87/W90 controllers retain ownership of BibTeX and styled output.

Rejected:

- reimplementation of citeproc inside Bibliography Manager;
- CSL JSON/YAML as a second persistent authority.

Deferred:

- Full may add current filtered/selected scopes to the existing W90 workflow.

## Referencer

Directly inspected:

- `src/DocumentView.C`: document list selection and record navigation;
- `src/DocumentProperties.C`: selected-document metadata editing;
- `src/RefWindow.C`: tag filtering (`tagSelectionChanged`), notes pane update, delete confirmation, `ensureSaved` lifecycle;
- `src/TagList.C`: explicit tag model.

Adopted:

- tag filtering visibly changes a derived list;
- detail/notes follow the current selection;
- save/close paths explicitly protect modified state.

Adapted:

- Calamus derives tags from `references.md` and uses atomic persist-first writes;
- Calamus does not own/copy PDF documents.

Rejected:

- legacy standalone GTK application lifecycle, plugin metadata retrieval, library-file ownership and document transfer/copy features.

## coBib

Directly inspected:

- `src/cobib/ui/components/list_view.py`: `ListView`, current-label navigation and deterministic list motion;
- `entry_view.py`: separate selected-entry representation;
- `main_content.py`: one visible content selection;
- `search_view.py`: navigable search result projection;
- `commands/search.py`: explicit search command and separate renderers;
- `commands/open.py`: selected-record local resource opening;
- `commands/delete.py`: explicit delete command;
- `commands/export.py`: derived export command.

Adopted:

- command/projection separation;
- one selected key can be restored in filtered results;
- opening and exporting are explicit actions over a selected or filtered set.

Adapted:

- Calamus implements the projection as GTK-free Python and renders it in the existing GTK panel;
- simple export uses the current visible projection.

Rejected:

- TUI/CLI as a second front end, database object, Git command integration, online parsers and downloader.

## Mandatory decision matrix

| Concern | ADOPT | ADAPT | REJECT | DEFER |
|---|---|---|---|---|
| Authority | one transparent local file | existing `references.md` grammar | DB/JSON index/second library | none |
| UI | list/detail, one selection | compact vertical GTK3 Research client | standalone app, Qt/TUI/GTK4 dependency | configurable wide columns |
| Search | rebuildable in-memory projection | all fields + explicit simple filters | background index | query language |
| CRUD | selected-record actions, validation | existing persist-first controller | implicit mutation | batch editing |
| Delete | explicit confirmation | current known-authority impact | silent cascade | cross-filesystem scan |
| Files | open/reveal selected path | one path, OS delegation | copy/index/embed PDF | multiple attachments, relative paths |
| Duplicates | explicit review | exact identifiers as derived errors | automatic merge | duplicate centre, field merge |
| Export | derived outputs | current visible projection + W87/W90 reuse | second authority | extra W90 scopes |
| Metadata | user-controlled | deterministic key suggestion | web/AI retrieval | none |

## Result for Calamus

The seven codebases converge on one transferable design: keep the canonical data model separate from a rebuildable list/detail/search projection, keep one selected-record authority, and make destructive or external-file operations explicit. W97 Core therefore extends the existing Calamus ReferenceStore/ReferenceController/Research Panel rather than introducing a new subsystem. Full duplicate/merge work remains frozen outside the Core contract.



## Exact-log correction and search/model rebuild addendum

The later dedicated R1/R2 logs supersede the initial crash hypothesis. Both failures were ordinary false-negative assertions caused by testing `Gtk.SearchEntry.search-changed` as though it were synchronous. The lifecycle observations remain design risks, not the causal frame.

Focused transfer from the mature corpus:

- GNOME Builder: persistent model/selection separation, generation tokens, and publishing only current results.
- GNOME Text Editor: construct the final result set before one publication event, retarget semantic selection, and suppress focus/actions during transient states.
- GNOME Citations, JabRef, KBibTeX, Zotero, Referencer and coBib: bibliographic identity and selected item are domain state; rows are presentation.

Rebuild matrix addition:

| Concern | ADOPT | ADAPT | REJECT | DEFER |
|---|---|---|---|---|
| Interactive search | explicit coalescing and stale-generation cancellation | 150 ms GTK3 timer over `changed` | implicit toolkit delay treated as synchronous | configurable delay |
| Completion oracle | delivered generation + expected projection | bounded true-App wait | one `pump()` after `set_text()` | performance telemetry |
| Selection | controller-owned citation key | row selection translated to/from key | row widget as semantic authority | full GtkTreeModel migration |
| Profile failure | capture status and emit full log before fail | Bash `if` condition protected from ERR trap | hidden dedicated log | optional core dump |
