# Calamus User Guide

Calamus is a lightweight, offline-first editor for plain-text and Markdown writing. This guide explains the visible commands and gives practical examples. The guide is part of the Calamus source and must be updated whenever a work item adds or changes a user-visible feature.

## Current command menu (W95extra mature-source rebuilt candidate)

This chapter is the authoritative map of the commands that are visible in the W95extra mature-source rebuilt candidate. It follows the menu bar from left to right and includes every static submenu. Dynamic lists such as recent files, templates, workspaces and favourites are described as lists because their rows depend on the user’s data.

Use this chapter when you know **where a command should be** but do not yet know what it does. Complex tools have separate tutorial chapters later in the guide. A command shown here is available now. The next chapter, **Final command menu target**, is explicitly a roadmap and must not be read as a list of already implemented functions.

### File

`File` owns document lifecycle, templates, the Writing Workspace, file favourites, printing and application exit.

- **New — `Ctrl+N`**: create a new empty document after the normal unsaved-changes check.
- **New from Template**: open the dynamic template submenu and create a document from a saved template.
- **Open… — `Ctrl+O`**: choose and open a text or Markdown document.
- **Recent Files**: open one of the files recorded in the recent-files list.
- **Writing Workspace**: manage the folder-based writing workspace.
  - **Show Workspace Panel**: reveal the Workspace in the left panel.
  - **New Text File…**: create a new text file inside the selected workspace folder.
  - **New Folder…**: create a folder inside the selected workspace folder.
  - **Rename Selected Item…**: rename the selected file or folder together with managed research sidecars when applicable.
  - **Duplicate Selected Text File**: duplicate a selected text file transactionally and carry its managed sidecars.
  - **Move Selected Item to Trash**: send the selected item and its managed sidecars to the system Trash.
  - **Change Workspace Folder…**: choose a different workspace root.
  - **Recent Workspaces**: reopen a root from the dynamic recent-workspaces list.
  - **Rescan Folder Contents**: rebuild the visible Workspace tree from disk.
  - **Reveal Workspace Folder in File Manager**: open the root in the desktop file manager.
  - **Close Workspace**: detach the current workspace without deleting files.
- **Save — `Ctrl+S`**: save the active document to its current path.
- **Save As… — `Ctrl+Shift+S`**: save the active document under a new path.
- **Save as Template…**: store the current text as a reusable template.
- **Manage Templates…**: inspect, rename or remove saved templates.
- **Favorites**: maintain favourite files, not positions inside a document.
  - **Add to Favourites — `Ctrl+Alt+B`**: add the current file to the favourites list.
  - **Edit Favourites… — `Ctrl+Shift+D`**: edit the stored list.
  - **Reload Favourites — `Ctrl+Alt+R`**: reload the list from its authority.
  - The remaining rows are the dynamic favourite-file entries.
- **Print Preview… — `Ctrl+Shift+P`**: preview the printable form of the current document.
- **Print… — `Ctrl+P`**: open the system print workflow.
- **Quit — `Ctrl+Q`**: close Calamus through the normal lifecycle checks.

### Edit

`Edit` contains reversible editing, clipboard commands and the complete current search/replace surface.

- **Undo — `Ctrl+Z`**: undo the most recent editor mutation and return the viewport to the restored caret position.
- **Redo — `Ctrl+Y`**: reapply the most recently undone mutation.

Undo and Redo preserve the **exact caret and selection** recorded at the edit boundary, including which end of a selection owns the insertion mark. Calamus does not guess the edit position from a text diff. After restoration, the viewport adapter waits for valid GTK scroll geometry and then projects the insertion mark through the vertical adjustment, centering it only when it is outside the safe visible area. This is one replaceable, event-driven reveal request—not a chain of timeouts—and cursor navigation by itself does not create an Undo step. Large-document history limits remain unchanged.
- **Cut — `Ctrl+X`**: move the selection to the clipboard.
- **Copy — `Ctrl+C`**: copy the selection.
- **Paste — `Ctrl+V`**: paste clipboard text.
- **Paste as Plain Text — `Ctrl+Shift+V`**: paste without rich-text formatting.
- **Select All — `Ctrl+A`**: select the entire document.
- **Duplicate Line / Selection — `Ctrl+D`**: duplicate the selection or the current line.
- **Find / Replace… — `Ctrl+F`**: open the unified find-and-replace interface.
- **Find All…**: collect all current matches for navigation.
- **Find Next Word — `Ctrl+G`**: move to the next match.
- **Find Previous — `Ctrl+Shift+G`**: move to the previous match.
- **Replace — `Ctrl+H`**: open replace controls.
- **Replace All — `Ctrl+Shift+H`**: replace all confirmed matches.

### Research

`Research` supports writing with reusable clips, document-local provisional work, bibliography, source-grounded notes, explicit links and derived checks. It does not create a hidden project database.

- **Research Panel — `Ctrl+Alt+C`**: show or hide the shared right-side Research Panel.
- **Clip Collection**: activate the Clip Collection client.
- **Insert Clip… — `Ctrl+Alt+K`**: search the shortcut list and insert the selected clip body into the editor.
- **Scratchpad — `Ctrl+Alt+S`**: activate the document-local Scratchpad client.
- **References**: activate the global Markdown bibliography.
- **Tags**: open the derived tag inventory for References, current Source Notes and current Scratchpad.
- **Reference Sets**: activate explicit named sets of Reference keys.
- **Source Notes**: activate the current document’s source-note sidecar.
- **Authoring Bridge**: activate derived backlinks, uses and broken-link views.
- **Capture Selection in Scratchpad… — `Ctrl+Alt+Shift+S`**: create a Scratchpad entry from selected manuscript text.
- **New Scratchpad Entry for Current Section…**: create an entry already linked to the current explicit heading.
- **Show Scratchpad for Current Section**: open Scratchpad filtered by the current section.
- **Create Source Note from Selection…**: create a Quote, Paraphrase or Comment from selected text.
- **Insert Link to Heading…**: insert an explicit internal link to a document heading.
- **Quick Cite… — `Ctrl+Alt+Q`**: search References and insert a Pandoc citation marker.
- **Open Citation in References — `Ctrl+Alt+Shift+Q`**: resolve the citation at the caret and open its Reference.
- **Rename Reference Key…**: preview and apply a controlled key migration across managed authorities.
- **Research Check…**: run an integrated consistency audit.
- **Tag Integrity…**: find and safely normalize explicit tag variants.
- **Import BibTeX/BibLaTeX…**: preview and import bibliographic records into `references.md`.
- **Export References as BibTeX/BibLaTeX…**: derive a `.bib` export without creating a second authority.
- **Export Research Apparatus…**: create one of the five derived Markdown research products.
- **Export with Pandoc/citeproc…**: create formatted bibliographies or documents with processed citations.

### Navigate

`Navigate` changes location or the visible left-side navigation client. It does not alter manuscript text.

- **Navigator Panel — `Ctrl+Alt+N`**: show or hide the document-structure Navigator.
- **Writing Workspace**: show or hide the folder Workspace in the same left-panel host.
- **Go to Line… — `Ctrl+L`**: move to an exact logical line.
- **Go to Section… — `Ctrl+Shift+L`**: choose a parsed Markdown section and move to it.
- **Insert Bookmark Here — `Ctrl+F2`**: add or remove a named navigation position at the current caret.
- **Manage Bookmarks…**: inspect and navigate bookmark positions in the current document.
- **Next Heading — `Ctrl+PageDown`**: move to the next heading.
- **Previous Heading — `Ctrl+PageUp`**: move to the previous heading.

### Writing

`Writing` is the bounded initial writing-assistance menu introduced by W95extra. It contains only the four commands authorized for this work item.

- **Typewriter Mode — `Shift+F9`**: keep the active visual line near the vertical midpoint once that position is naturally attainable. Pointer selection and manual scrolling temporarily take control; typing, keyboard movement, Undo/Redo or explicit navigation resume the mode. Typewriter Mode changes only the viewport and never inserts text or creates an Undo step.
- **Insert Date**: insert the current local date as `YYYY-MM-DD` through the normal grouped editor command boundary.
- **Insert Time**: insert the current local time as `HH:MM` through the same boundary.
- **Insert Date and Time — `Ctrl+Alt+D`**: insert `YYYY-MM-DD HH:MM`.

### Revise

`Revise` transforms or cleans existing text deliberately. Selection-sensitive commands act on the selection and must remain undoable through the editor mutation gateway.

- **UPPERCASE (convert selected) — `Ctrl+Alt+U`**: convert the selection to uppercase.
- **Lowercase (convert selected) — `Ctrl+Alt+Shift+U`**: convert the selection to lowercase.
- **Title Case — `Ctrl+Alt+Y`**: apply title capitalization.
- **Sentence case — `Ctrl+Alt+Shift+Y`**: normalize the selection as sentence case.
- **Next Bookmark — `F2`**: move to the next bookmark.
- **Previous Bookmark — `Shift+F2`**: move to the previous bookmark.
- **Paste Clean from PDF — `Ctrl+Alt+V`**: clean clipboard text copied from a PDF before insertion.
- **Clean Selected Text from PDF — `Ctrl+Alt+Shift+V`**: clean selected PDF-derived text already in the document.
- **Smart Typography — `Ctrl+Alt+M`**: normalize common typographic forms.
- **Reflow Paragraph — `Ctrl+Alt+J`**: reflow the current paragraph.
- **Join Lines — `Ctrl+J`**: join selected or adjacent lines according to the command contract.
- **Remove Extra Spaces**: collapse unwanted repeated spaces.
- **Remove Trailing Spaces**: remove spaces at line endings.
- **Sort Alphabetically A-Z — `Ctrl+Alt+Up`**: sort selected lines ascending.
- **Sort Alphabetically Z-A — `Ctrl+Alt+Down`**: sort selected lines descending.

### View

`View` currently exposes concentration and auxiliary visual tools.

- **Focus Mode — `F9`**: reduce visual distraction around the editor.
- **Distraction-Free Mode — `F11`**: switch to the full distraction-free presentation.
- **Highlight Current Line — `Ctrl+Alt+I`**: toggle current-line highlighting.
- **Character Map — `Ctrl+Alt+F10`**: open the character-selection utility.

### Options

`Options` is still visible in W92 for historical compatibility. The approved final menu removes this top-level menu and redistributes these commands under `View` and `Tools`.

- **Word Wrap — `Alt+Z`**: toggle wrapping of long logical lines.
- **Font… — `Ctrl+Shift+F`**: choose the editor font.
- **Transparent Mode — `Ctrl+Shift+T`**: toggle the saved transparency mode.
- **Always on Top — `Ctrl+Shift+A`**: keep the main window above ordinary windows.
- **White Background**: select the light appearance.
- **Dark Mode**: select the dark appearance.
- **Line Numbers — `Ctrl+Alt+L`**: show or hide logical line numbers.
- **Font Bigger — `Ctrl++`**: increase the editor font size.
- **Font Smaller — `Ctrl+-`**: decrease the editor font size.
- **Opacity**: set an exact window opacity.
  - **Opacity Selection…**: choose a value through the opacity dialog.
  - **100%, 90%, 88%, 80%, 70%, 60%, 50%, 40%, 30%**: apply the selected preset directly.

### Tools

`Tools` contains external utilities and diagnostic information.

- **External Spellcheck — `F7`**: run the configured external spelling workflow.
- **Document Statistics — `Ctrl+Alt+W`**: show counts and document measurements.
- **Language…**: select the language used by supported language tools.
- **System Info…**: show runtime, source identity and environment information.

### Help

- **User Guide…**: open this guide with the Guide Navigator visible by default.
- **Keyboard Shortcuts — `Ctrl+/`**: show the shortcut reference.
- **About — `F1`**: show the stable Calamus identity and credits.

### What is not a current top-level menu

W95extra exposes the bounded top-level `Writing` menu documented above. `Options` is still present even though it is excluded from the approved final menu. The final target below records later destinations and must not be used to infer that an unfinished command already exists.

## Final command menu target

This chapter records the final menu architecture approved in operational-memory Entry 061 and updates it with the later certified Research, Workspace, Reference Sets, Authoring Bridge, Pandoc and Scratchpad decisions. It is a **roadmap**, not a claim about the current executable.

Status words used below:

- **Available**: already present in the current W92 candidate, although its final menu location may still change.
- **Planned**: approved final target but not yet certified.
- **Frozen**: approved scope deliberately postponed. Scratchpad Full is frozen until Calamus is complete and the user gives a separate explicit authorization.
- **Retired**: rejected or removed behavior that must not be presented as available.

The final top-level order is:

```text
File
Edit
Research
Navigate
Writing
Revise
View
Tools
Help
```

`Search` and `Options` are not final top-level menus. Search remains under `Edit`; current Options commands move mainly to `View` and `Tools`.

### Final File

```text
File
├── New                                      [Available]
├── New from Template                        [Available]
├── Open…                                    [Available]
├── Open Recent                              [Available]
│   ├── [recent files]
│   └── Clear Recent Files                   [Planned]
├── Writing Workspace                        [Available]
│   ├── Show Workspace Panel
│   ├── New Text File…
│   ├── New Folder…
│   ├── Rename Selected Item…
│   ├── Duplicate Selected Text File
│   ├── Move Selected Item to Trash
│   ├── Change Workspace Folder…
│   ├── Recent Workspaces
│   ├── Rescan Folder Contents
│   ├── Reveal Workspace Folder in File Manager
│   └── Close Workspace
├── Save                                     [Available]
├── Save As…                                 [Available]
├── Save a Copy…                             [Planned]
├── Revert to Saved                          [Planned]
├── Templates                                [Available]
│   ├── Save as Template…
│   └── Manage Templates…
├── Favorites                                [Available]
│   ├── Add Current File to Favorites
│   ├── Open Favorite…
│   ├── Remove Current File from Favorites
│   └── Manage Favorites…
├── Export                                   [Planned shell; Pandoc engine available]
│   ├── Export as PDF…
│   ├── Export as HTML…
│   ├── Export as DOCX…
│   └── Export as Markdown…
├── Page Setup…                              [Planned]
├── Print Preview…                           [Available]
├── Print…                                   [Available]
└── Quit                                     [Available]
```

Favorites remain file/document shortcuts. They are not bookmarks and therefore never belong under `Navigate`.

### Final Edit

```text
Edit
├── Undo                                     [Available]
├── Redo                                     [Available]
├── Cut                                      [Available]
├── Copy                                     [Available]
├── Paste                                    [Available]
├── Paste as Plain Text                      [Available]
├── Select All                               [Available]
├── Duplicate Line / Selection               [Available]
├── Find / Replace…                          [Available]
├── Find All…                                [Available]
├── Find Next                                [Available]
├── Find Previous                            [Available]
├── Replace Current                          [Partly available through Replace]
├── Replace All                              [Available]
├── Go to Search Result                      [Planned]
└── Clear Search Highlight                   [Planned]
```

Preferences belong under `Tools` in the final menu.

### Final Research

```text
Research
├── Show / Hide Research Panel               [Available]
├── Clip Collection                          [Available]
│   ├── Insert Clip…                         [Available; Ctrl+Alt+K]
│   ├── New / Capture / Edit / Duplicate     [Available in panel]
│   ├── Delete with confirmation             [Available in panel]
│   ├── Copy Body / Refresh / Open Clip File [Available in panel]
│   └── Mnemonic shortcuts / {{cursor}}      [Available]
├── Scratchpad                               [Basic available; Full frozen until Calamus completion and explicit authorization]
│   ├── Show Scratchpad                      [Available]
│   ├── Capture Selection in Scratchpad…     [Available]
│   ├── New Entry for Current Section…       [Available]
│   ├── Show for Current Section             [Available]
│   ├── Insert Body                          [Available in panel]
│   ├── Copy Body                            [Available in panel]
│   ├── Refresh                              [Available in panel]
│   ├── Archive / Restore / Delete           [Available in panel]
│   ├── Clear Scratchpad                     [Retired as an unsafe blind bulk action]
│   ├── Links to References and Source Notes [Frozen: Scratchpad Full]
│   ├── Related Entries                      [Frozen: Scratchpad Full]
│   └── Show Uses                            [Frozen: Scratchpad Full]
├── References                               [Available]
│   ├── Add Reference Note                   [Adapted as New Reference]
│   ├── Insert Reference Marker              [Adapted as Quick Cite…]
│   ├── Open References List                 [Available as References]
│   ├── Clear Unused References              [Planned only with impact preview]
│   ├── New / Edit / Duplicate / Delete
│   ├── Related References
│   ├── Quick Cite…
│   ├── Open Citation in References
│   └── Rename Reference Key…
├── Reference Sets                           [Available]
│   ├── New / Edit / Delete Set
│   └── Navigate Set Members
├── Source Notes                             [Available]
│   ├── Add Source Note                      [Available as New / Create from Selection]
│   ├── Insert Source Note Marker            [Planned; explicit textual convention required]
│   ├── Open Source Notes                    [Available]
│   ├── Manage Source Notes                  [Available through the panel]
│   ├── Create Source Note from Selection…
│   ├── New / Edit / Delete Source Note
│   └── Navigate Document Target
├── Authoring Bridge                         [Available]
│   ├── Backlinks by Reference
│   ├── Backlinks by Heading
│   ├── Related References
│   └── Broken Research Links
├── Tags                                     [Available]
│   ├── Add Tag to Selection                 [Deferred: no hidden document-tag authority]
│   ├── Show Tags List                       [Available as Tags]
│   ├── Go to Next Tag                       [Adapted as Open exact use]
│   ├── Go to Previous Tag                   [Adapted as Open exact use]
│   ├── Show Uses                            [Available in Tags]
│   ├── Rename Tag…                          [Available as Rename / Merge…]
│   ├── Merge Tags…                          [Available as Rename / Merge…]
│   ├── Remove Tag…                          [Available]
│   ├── Normalize All…                       [Available]
│   └── Manage Tags…                         [Available as Tags]
├── Insert Link to Heading…                  [Available]
├── Research Check…                          [Available]
├── Tag Integrity…                           [Available]
├── Import BibTeX/BibLaTeX…                  [Available]
├── Export References as BibTeX/BibLaTeX…   [Available]
├── Export Research Apparatus…               [Available]
├── Export with Pandoc/citeproc…             [Available]
└── Research Panel Settings…                 [Planned]
```

The Tags client is a projection over explicit tags already stored in Markdown authorities. It does not create a database, automatic taxonomy, knowledge graph or AI tagging system. The original Entry 061 actions for next/previous document tag were adapted to exact-use navigation because Calamus has no hidden inline document-tag authority.

### Final Navigate

```text
Navigate
├── Navigator Panel                          [Available]
├── Writing Workspace                        [Available]
├── Go to Line…                              [Available]
├── Go to Beginning                          [Planned]
├── Go to End                                [Planned]
├── Go to Section…                           [Available]
├── Refresh Section List                     [Planned explicit command]
├── Bookmarks                                [Available core; final placement planned]
│   ├── Insert Bookmark Here
│   ├── Next Bookmark
│   ├── Previous Bookmark
│   └── Manage Bookmarks…
├── Position History                         [Planned]
│   ├── Back
│   └── Forward
├── Revision Marks                           [Planned]
│   ├── Next Revision Mark
│   └── Previous Revision Mark
├── Next Heading                             [Available]
├── Previous Heading                         [Available]
├── Next Paragraph                           [Planned]
├── Previous Paragraph                       [Planned]
├── Next Footnote                            [Planned]
└── Previous Footnote                        [Planned]
```

Bookmarks are named positions inside one document. They are distinct from File Favorites.

### Final Writing

```text
Writing
├── Word Count                               [Planned placement]
├── Document Statistics                      [Available under Tools today]
├── Writing Statistics                       [Planned]
├── Set Word Goal…                           [Planned]
├── Show Word Goal                           [Planned]
├── Clear Word Goal                          [Planned]
├── Focus Mode                               [Available under View today]
├── Typewriter Mode                          [Available under Writing]
├── Distraction-Free Mode                    [Available under View today]
├── Insert Heading                           [Planned]
├── Insert Subheading                        [Planned]
├── Insert Separator                         [Planned]
├── Insert Footnote                          [Planned]
├── Insert Citation Placeholder              [Planned]
├── Insert Comment / Note                    [Planned]
├── Insert Date                              [Available under Writing]
├── Insert Time                              [Available under Writing]
└── Insert Date and Time                     [Available under Writing]
```

W95extra restores Typewriter Mode through a new geometry-owned viewport runtime. The previous retired implementation remains forbidden; publication still requires the dedicated True GTK and manual desktop gates.

### Final Revise

```text
Revise
├── Uppercase                                [Available]
├── Lowercase                                [Available]
├── Title Case                               [Available]
├── Sentence Case                            [Available]
├── Invert Case                              [Planned]
├── Fix Word Spacing                         [Planned]
├── Remove Extra Spaces                      [Available]
├── Remove Trailing Spaces                   [Available]
├── Normalize Line Breaks                    [Planned]
├── Reflow Paragraph                         [Available]
├── Reflow Selection                         [Planned]
├── Clean Selected Text from PDF             [Available]
├── Paste Clean from PDF                     [Available]
├── Smart Typography                         [Available core]
│   ├── Straight Quotes to Curly Quotes      [Planned explicit subcommand]
│   ├── Curly Quotes to Straight Quotes      [Planned explicit subcommand]
│   ├── Hyphen to En Dash                    [Planned explicit subcommand]
│   ├── Double Hyphen to Em Dash             [Planned explicit subcommand]
│   └── Normalize Apostrophes                [Planned explicit subcommand]
├── Revision Marks                           [Planned]
│   ├── Insert Revision Mark
│   ├── Remove Revision Mark
│   ├── Clear All Revision Marks
│   └── Show Revision Marks List
├── Trim Empty Lines                         [Planned]
├── Remove Duplicate Blank Lines             [Planned]
└── Clean Text…                              [Planned]
```

### Final View

```text
View
├── Text Wrap                                [Available under Options today]
├── Font…                                    [Available under Options today]
├── Increase Font Size                       [Available under Options today]
├── Decrease Font Size                       [Available under Options today]
├── Reset Font Size                          [Planned]
├── Line Numbers                             [Available under Options today]
├── Highlight Current Line                   [Available]
├── Status Bar                               [Planned]
├── Research Panel                           [Available through Research]
├── Navigator Panel                          [Available through Navigate]
├── Writing Workspace                        [Available through Navigate/File]
├── Fullscreen / Distraction-Free Mode       [Available]
├── Always on Top                            [Available under Options today]
├── Theme                                    [Available core]
│   ├── Light
│   ├── Dark
│   └── System Default                       [Planned explicit choice]
├── Transparency                             [Available core]
│   ├── Increase Transparency                [Planned relative command]
│   ├── Decrease Transparency                [Planned relative command]
│   └── Reset Transparency                   [Planned]
├── Zoom In                                  [Planned]
├── Zoom Out                                 [Planned]
└── Reset Zoom                               [Planned]
```

The current top-level `Options` menu disappears when these placements are completed and certified.

### Final Tools

```text
Tools
├── Spell Check                              [External workflow available]
│   ├── Check Spelling
│   ├── Set Language
│   ├── Add Word to Dictionary               [Planned]
│   └── Manage Dictionaries…                 [Planned]
├── Character Map                            [Available under View today]
├── Insert Special Character…                [Planned]
├── Document Info                            [Planned]
├── System Info…                             [Available]
├── Writing Workflow Tools                   [Planned]
│   ├── Reading Time
│   ├── Estimate Pages
│   ├── Outline from Headings
│   └── Export Outline…
├── Preferences…                             [Planned]
└── Reset Preferences                        [Planned]
```

### Final Help

```text
Help
├── About Calamus                            [Available, final wording]
├── User Guide / Command Guide               [Available; hierarchical Navigator in W92 R3]
├── Keyboard Shortcuts                       [Available]
├── Writing Principles                       [Planned]
└── Writing Workflow                         [Planned]
```

The User Guide opens with a dedicated hierarchical **Guide Navigator** visible by default. This is not the document Navigator: it reads only the guide headings and never changes the active manuscript, its caret or its left-panel state.

### Rule for keeping Help complete

Whenever a work item adds, removes, renames or relocates a visible command, that same work item must update:

1. the current menu map in this guide;
2. the relevant tutorial or command explanation;
3. the final target map when the architectural target changes;
4. the Help Navigator tests that verify menu and submenu visibility.

A work item cannot be published as user-visible functionality while Help still describes an earlier menu.

## Typewriter Mode

Typewriter Mode is a **view policy**, not a text transformation. Turn it on with `Writing → Typewriter Mode` or `Shift+F9`. The menu row is checked while the mode is active. The setting is session-only in W95extra and is not silently persisted.

### What it does

Calamus measures the real GTK insertion-mark rectangle, the visible editor rectangle and the vertical adjustment. After the working line can naturally reach the middle of the editor, the mode keeps that visual line near 50% of the viewport. A temporary bottom runway, derived from the current viewport height, lets the last visual line reach the same position. The runway is presentation-only and is removed exactly when the mode is turned off or Calamus closes.

The first lines of a short or newly opened document remain at the natural top. Calamus does not create an empty half-screen above the beginning merely to force immediate centering.

### When Calamus temporarily yields control

Typewriter Mode does not fight deliberate pointer or viewport actions. It suspends projection while:

- the mouse button is down or text is being selected with the pointer;
- a non-empty selection is active;
- the wheel, touchpad or scrollbar is used manually;
- the editor loses focus.

The next edit, keyboard caret movement, Undo/Redo or explicit structural navigation resumes the mode. Merely releasing the mouse does not snap the document back.

### Undo, Redo and navigation

Undo and Redo first restore the exact text, insertion mark and selection bound recorded by W95. Only after that semantic restoration does the single viewport runtime project the restored caret. Search and navigation submit the same kind of semantic viewport intent. No second object writes the vertical adjustment independently.

### What Typewriter Mode never does

It never:

- changes document text, line endings or Markdown;
- inserts padding characters or blank lines;
- creates an Undo step;
- changes the horizontal scroll position;
- uses repeated timeouts, polling or guessed line heights;
- recentres during pointer drag;
- merge itself with Focus Mode or Distraction-Free Mode.

### Practical validation

Use a long wrapped document. Enable the mode near the beginning and type until the caret naturally reaches the midpoint. Continue typing for several paragraphs: the active visual line should remain stable without block jumps, oscillation or drift. Then test pointer selection, wheel scrolling, keyboard resumption, Undo/Redo, the final line and disabling the mode. Turning it off must restore the normal bottom margin immediately.

## Learning the Research apparatus

The Research apparatus is easiest to learn when each object has one clear job. Calamus deliberately keeps the document, bibliography and notes separate so that every file remains readable, portable and recoverable.

### The six objects you must distinguish

| Object | What it is | Where it lives | What it is for |
|---|---|---|---|
| **Reference** | One bibliographic record identified by a stable key such as `ratzinger1968` | Global `references.md` | Describes a source once: author, title, date, publisher, tags and related metadata |
| **Citation** | A Pandoc citation marker such as `[@ratzinger1968]` inside the manuscript | Current document | Shows where a source is cited in the prose |
| **Source Note** | A quotation, paraphrase or research comment with its own stable ID | Document sidecar `Document.md.source-notes.md` | Preserves material derived from a source and its provenance without inserting it into the manuscript |
| **Scratchpad Entry** | A Note, Idea, Draft or Task with its own stable ID | Document sidecar `Document.md.scratchpad.md` | Develops the author’s provisional thinking before it becomes manuscript text |
| **Document Target** | An explicit heading identifier such as `#introduction` created by `## Introduction {#introduction}` | Current document | Connects a Source Note, Scratchpad Entry or internal link to a precise section of the manuscript |
| **Backlink** | A read-only result calculated from the files above | Nowhere: it is derived on demand | Answers questions such as “Where is this Reference cited?” or “Which notes belong to this section?” |

A Reference is not a citation. A Source Note preserves material grounded in a source; a Scratchpad Entry develops the author’s own provisional work. Either may point to a document heading. Backlinks are derived on demand and never become a stored authority.

### Four rules that prevent most mistakes

1. **Create the Reference before creating quotations or paraphrases.** Quote and Paraphrase notes require a valid Reference key.
2. **Use Scratchpad for provisional thinking, not Source Notes.** An Idea, Draft or writing Task belongs in `Document.md.scratchpad.md`; quotations and paraphrases belong in Source Notes.
3. **Give important headings explicit IDs.** Write `## Method {#method}` rather than relying on an automatically generated slug. Calamus offers only explicit, unique IDs as stable targets.
4. **Refresh views after an authority changes.** Authoring Bridge is a snapshot, and Scratchpad may change outside Calamus. Use the relevant **Refresh** command before relying on an old view.

### Which command should I use?

| Your intention | Use this command |
|---|---|
| Register a book, article or archival source | `Research → References` |
| Save a quotation, paraphrase or source-based research observation | `Research → Source Notes` |
| Capture an idea, draft or writing task for the current document | `Research → Scratchpad` or `Ctrl+Alt+S` |
| Preserve selected manuscript text as provisional material | `Research → Capture Selection in Scratchpad…` or `Ctrl+Alt+Shift+S` |
| Turn selected manuscript text into a source-grounded note | `Research → Create Source Note from Selection…` |
| Insert a citation key in the manuscript | `Research → Quick Cite…` |
| Link prose to a stable section of the same document | `Research → Insert Link to Heading…` |
| See every citation and note connected to a source | `Research → Authoring Bridge → Backlinks by Reference` |
| See every link and note connected to a section | `Research → Authoring Bridge → Backlinks by Heading` |
| Find missing keys, missing targets or ambiguous heading IDs | `Research → Authoring Bridge → Broken Research Links` |
| Audit the whole Research apparatus for consistency | `Research → Research Check…` |
| Browse, navigate and standardize Research tags | `Research → Tags` |
| Produce a bibliography, annotated bibliography or dossier | `Research → Export Research Apparatus…` |

## Start here: from a blank editor to a finished short academic article

This is a real beginning-to-end tutorial. It assumes that Calamus has opened with an empty editor and that you need to write a short academic article for a journal. The example article has an introduction, three main sections divided into subsections, and a conclusion. Follow it once with a disposable file before adapting the method to your own work.

The example title is **Tradition and Renewal in Parish Life**. The research question is simple: how can a parish preserve Christian tradition while responding intelligently to present pastoral conditions?

### Stage 1 — Save the empty document before doing research work

Source Notes belong to a saved document. Therefore the first operation is not to create a Reference or a note, but to save the empty file.

1. Choose `File → Save As…`.
2. Create a project folder, for example:

   `~/Documents/Articles/Tradition-and-Renewal/`

3. Save the document as:

   `tradition-and-renewal.md`

Use `.md`, not `.txt`, when the manuscript will contain Markdown headings, internal links and Pandoc citations.

Calamus keeps document-specific research material beside this file in two transparent sidecars:

```text
tradition-and-renewal.md.source-notes.md
tradition-and-renewal.md.scratchpad.md
```

The first stores source-grounded notes; the second stores provisional authorial work. Do not edit either sidecar simultaneously in another application while Calamus is using it.

### Stage 2 — Understand heading levels before typing the outline

Markdown headings are made with hash signs followed by one space:

```markdown
# H1: document title
 ## H2: main section
### H3: subsection
#### H4: smaller subdivision, used only when really necessary
```

For a short academic article, use this hierarchy:

- **one H1** for the title of the whole article;
- **H2** for Introduction, the three main sections and Conclusion;
- **H3** for the subsections inside each main section;
- **H4** only when an H3 subsection genuinely needs another level.

Do not use a new H1 for every section. Do not jump directly from H2 to H4. Do not imitate a heading by writing bold text: `**Introduction**` is bold text, not a structural heading.

Calamus can use an explicit identifier placed at the end of a heading:

```markdown
 ## Introduction {#introduction}
```

The visible title is `Introduction`. The stable target is `#introduction`. Source Notes and internal links can point to that target.

Good identifiers are:

- unique within the document;
- lowercase;
- made from letters, numbers and hyphens;
- short enough to remain readable;
- stable even if you later improve the visible heading title.

Examples:

```markdown
{#introduction}
{#historical-background}
{#word-and-sacrament}
{#pastoral-discernment}
{#conclusion}
```

Avoid spaces, accented characters and duplicate identifiers. Once Source Notes or links point to an identifier, do not change it casually.

### Stage 3 — Type the complete article skeleton

In the empty editor, type or paste this complete outline:

```markdown
# Tradition and Renewal in Parish Life

 ## Introduction {#introduction}

State the problem, the research question and the method here.

 ## 1. Historical background {#historical-background}

### 1.1 Tradition as living reception {#living-reception}

Explain how tradition is received and transmitted.

### 1.2 Change in modern parish life {#modern-parish-change}

Describe the historical and social changes that affect parish ministry.

 ## 2. Theological principles {#theological-principles}

### 2.1 Word and sacrament {#word-and-sacrament}

Explain the theological centre of parish life.

### 2.2 Communion and mission {#communion-and-mission}

Relate ecclesial communion to missionary responsibility.

 ## 3. Pastoral discernment {#pastoral-discernment}

### 3.1 What must be preserved {#what-must-be-preserved}

Identify elements that cannot be reduced to custom or convenience.

### 3.2 What may be adapted {#what-may-be-adapted}

Identify practices that may change in response to real pastoral needs.

 ## Conclusion {#conclusion}

Answer the research question and state the principal result.
```

The numbers `1`, `1.1`, `2`, and so on are visible text. They are optional. The structural level comes from `##` or `###`, not from the number.

Choose `Navigate → Section Navigator` and verify that the title, the five H2 sections and the six H3 subsections appear in the correct hierarchy. If the hierarchy looks wrong, correct it before writing prose.

At this point you have not written the article. You have created its intellectual map.

### Stage 4 — Register each source once in References

A Reference is the bibliographic identity of a source. It belongs to the global Calamus References library and may be reused in many documents. A Source Note belongs instead to this particular article.

Choose `Research → References` and add these three example records.

First source:

```text
Key: ratzinger1968
Type: Book
Author: Joseph Ratzinger
Title: Introduction to Christianity
Year: 1968
Tags: faith, theology
```

Second source:

```text
Key: newman1870
Type: Book
Author: John Henry Newman
Title: An Essay in Aid of a Grammar of Assent
Year: 1870
Tags: faith, assent
```

Third source:

```text
Key: vaticanii1964
Type: Other
Author: Second Vatican Council
Title: Lumen gentium
Year: 1964
Tags: church, communion, mission
```

A readable key normally combines author or institution and year. Keep it stable. Page numbers do not belong in the key; they belong in Source Note locators and citations.

If the source already exists in References, do not create a duplicate. Select the existing record and use its canonical key.

### Stage 5 — Build a small research notebook before drafting

You can create Source Notes before the relevant prose exists. Open `Research → Source Notes` and press **Add**.

Create this quotation note:

```text
Type: Quote
Reference: ratzinger1968
Document Target: #theological-principles
Text: Faith does not destroy reason but calls it to become fully itself.
Locator: p. 42
Comment: Use when explaining why faith and rational inquiry are not enemies.
Tags: faith, reason
```

Create this paraphrase note:

```text
Type: Paraphrase
Reference: vaticanii1964
Document Target: #communion-and-mission
Text: The Church is not closed in upon itself; communion is ordered toward mission.
Locator: no. 1
Comment: Connect ecclesial identity with pastoral outreach.
Tags: communion, mission
```

Create this personal research comment:

```text
Type: Comment
Reference: leave empty
Document Target: #what-may-be-adapted
Text: Distinguish the substance of parish life from customs that developed in one historical period.
Locator: leave empty
Comment: This is my analytical question, not a quotation from a source.
Tags: method, discernment
```

The three types serve different purposes:

- **Quote** preserves the source's wording and therefore needs an exact locator;
- **Paraphrase** records the source's idea in your own words and still needs a Reference and locator;
- **Comment** records your own observation, question or drafting decision and may have no Reference.

A Source Note is not automatically a citation. It stores research material and connects it to a Reference and, optionally, to a section of the article.

### Stage 6 — Draft the Introduction without inserting citations blindly

Replace the placeholder under `## Introduction {#introduction}` with a short paragraph such as:

```markdown
Contemporary parish life often experiences tradition and adaptation as opposing demands. One side fears that every change weakens Christian identity; the other assumes that inherited forms are necessarily obstacles to mission. This article argues that the opposition is false. The decisive question is not whether a practice is old or new, but whether it serves the Church's received faith and present mission.
```

This paragraph states the problem and thesis. It does not need a citation after every sentence. Cite a source when a claim, interpretation, quotation or specific fact depends on that source.

### Stage 7 — Insert a simple citation with a page locator

Under `### 2.1 Word and sacrament {#word-and-sacrament}`, write:

```text
Christian faith does not abolish rational inquiry; it asks reason to become more fully itself.
```

Place the cursor immediately before the final period. Choose `Research → Quick Cite…`, select `ratzinger1968`, and enter this Locator:

```text
p. 42
```

The preview must be:

```markdown
[@ratzinger1968, p. 42]
```

After insertion the finished sentence should be:

```markdown
Christian faith does not abolish rational inquiry; it asks reason to become more fully itself [@ratzinger1968, p. 42].
```

This is the safest ordinary pattern: write the claim, insert the citation before the punctuation, and include the exact page or other locator when one is available.

### Stage 8 — Recognize the main citation possibilities

Calamus stores Pandoc-compatible citation syntax in plain Markdown. These are the patterns you will use most often.

**A source without a specific page**

```markdown
The relation between faith and reason remains central to modern theology [@ratzinger1968].
```

Use this only when the claim concerns the work as a whole or when the source has no useful pagination.

**One page**

```markdown
Faith seeks understanding rather than the suspension of reason [@ratzinger1968, p. 42].
```

**A page range**

```markdown
Newman distinguishes several forms of assent [@newman1870, pp. 55-57].
```

**A numbered paragraph, canon, section or document number**

```markdown
The Church is described as a sacrament of union with God and humanity [@vaticanii1964, no. 1].
```

Type the full locator into the Quick Cite Locator field: `p. 42`, `pp. 55-57`, `no. 1`, `ch. 3`, or another concise form appropriate to the source.

**Two or more sources supporting the same sentence**

A combined Pandoc citation cluster is written manually as:

```markdown
Tradition involves both continuity and living reception [@newman1870, pp. 55-57; @ratzinger1968, p. 42].
```

Each item begins with `@`. Separate the items with semicolons inside one pair of square brackets. Calamus recognizes each key separately in Authoring Bridge and Research Check.

**The author's name already appears in your sentence**

The simplest clear form is:

```markdown
Ratzinger presents faith as an appeal to the whole human capacity for truth [@ratzinger1968, p. 42].
```

Advanced Pandoc users may write a bare narrative key such as:

```markdown
@ratzinger1968 presents faith as an appeal to the whole human capacity for truth.
```

Calamus recognizes a bare `@key`, but Quick Cite deliberately inserts the safer bracketed form. Use bare narrative syntax only when you understand how your external Pandoc/citeproc style will render it.

**A direct quotation**

```markdown
Ratzinger writes that “faith does not destroy reason” [@ratzinger1968, p. 42].
```

The quotation marks do not replace the citation. Preserve the same quotation as a Quote Source Note when it matters to your research trail.

Do not type a citation key that is absent from References. A string such as `[@unknown2026]` remains plain text, but Research Check and Broken Research Links will report it as unresolved.

### Stage 9 — Create a Source Note from text already written in the article

Sometimes you first write or paste an important sentence in the manuscript and only afterward decide to preserve it as research material.

1. Select exactly this sentence in the editor:

   `Christian faith does not abolish rational inquiry; it asks reason to become more fully itself.`

2. Choose `Research → Create Source Note from Selection…`.
3. Confirm:

```text
Type: Paraphrase
Reference: ratzinger1968
Document Target: #word-and-sacrament
Text: Christian faith does not abolish rational inquiry; it asks reason to become more fully itself.
Locator: p. 42
Comment: Draft paraphrase used in section 2.1.
Tags: faith, reason
```

4. Press **Save**.

The document text must not change. Calamus adds one Source Note to the sidecar and selects it in Source Notes.

Use **Create Source Note from Selection** when the exact selected text should become the note. Use **Source Notes → Add** when you are taking notes before writing or when the note text is not already in the manuscript.

### Stage 10 — Link one part of the article to another

Internal links help a reader move through a longer argument and allow Source Notes to target stable sections.

Under `### 3.2 What may be adapted {#what-may-be-adapted}`, write:

```text
The distinction depends on the theological principles discussed above.
```

Select the words:

`the theological principles discussed above`

Open `Research → Authoring Bridge`, choose **Backlinks by Heading**, select `Theological principles — #theological-principles`, and press **Insert Link to Heading…**. Choose the same heading and insert.

The result should be:

```markdown
The distinction depends on [the theological principles discussed above](#theological-principles).
```

Only headings with an explicit, unique identifier are offered. This is why the outline was created with `{#...}` targets at the beginning.

### Stage 11 — Use Authoring Bridge as a map, not as storage

Open `Research → Authoring Bridge`.

Choose **Backlinks by Reference** and select `ratzinger1968`. The list may include:

- the citation `[@ratzinger1968, p. 42]` in the article;
- the Quote Source Note created before drafting;
- the Paraphrase Source Note created from the manuscript selection.

Open a citation result to select the exact citation cluster in the editor. Open a Source Note result to select that stable note in Source Notes.

Choose **Backlinks by Heading** and select `Theological principles — #theological-principles`. The list may include:

- Source Notes whose Document Target is `#theological-principles`;
- internal Markdown links that point to `#theological-principles`.

Choose **Broken Research Links** to find:

- citation keys absent from References;
- document links pointing to missing heading identifiers;
- Source Notes with missing References;
- Source Notes with missing or ambiguous Document Targets.

The Authoring Bridge is a derived snapshot. If you modify the document after opening it, press **Refresh** before trusting counts or opening old rows. Backlinks are never stored in a database.

### Stage 12 — Draft the three main sections in a controlled order

A practical sequence is:

1. open **Backlinks by Heading** for the subsection you are about to write;
2. review its Source Notes;
3. write one paragraph around one clear claim;
4. insert the citation exactly where the source supports the claim;
5. move to the next subsection;
6. use your Comment notes for transitions, objections and conclusions.

For example, section 2 may become:

```markdown
 ## 2. Theological principles {#theological-principles}

### 2.1 Word and sacrament {#word-and-sacrament}

Christian faith does not abolish rational inquiry; it asks reason to become more fully itself [@ratzinger1968, p. 42]. Word and sacrament therefore cannot be treated as inherited ornaments. They constitute the theological centre from which pastoral adaptation must be judged.

### 2.2 Communion and mission {#communion-and-mission}

Ecclesial communion is not self-enclosure. The Church receives unity as a gift that orders it toward witness and service [@vaticanii1964, no. 1]. A parish preserves its identity precisely by allowing that identity to become missionary action.
```

Notice the order: heading, claim, citation, interpretation and transition. The citation supports the claim; it does not replace your argument.

### Stage 13 — Revise headings without breaking their targets

Suppose you improve this visible heading:

```markdown
 ## 3. Pastoral discernment {#pastoral-discernment}
```

and rename it:

```markdown
 ## 3. Criteria for pastoral discernment {#pastoral-discernment}
```

The visible title changed, but the identifier remained `#pastoral-discernment`. Existing Source Notes and internal links still resolve.

If you also change the identifier, every link and Source Note target using the old ID must be updated. After structural editing, run `Research → Research Check…` and inspect **Broken Research Links**.

### Stage 14 — Write the Conclusion from the evidence already assembled

Replace the Conclusion placeholder with a direct answer to the research question:

```markdown
 ## Conclusion {#conclusion}

A parish does not remain faithful by refusing every change, nor does it become missionary by treating inherited forms as disposable. The decisive distinction is theological: Word, sacrament, communion and mission define what must be preserved, while historically conditioned practices may be adapted through prudent discernment. Tradition and renewal are therefore not rival programmes but two dimensions of responsible ecclesial life.
```

A conclusion normally synthesizes the argument. Add citations only when it introduces a new sourced claim or repeats a specific claim that still requires documentation.

### Stage 15 — Perform the final academic check

Before considering the article complete, verify all of the following.

**Document structure**

- there is exactly one H1 title;
- Introduction, the three main sections and Conclusion are H2;
- subsections are H3 beneath the correct H2;
- no level is skipped without reason;
- every heading used as a target has one explicit, unique ID.

**References and citations**

- every `@key` exists in References or resolves through one unambiguous alias;
- quotations and precise claims include a useful locator;
- combined clusters use semicolons between citation items;
- citation punctuation is correct in the surrounding sentence;
- no citation appears inside a code example by mistake.

**Source Notes**

- Quote notes preserve exact wording and locators;
- Paraphrase notes use your wording but retain Reference and locator;
- Comment notes are clearly your own analysis;
- Document Targets point to the section where each note is useful;
- no Source Note was silently duplicated.

**Integrity and navigation**

1. Save the document.
2. Choose `Research → Research Check…`.
3. Open `Research → Authoring Bridge → Broken Research Links`.
4. Correct missing keys and heading targets.
5. Press **Refresh** after document changes.
6. Test at least one backlink by Reference and one backlink by Heading.

**Submission boundary**

Calamus stores transparent Markdown and Pandoc citation syntax. It does not decide the journal's final citation style. Final bibliography formatting belongs to an external Pandoc/citeproc workflow or to the journal's required production system.

### Four common starting situations

The complete tutorial followed one path, but real work may begin in different ways.

**You know the source before you start writing**

`References → Source Notes → article outline → drafting → Quick Cite`

This is the best path for planned academic research.

**You have already written or pasted a useful passage**

`select the passage → Create Source Note from Selection → choose Reference and target → Quick Cite where needed`

This preserves the connection without altering the manuscript text.

**You have an idea that is entirely your own**

`Source Notes → Add → Type: Comment → optional Document Target → no Reference`

Do not invent a Reference merely to store your own analytical note.

**You have a source but do not yet know where it belongs**

Create the Source Note with its Reference and locator, but leave Document Target empty. Add the target later when the outline is stable.

The core method remains the same: first establish structure, then preserve evidence, then write claims, then cite them, and finally inspect the derived connections.

## Source Note types: Quote, Paraphrase and Comment

Choose the type according to what the note contains, not according to how important it is.

### Quote

Use **Quote** when **Text** reproduces the source substantially verbatim.

Recommended fields:

```text
Reference: required
Locator: strongly recommended
Text: exact quotation
Comment: your interpretation, warning or intended use
Tags: concepts useful for retrieval
Document Target: optional section where the quotation may be used
```

Example:

```text
Type: Quote
Reference: newman1870
Page: 63
Text: Growth is the only evidence of life.
Comment: Possible epigraph for the section on doctrinal development.
Target: #development
```

Do not put your own interpretation inside the quoted **Text**. Put it in **Comment** so that source material and analysis remain distinguishable.

### Paraphrase

Use **Paraphrase** when **Text** restates an author’s argument in your own words.

A Paraphrase still requires a Reference because the idea belongs to a source even though the wording is yours.

Example:

```text
Type: Paraphrase
Reference: guardini1950
Page: 18–21
Text: Christian existence is understood through a living relation to the person of Christ, not merely through abstract principles.
Comment: Compare with the personalist structure of the next chapter.
Target: #christology
```

A useful test: if the sentence could be mistaken for your own unsupported claim, preserve the Reference and locator.

### Comment

Use **Comment** for your own research observation, editorial decision, question or reminder. A Comment may have no Reference.

Example without a source:

```text
Type: Comment
Reference: No reference (Comment only)
Text: Verify whether this subsection repeats the argument made in Chapter 2.
Tags: revision, duplication
Target: #method
```

Example linked to a source:

```text
Type: Comment
Reference: ratzinger1968
Text: Compare this source with Guardini before drafting the conclusion.
Tags: comparison, conclusion
```

A Comment is not a substitute for a task manager. Use it when the observation belongs to the intellectual apparatus of this document.

## Understanding every Source Note field

- **ID**: stable identity generated by Calamus. Do not use the visible text as identity and do not change the ID casually.
- **Type**: Quote, Paraphrase or Comment.
- **Reference**: canonical key from `references.md`. Required for Quote and Paraphrase; optional for Comment.
- **Tags**: research concepts, not prose keywords. Prefer a small controlled vocabulary such as `faith`, `ecclesiology`, `method`.
- **Text**: the preserved research content.
- **Comment**: your analysis of the note, intended use, doubts or cross-comparisons.
- **Document Target**: one explicit heading ID in the current document. It answers “Which section is this note intended for?”
- **Page / Page End**: printed or PDF page range.
- **Chapter / Section / Paragraph**: alternative or supplementary locators for sources whose pagination is unstable or absent.

### Locator examples

A printed book:

```text
Page: 42
Page End: 45
```

A conciliar document:

```text
Section: 10
Paragraph: 2
```

An ebook without stable pages:

```text
Chapter: The Nature of Faith
Section: Revelation and Response
```

Do not force every locator field to contain something. Enter only information that helps you return to the source reliably.

## A realistic academic workflow

The following pattern scales from an article to a monograph.

### During reading

1. Add or import the Reference.
2. Create Source Notes while reading.
3. Use **Quote** for exact wording, **Paraphrase** for arguments in your own words and **Comment** for your analysis.
4. Add a precise locator immediately; postponed locators are often never recovered.
5. Add one to three stable tags rather than a long list of near-synonyms.
6. Add a Document Target only when you already know the intended section.

### During outlining

1. Create headings with explicit IDs:

   ```markdown
   ## Historical context {#historical-context}
   ## Theological analysis {#theological-analysis}
   ## Pastoral implications {#pastoral-implications}
   ```

2. Open Authoring Bridge by heading to see which notes are already assigned to each section.
3. Use Comments without References for structural decisions such as “Move this objection before the synthesis.”
4. Insert internal heading links only where they improve navigation for the reader.

### During drafting

1. Write the argument in the document.
2. Use Quick Cite at the exact point where the source supports the statement.
3. Open Authoring Bridge by Reference to inspect every use of a source and avoid accidental over-reliance.
4. Open Authoring Bridge by Heading to retrieve the notes intended for the current section.
5. Convert useful selected prose into a Source Note only when the selection itself should become part of the research record; do not duplicate ordinary draft text mechanically.

### Before export

1. Run Broken Research Links.
2. Run Research Check.
3. Resolve missing citation keys and heading targets.
4. Review tag variants in `Research → Tags` with **Variants only**.
5. Export the appropriate Research Apparatus product.
6. Use external Pandoc/citeproc later for final citation style and bibliography rendering.

## Worked scenario: building one section from several sources

Suppose the document contains:

```markdown
## Revelation and Faith {#revelation-faith}
```

Create these notes:

```text
sn-a
Type: Quote
Reference: ratzinger1968
Page: 47
Target: #revelation-faith
Text: [exact quotation]
Tags: revelation, faith

sn-b
Type: Paraphrase
Reference: guardini1950
Page: 22
Target: #revelation-faith
Text: Guardini presents faith as a personal response rather than assent to an isolated proposition.
Tags: revelation, person

sn-c
Type: Comment
Reference: No reference
Target: #revelation-faith
Text: Begin with the human act of trust, then distinguish it from theological faith.
Tags: structure
```

Authoring Bridge by heading now shows all three notes together even though they have different types and only two have References. Authoring Bridge by Reference shows `sn-a` under `ratzinger1968` and `sn-b` under `guardini1950`, but not `sn-c`. This is expected: the same note collection can be projected by section or by source without duplicating records.

After drafting, insert citations such as:

```markdown
Faith is not reducible to assent to an isolated proposition [@guardini1950, 22].
```

The citation and Source Note now appear together under the Reference projection, while the Source Note remains available under the heading projection.

## Authoring Bridge: how to read the results

### Backlinks by Reference

Use this mode to answer:

- Where is this source cited?
- Which Source Notes depend on it?
- Is an alias being resolved to the canonical key?
- Have I cited the source in the manuscript without preserving any research notes, or preserved notes without citing it yet?

An alias occurrence such as `@intro1968` may appear under canonical Reference `ratzinger1968`. This does not create a second source; it shows that the alias resolves to the same authority.

### Backlinks by Heading

Use this mode to answer:

- Which Source Notes are intended for this section?
- Which internal links point to it?
- Has a planned section accumulated enough material?
- Did I rename or remove a heading target without updating its links?

Only explicit, unique heading IDs are stable targets. If two headings use the same ID, the target becomes ambiguous and Calamus reports it rather than guessing.

### Broken Research Links

This mode may report several different problems that look similar but have different owners:

| Problem | Meaning | Correct place to fix it |
|---|---|---|
| Missing citation key | The document cites a key absent from References | Correct the citation or add/import the Reference |
| Missing Source Note Reference | A note names a key absent from References | Edit the Source Note or restore the Reference |
| Missing heading link target | A Markdown link points to an absent ID | Correct the document link or restore the heading ID |
| Missing Source Note target | A note targets an absent ID | Edit the Source Note or restore the heading ID |
| Ambiguous heading ID | More than one heading owns the same explicit ID | Give each heading a unique ID |

Open each result before editing. Calamus selects the exact document range or stable Source Note ID so that you repair the correct owner.

## Safe editing and stale projections

Authoring Bridge results are deliberately immutable snapshots. This protects navigation from silently drifting after edits.

Example:

1. Build Backlinks by Heading for `#introduction`.
2. Insert another link to `#introduction`.
3. Try to open a row from the old projection.
4. Calamus refuses and asks for **Refresh**.
5. Refresh; the count now includes the new link.

This is not an inconvenience or a synchronization failure. It is a safety gate: Calamus will not use offsets calculated for an older document state.

The same principle applies to external file changes. If `references.md` or the Source Notes sidecar changes after a dialog preview, Calamus fails closed instead of overwriting newer content.

## Common mistakes and how to recover

### “Quote and Paraphrase require a Reference”

Cause: the Source Note type is Quote or Paraphrase but no valid Reference is selected.

Recovery:

1. Cancel the dialog if the intended source has not yet been registered.
2. Add or import the Reference.
3. Reopen the Source Note dialog and select its key.

Use Comment only when the note is genuinely your own observation, not as a way to bypass missing bibliography data.

### The expected Document Target is absent

Possible causes:

- the document is unsaved;
- the heading has no explicit `{#id}`;
- the ID is malformed;
- the same ID occurs more than once;
- the selection is not inside the section you expected.

Recovery: save the document, give the heading one valid unique ID, then reopen the command.

### Authoring Bridge shows an old count

Cause: the projection was built before the latest document or Research change.

Recovery: press **Refresh**. Counts are derived; they are not updated by a background watcher.

### A citation exists but no Source Note appears

This is not automatically an error. A citation marks support in the manuscript; a Source Note preserves research material. You may legitimately have one without the other. Create a Source Note when retaining the quotation, paraphrase, locator or analysis will help future work.

### A Source Note exists but the source is not cited

This is also not automatically an error. The note may be preparatory material, rejected evidence or material reserved for another section. Use Authoring Bridge to review it; do not insert a citation merely to make counts symmetrical.

### A heading link is reported as broken after renaming a heading

Changing the visible heading title does not matter if the explicit ID remains unchanged. Changing or removing `{#id}` changes the target identity. Restore the old ID or update each affected link and Source Note target deliberately.

### Undo does not change Source Notes

Document Undo owns document mutations such as inserting a heading link or citation. Source Notes are a separate file authority saved atomically through their own controller. Creating or editing a Source Note is not merged into the document’s text Undo history.

### The same tag appears with different capitalization

Use `Research → Tags`, activate **Variants only**, and inspect exact uses. Calamus treats Unicode-normalized, whitespace-collapsed, case-insensitive variants as one logical identity and lets you review the impact before rewriting them.

## Research habits that scale

- Use stable Reference keys and avoid changing them after citations and notes accumulate.
- Capture locators at reading time.
- Keep quoted source text separate from your own Comment.
- Prefer a small controlled tag vocabulary.
- Add explicit heading IDs early for sections that will receive notes or links.
- Use Document Target for intended manuscript placement; use Tags for subject classification. They are not interchangeable.
- Run Authoring Bridge by heading while drafting and by Reference while checking source use.
- Run Broken Research Links and Research Check before every major export.
- Treat derived exports as disposable products. Edit the authorities, then regenerate the output.
- Keep the document and its `.source-notes.md` sidecar together when moving or backing up a project.

## Research glossary

- **Authority**: a file that owns data. The document owns prose and citations; `references.md` owns bibliographic records; the sidecar owns Source Notes.
- **Canonical key**: the primary stable key of a Reference.
- **Alias**: an alternative citation key resolving to a canonical Reference.
- **Citation cluster**: one Pandoc citation expression, possibly containing several keys, such as `[@ratzinger1968; @guardini1950]`.
- **Derived projection**: a read-only view calculated from authorities, such as Authoring Bridge.
- **Document Target**: a Source Note relationship to one explicit heading ID.
- **Explicit heading ID**: the identifier in a heading such as `{#method}`.
- **Locator**: page, chapter, section or paragraph information identifying a place in a source.
- **Sidecar**: a transparent companion file associated with one document.
- **Stable ID**: an identity that does not depend on row order or visible text, such as a Source Note ID.
- **Stale snapshot**: a derived result calculated before an authority changed; it must be refreshed before navigation.


## A practical Research workflow

Example project:

- document: `~/Documents/Book/Chapter-01.md`
- global References authority: `$XDG_DATA_HOME/calamus/research/references.md`
- document Source Notes authority: `~/Documents/Book/Chapter-01.md.source-notes.md`

A typical path is:

1. Save the document as `~/Documents/Book/Chapter-01.md`.
2. Open `Research → References` and add a source with a stable key such as `ratzinger1968`.
3. Open `Research → Source Notes` and add a note linked to `ratzinger1968` and, when useful, to a document heading such as `#introduction`.
4. Select a useful sentence and use `Research → Create Source Note from Selection…` to turn it into a prefilled Source Note.
5. Use `Research → Insert Link to Heading…` to create a Markdown link to one explicit `{#heading-id}`.
6. Open `Research → Authoring Bridge` to inspect navigable citations, Source Notes, heading links and broken Research links derived from the current files.
7. Place the cursor where the citation belongs and use `Research → Quick Cite…` to insert `[@ratzinger1968]`.
8. Use **Related References…** in the References client when two works have an explicit scholarly relationship.
9. Use `Research → Reference Sets` to assemble static working lists such as `Core sources` or `Check before submission`.
10. Use `Research → Research Check…` before exporting to find missing citation keys, broken targets, asymmetric Related References, invalid set members, duplicate aliases and tag-identity collisions.
11. Use `Research → Tags` to inspect, navigate, rename, merge, remove or normalize Research tags without changing the document text.
12. Use `Research → Import BibTeX/BibLaTeX…` when a trusted `.bib` library must be reviewed and merged into `references.md`.
13. Use `Research → Export References as BibTeX/BibLaTeX…` to create a derived `.bib` file for another bibliographic tool.
14. Use `Research → Export Research Apparatus…` to create a derived Markdown dossier or one of its component reports.

The document, `references.md` and the document Source Notes sidecar remain separate authorities. Derived reports are not authorities and may be regenerated.

## Research Panel

`Research → Research Panel` opens the right-side Research workspace. Its selector follows the same learning order as the Research menu: **Clip Collection**, **Scratchpad**, **References**, **Reference Sets**, **Source Notes** and **Authoring Bridge**. The selector opens **below** the control as a visible, scrollable list and begins from the first client, so earlier choices remain visible even after a later client has been used. Selecting a row immediately changes the active Research client and closes the selector. The User Guide presents these clients in the same order, so the path learned in Help is the path encountered in the application.

Practical example: while editing `Chapter-01.md`, open the Research Panel and move from Clip Collection to Scratchpad before entering the bibliographic workflow. Clip Collection answers “what reusable text do I keep globally?”, while Scratchpad answers “what provisional thinking belongs to this document?”. References and Source Notes come later because they introduce sources and source-grounded evidence.


## Clip Collection

`Research → Clip Collection` opens the global library of short text fragments that can be reused in different documents. Typical clips are a Markdown outline, a recurring formula, a standard reply, a checklist, a signature, a quotation layout or a pastoral refrain written by you.

Clip Collection is deliberately different from the other Research clients:

- it is **global**, not owned by the current document;
- it stores reusable text, not unfinished project-specific thinking;
- it has no bibliographic meaning;
- it is not a second Scratchpad;
- it does not monitor or remember the system clipboard;
- it does not create tags, concepts, folders or automatic relations.

### Where clips are stored

The canonical authority is the readable UTF-8 Markdown file:

    ~/.config/calamus/clips.md

W95 uses **Calamus Clip Collection v2**. Every clip has a stable technical ID, a title, an optional mnemonic shortcut, creation and update timestamps, and a Markdown body. Calamus can migrate the earlier v1 Markdown format and the legacy `clips.json` source. The old JSON file is retained as a read-only backup and is never used as a second authority.

Use **Manage → Open Clip File** to open `clips.md` in the system’s default text editor. Use **Refresh** after editing it outside Calamus. Before every write, Calamus checks whether the file changed externally. A stale authority is never overwritten silently: refresh the external version, inspect it and repeat the intended operation.

The collection has an explicit maximum of 200 records. Calamus does not silently discard older clips when the limit is reached.

### Stable ID, title and mnemonic shortcut

A clip has three different identifiers:

- **Stable ID** — an internal value such as `clip-0123456789abcdef0123456789abcdef`. It remains the identity even when the title or shortcut changes.
- **Title** — the readable description displayed in the list.
- **Shortcut** — one optional mnemonic such as `firma`, `intro-articolo` or `risposta-ringraziamento`.

A mnemonic shortcut is **not a tag**. A clip has at most one shortcut; the shortcut is globally unique; it does not classify clips or create a taxonomy. It is simply a short address used to retrieve the correct body quickly.

Shortcut rules:

- 1–32 characters;
- lowercase letters, numbers, `-` and `_`;
- the first character must be a letter or number;
- comparison is case-insensitive;
- two clips cannot share the same shortcut;
- Duplicate deliberately leaves the new shortcut empty so that the original remains unambiguous.

### Understand the list and detail view

Each row shows:

1. the shortcut, or `—` if none exists;
2. the title;
3. the first non-empty line of the body as an ellipsized preview.

The lower detail area shows the complete selected body without editing it. Use **Edit** for changes. This separation prevents an accidental keystroke in the panel from rewriting the authority.

The Search field checks shortcut, title and body. Matching is deliberately simple and deterministic:

1. exact shortcut;
2. shortcut beginning with the query;
3. title beginning with the query;
4. shortcut containing the query;
5. title containing the query;
6. body containing the query.

The selected clip is tracked by stable ID, not by row number or displayed text. Refreshing or filtering therefore does not silently redirect an action to a different clip.

### Create a new clip

Press **New** and enter:

- **Title** — a concise readable name;
- **Shortcut** — optional and unique;
- **Body** — the reusable text.

The body cannot be empty. The dialog validates the shortcut and the special cursor marker before any file is changed. Cancel leaves both the authority and the document untouched.

When the same body already exists, Calamus warns you and offers three explicit choices:

- select the existing clip;
- create another clip deliberately;
- cancel.

A duplicate body is therefore possible, but never created without your knowledge.

### Capture selected document text

Select non-empty text in the editor and press **Capture Selection**. Calamus opens the New Clip dialog with that selection copied into the Body. You can edit the title, add a shortcut and review the body before saving.

Capture never deletes or changes the selected document text. With no selection, the command stops with an error instead of creating an empty clip.

### Edit, duplicate and delete

Use **Manage → Edit** to change the title, shortcut or body. The stable ID and creation timestamp remain unchanged; the update timestamp changes only after a successful atomic save.

Use **Manage → Duplicate** when you intentionally need a second independent record. Calamus asks you to confirm the duplicate body, creates a new stable ID and leaves the shortcut empty.

Use **Manage → Delete** to remove the selected clip permanently. Delete always asks for confirmation. Cancelling changes nothing. After deletion, the nearest remaining clip is selected by ID.

### Insert a selected clip from the panel

Place the editor cursor at the destination, select a clip and press **Insert**, press Enter on the selected row, or double-click it. The Body enters the real document through Calamus’s normal document-editing gateway:

- the document becomes modified;
- insertion is one coherent Undo step;
- the clip remains in the collection;
- `clips.md` is not rewritten merely because the body was inserted.

If `clips.md` changed after the panel loaded it, insertion stops rather than using an obsolete body. Refresh and choose the clip again.

### Insert Clip quickly with Ctrl+Alt+K

Choose `Research → Insert Clip…` or press `Ctrl+Alt+K` from the editor. A compact keyboard-first selector opens with Search focused.

At an empty query it is also the complete **list of clip shortcuts**. Rows show shortcut, title and body preview. Clips with shortcuts appear first in shortcut order; clips without shortcuts follow in title order.

Keyboard operation:

- type a shortcut, title word or body fragment;
- use Up and Down to change selection;
- press Enter to insert;
- double-click a row to insert;
- press Escape to cancel.

Even an exact shortcut match requires Enter or an explicit activation. Merely typing a shortcut never changes the document. After insertion, focus returns to the editor and one Undo removes the complete inserted body.

### Position the caret with {{cursor}}

A clip body may contain the literal marker `{{cursor}}` once:

```text
Gentile {{cursor}},

la ringrazio per la sua comunicazione.
```

When the clip is inserted, the marker is removed and the caret is placed at that position. If the marker is absent, the caret is placed after the inserted text. More than one marker is invalid and must be corrected before insertion.

`{{cursor}}` is only a deterministic position marker. It does not execute code, read the clipboard, insert another clip or evaluate an expression. The insertion mark is placed explicitly at that position after the grouped edit; if the marker is first, last or in the middle, the caret must remain there rather than falling back to the end of the inserted body.

### Copy Body without changing the document

Press **Copy Body** to place the selected body on the system clipboard. This is an explicit one-time copy. Calamus does not watch the clipboard, build clipboard history or capture later clipboard changes.

### Numeric quick slots 1–9

The compatibility shortcuts `Ctrl+Alt+1` through `Ctrl+Alt+9` insert the first nine records in the canonical order of `clips.md`. These are **numeric quick slots**, not stable identities and not mnemonic shortcuts.

Use them only for a small, deliberately ordered group of clips. Reordering or deleting records can change a numeric slot. For dependable retrieval by name, use `Ctrl+Alt+K` and the clip’s mnemonic shortcut.

### Refresh and external changes

**Manage → Refresh** performs a real disk reload. It does not merely redraw cached rows. Calamus attempts to preserve the selection by stable ID.

Every mutation follows a persist-first transaction:

1. validate the complete candidate collection;
2. verify the authority revision;
3. write a unique temporary file in the same directory;
4. flush and `fsync` it;
5. verify the revision again;
6. atomically replace `clips.md`;
7. update the panel only after disk success.

If parsing, validation, writing or replacement fails, the previous file, the runtime list and the active document remain unchanged.

### A first five-minute exercise

1. Open `Research → Clip Collection`.
2. Press **New**.
3. Title the clip `Three-part outline`.
4. Give it the shortcut `outline3`.
5. Enter:

```text
## First part

## Second part

## Third part

{{cursor}}
```

6. Save it.
7. Place the cursor in a disposable document.
8. Press `Ctrl+Alt+K`, type `outline3`, then press Enter.
9. Verify that the outline appears and the caret is at the marker position.
10. Press `Ctrl+Z` once and verify that the complete insertion is undone.
11. Return to Clip Collection, use **Copy Body**, then use **Refresh**.

### Common mistakes and recovery

#### “I used several words as shortcuts to classify a clip”

Use one concise mnemonic address. Clip shortcuts are not tags. W95 intentionally has no clip taxonomy.

#### “Ctrl+Alt+1 inserted a different clip than before”

Numeric quick slots follow file order. Use `Ctrl+Alt+K` and a stable mnemonic shortcut when identity matters.

#### “Capture created nothing”

Select non-empty document text first. Capture refuses an empty selection.

#### “Insert says the collection changed outside Calamus”

Press Refresh, inspect the current external version, select the clip again and repeat the insertion. Calamus does not guess which version should win.

#### “A clip cannot be inserted because of {{cursor}}”

Edit it and retain zero or one marker. Two or more markers are invalid.

#### “I need notes tied to one section of this document”

Use Scratchpad. Clip Collection is global reusable text and must not become a second document notebook.

### Keep the collection deliberate

Use clear titles and memorable shortcuts, remove obsolete duplicates and prefer one reliable clip over many nearly identical variants. When material becomes project-specific reasoning, move it into the appropriate document’s Scratchpad. When it represents evidence from a source, create a Source Note instead.

## Scratchpad

`Research → Scratchpad` or `Ctrl+Alt+S` opens the structured notebook belonging to the current saved document. The current implementation is **Scratchpad Basic**: it is intentionally small, explicit and file-based. Its purpose is to make the distance between a passing thought and finished manuscript text manageable.

Scratchpad is not a miniature database and not a second document editor. It is the place where you can safely hold material that is useful but not yet ready to remain in the manuscript: an idea, a rough paragraph, a question expressed as a Note, or a concrete writing Task.

### Start with the mental model, not with the buttons

Before creating an entry, ask what kind of object you actually have:

| What you have | Where it belongs | Example |
|---|---|---|
| Reusable text independent of the current document | Clip Collection | A standard Markdown outline |
| Provisional thinking for the current document | Scratchpad | “The conclusion should return to the image of memory” |
| Material taken from a source | Source Notes | A quotation with page number |
| Bibliographic identity of a work | References | Author, title, year and citation key |
| Text already accepted as part of the manuscript | The document | A finished paragraph in the chapter |

This distinction prevents the most common learning problem: using every Research client as if it were a generic notes box.

### First guided exercise: ten minutes from an empty document

Use a disposable document copy for this exercise.

1. Create and save `Scratchpad-Practice.md`. Scratchpad cannot own persistent entries until the document has a real path.
2. Type the following structure in the document. The four leading spaces are only formatting in this guide; in the document the headings begin at the left margin:

        # Tradition and Memory

        ## Introduction {#introduction}

        ## Historical roots {#historical-roots}

        ## Pastoral consequences {#pastoral-consequences}

        ## Conclusion {#conclusion}

3. Place the cursor under `Introduction`.
4. Open `Research → Scratchpad` or press `Ctrl+Alt+S`.
5. Press **New** and create:
   - Type: `Idea`
   - Status: `Inbox`
   - Title: `Open with lived memory`
   - Body: `Begin from the way a community remembers before explaining the theory.`
   - Tag: `introduction`
   - Section: `#introduction`
6. Save the entry. It now exists in `Scratchpad-Practice.md.scratchpad.md`, not in the document text.
7. Select the unfinished sentence `Memory is not only...` in the document and use `Research → Capture Selection in Scratchpad…` or `Ctrl+Alt+Shift+S`.
8. Give the captured entry the title `Rough opening sentence`, choose Type `Draft`, link it to `#introduction`, and save it.
9. Use `Research → Show Scratchpad for Current Section`. Only entries linked to `#introduction` should remain visible.
10. Select `Rough opening sentence`, improve its Body, then use **Insert**. The Body enters the document at the cursor, but the Scratchpad Entry remains available for review.
11. Undo the document insertion once. The entry remains in Scratchpad because document Undo does not rewrite the sidecar.
12. Mark the idea `Active`, then later `Resolved` when the introduction no longer depends on it.

At the end of this exercise you have learned the complete basic cycle: **capture → clarify → connect → retrieve → insert → resolve**.

### Where the data lives

Scratchpad belongs to one saved document. For example:

    article.md
    article.md.scratchpad.md

The sidecar is readable UTF-8 Markdown. There is no hidden database, global Scratchpad library, background index or knowledge graph. A backup of the document should include its `.scratchpad.md` companion. Writing Workspace operations Rename, Duplicate and Move to Trash carry the managed sidecar with the document.

A practical consequence follows: two documents with the same title in different folders have different Scratchpads because ownership is determined by the complete document path.

### Understand the four types through examples

The type describes what the entry **is**, not how urgent it feels.

- **Note** — an observation or question that does not yet demand a direction. Example: `Check whether “memory” is being used historically or theologically.`
- **Idea** — a possible direction for the argument. Example: `Contrast institutional memory with living tradition in the second section.`
- **Draft** — prose already taking shape but not yet accepted into the manuscript. Example: a rough transition paragraph between two headings.
- **Task** — a concrete action required by the document. Example: `Verify the page locator for the Newman quotation.`

Do not create artificial types by encoding them in punctuation or titles. A question can be a Note; a concept under development can be an Idea. Tags and titles provide the vocabulary without enlarging the data model.

### Understand the four states as a simple lifecycle

The status answers “where is this entry in my work?”

- **Inbox** — captured quickly and not yet reviewed.
- **Active** — deliberately part of the current writing process.
- **Resolved** — dealt with, incorporated or consciously rejected, but still worth retaining.
- **Archived** — removed from ordinary working views without deletion.

A useful daily habit is:

1. capture freely into Inbox while writing;
2. review Inbox at the end of the session;
3. promote only useful entries to Active;
4. mark completed decisions Resolved;
5. archive material that should remain available but no longer occupy the working list.

Scratchpad is not a task manager: it has no priorities, due dates, reminders or notifications.

### Three ways to create an entry

#### New

Press **New** in the Scratchpad client, or press `Insert` while the entry list owns focus. Use this when the thought does not already exist as selected document text.

Example: while reading the Introduction, you realise that the conclusion should echo its opening image. Create an Idea titled `Return to opening image`, link it to both `#introduction` and `#conclusion`, and tag it `structure`.

#### Capture Selection in Scratchpad

Select text in the document and choose `Research → Capture Selection in Scratchpad…`, or press `Ctrl+Alt+Shift+S`. Calamus copies the selection into a new entry Body. It does not delete or alter the selected document text.

Use capture when a paragraph interrupts the current flow but may still contain something worth developing. After capture, decide explicitly whether the original paragraph should remain, be revised or be removed through normal document editing.

#### New Scratchpad Entry for Current Section

Place the cursor inside a heading that has an explicit Pandoc identifier and choose `Research → New Scratchpad Entry for Current Section…`. The dialog opens with that section already selected.

A stable heading looks like this in the document:

    ## Tradition and memory {#tradition-and-memory}

Calamus stores `#tradition-and-memory`. It does not store a line number or guess a section from similar wording.

### Titles, Body, tags and section links

A useful entry usually has four layers:

- **Title** — short enough to recognise in a list;
- **Body** — the actual thought, draft or instruction;
- **Tags** — manual terms for finding related entries;
- **Sections** — explicit locations in the current document where the entry matters.

Example:

- Title: `Distinguish memory from nostalgia`
- Type: `Idea`
- Status: `Active`
- Tags: `memory`, `definition`, `chapter-2`
- Sections: `#historical-roots`, `#pastoral-consequences`
- Body: `Define memory as a living reception of the past; reserve nostalgia for idealising a past that no longer challenges the present.`

Tags are flat and manual. Their spelling is preserved. Calamus does not invent synonyms, infer concepts or generate a taxonomy. Prefer a small stable vocabulary over many nearly identical forms.

A single entry may point to several headings. **Open Section** navigates to a selected target. `Research → Show Scratchpad for Current Section` filters the list to the section under the cursor. Press **All** to return to the complete list.

When a target is missing or ambiguous, Calamus reports the problem rather than guessing. Repair the heading ID or edit the entry’s section links explicitly.

### Finding an entry without remembering where you put it

The search field checks stable ID, title, Body, tags and section targets. Combine it with Type, Status, Tag and Current Section filters.

Useful retrieval patterns:

- show `Draft` + `Active` to find prose ready for another revision;
- show `Task` + `Inbox` at the end of the day to triage unfinished actions;
- choose tag `conclusion` to collect all provisional material for the ending;
- place the cursor in a section and use **Show Scratchpad for Current Section** to reduce the list to the local context;
- choose **Current work** to hide Archived entries without deleting them.

When a result seems missing, clear the search, press **All**, remove Type/Status/Tag filters and press **Refresh**. Most “lost entry” cases are active filters, not data loss.

### From provisional material to manuscript text

Select an entry and use:

- **Insert** to place its Body at the current cursor through Calamus’s normal document-editing gateway;
- **Copy** to place the Body on the clipboard without changing the document.

Insert participates in Undo and marks the document modified. It does **not** automatically delete, archive or resolve the entry. This is deliberate: inserting prose and deciding that an idea is finished are different decisions.

A safe sequence is:

1. open the destination section;
2. reread the surrounding paragraph;
3. insert or copy the Body;
4. revise the document text in context;
5. return to Scratchpad;
6. mark the entry Resolved only when its role is genuinely complete.

### Refresh and changes made outside Calamus

Press **Refresh** or `F5` when the sidecar may have changed outside the current view. Refresh reloads the file from disk; it is not a save command.

Before every Scratchpad write, Calamus checks whether the sidecar changed after it was loaded. A stale conflict offers **Reload**, **Overwrite** or **Cancel**:

- choose **Reload** when the external version is authoritative;
- choose **Overwrite** only after deliberately deciding that the current Calamus state should replace it;
- choose **Cancel** when you need to inspect both versions first.

The ordinary safe choice is Reload, followed by reapplying the intended edit. Writes use a staged file, flush, `fsync` and atomic replacement. Malformed data remains visible but read-only until corrected; Calamus does not silently “repair” an authority.

### Archive, restore and delete

**Archive** removes an entry from ordinary work without destroying it. Applying Archive to an already archived entry restores it as Active.

**Delete** or the `Delete` key asks for confirmation and permanently removes the selected entry from the sidecar. Cancelling the confirmation changes nothing. Prefer Archive when you are uncertain; use Delete only for material you truly do not want to retain.

### Three realistic working scenarios

#### Scenario A — A paragraph is interesting but disrupts the argument

Capture it as a Draft, give it a precise title, link it to the section where it might belong, then remove or rewrite the original through normal document editing. Later filter Active Drafts and decide whether to insert the revised Body.

#### Scenario B — An idea concerns two distant sections

Create one Idea and link it to both headings. Do not duplicate it. From either section, **Show Scratchpad for Current Section** makes the shared entry visible; **Open Section** lets you move between its targets.

#### Scenario C — You discover work that must be done before publication

Create a Task such as `Check all page locators in section 3`, tag it `verification`, and leave it Active. When the checks are complete, mark it Resolved. Use Scratchpad for the writing obligation; keep the source-specific evidence and locators in Source Notes.

### Common mistakes and recovery

#### “I created a source quotation in Scratchpad”

Create a Source Note with source key and locator. Scratchpad may hold your interpretation or writing plan, but it should not become the authority for source-grounded evidence.

#### “I cannot see an entry I know exists”

Press **All**, clear search and filters, include Archived entries, then press **Refresh**. Also confirm that the currently open document is the document that owns the sidecar.

#### “Show Scratchpad for Current Section returns nothing”

Confirm that the cursor is inside a heading with one explicit `{#id}` and that the entry links to the same ID. Similar heading text is not enough.

#### “Insert put text in the wrong place”

Undo the document edit, place the cursor correctly and insert again. The Scratchpad Entry remains untouched.

#### “I edited the sidecar externally and now Calamus warns about stale data”

Do not choose Overwrite reflexively. Reload, inspect the external change, and repeat the intended edit from the fresh state.

#### “The list is becoming overwhelming”

Review Inbox, resolve decisions, archive inactive material and stabilise your tags. The solution is a small maintenance rhythm, not more entry types or more hidden automation.

### A five-minute end-of-session review

Before closing a substantial writing session:

1. open Scratchpad;
2. filter `Inbox`;
3. give each useful capture a clear title and type;
4. link it to the relevant sections;
5. delete accidental captures only after confirmation;
6. move current work to Active;
7. mark completed items Resolved;
8. archive material that no longer needs attention;
9. press Refresh if another editor touched the sidecar;
10. save the document and back up both document and sidecar.

This small review is what turns Scratchpad from a pile of fragments into a dependable writing instrument.

### Current boundaries

Scratchpad Basic does not yet connect entries directly to References, Source Notes or other Scratchpad Entries. It does not provide relationship-oriented Show Uses, coordinated heading rename or advanced link repair. Those Scratchpad Full functions are not silently simulated in the current version.

W94 does, however, include Scratchpad tag fields in the derived Tags client. This permits exact-use navigation and controlled tag rename, merge, removal or normalization across References, current Source Notes and current Scratchpad without adding the richer relationships reserved for Scratchpad Full.

The dependable Basic contract remains document-local entries, explicit tags, explicit section links, transparent Markdown storage, safe refresh and controlled insertion into the manuscript.

### Quick reference after you have learned the workflow

- Open Scratchpad: `Ctrl+Alt+S`
- Capture selection: `Ctrl+Alt+Shift+S`
- New entry while list has focus: `Insert`
- Refresh from disk: `F5`
- Delete with confirmation: `Delete`
- Remove section filter: **All**
- Put Body in document: **Insert**
- Put Body on clipboard: **Copy**
- Hide without destroying: **Archive**
- Return an archived entry to work: **Archive** again

## References

`Research → References` manages the global Markdown reference library. References are stored in:

`$XDG_DATA_HOME/calamus/research/references.md`

When `XDG_DATA_HOME` is not set, the usual location is:

`~/.local/share/calamus/research/references.md`

Use stable, readable keys such as `guardini1950` or `ratzinger1968`. These keys are inserted into Pandoc-style citations and linked from Source Notes.

Practical example: add Joseph Ratzinger, *Introduction to Christianity*, key `ratzinger1968`, and tags `faith`, `theology`.


## Tags

`Research → Tags` opens a persistent client in the Research Panel. It answers three practical questions that the individual editors cannot answer on their own:

1. Which explicit tags currently exist?
2. Where is a selected tag actually used?
3. What will change if that tag is renamed, merged, removed or normalized?

Tags does **not** own a tag library. It derives a fresh inventory from the tag fields already stored in three readable Markdown authorities:

- the global References library;
- the current document Source Notes sidecar;
- the current document Scratchpad sidecar.

Closing the panel discards the projection. Opening it again or pressing **Refresh** rebuilds the list from those files. There is no `tags.db`, `tags.json`, background index, hidden taxonomy or cloud service.

### Tutorial: build a useful tag vocabulary from one article

This tutorial is a learning path, not a command reference. Work through it in order with a disposable article. The aim is to understand what Calamus is showing, make one safe correction, and finish with a small vocabulary that you could use every day.

#### Step 1 — Start with the mental model

A **tag** is an explicit label stored on a scholarly object. In W94, an object may be:

- a global Reference;
- a Source Note belonging to the current document;
- a Scratchpad entry belonging to the current document.

The manuscript itself is not a tag authority. If the word `tradition` appears twenty times in the prose, Tags does not count those twenty words. It counts only explicit `Tags:` fields. Use Find when you need occurrences in prose.

Calamus distinguishes three things:

1. **Logical tag** — the identity used for grouping, such as `tradition`.
2. **Stored variant** — the exact spelling found in a file, such as `Tradition`, ` tradition ` or `TRADITION`.
3. **Use** — one Reference, Source Note or Scratchpad entry that explicitly owns that tag.

The upper list shows logical tags. The lower list shows their exact uses. Nothing is rewritten merely because Calamus groups several spellings together.

#### Step 2 — Create one realistic research trail

Imagine an article titled *Tradition and ecclesial memory*. Give the article these headings:

```markdown
# Tradition and ecclesial memory

## Introduction {#introduction}
## Historical witnesses {#historical-witnesses}
## Theological synthesis {#theological-synthesis}
## Conclusion {#conclusion}
```

Now create three related research objects:

1. In **References**, create `ratzinger1968`, title it *Introduction to Christianity*, and add `tradition, ecclesiology`.
2. In **Source Notes**, create a Comment linked to `ratzinger1968`, target `#theological-synthesis`, and add `Tradition, reception`.
3. In **Scratchpad**, create an Idea titled `Tradition as living memory`, link it to `#conclusion`, and add ` tradition , ecclesiology`.

You now have three authorities and four useful labels. One logical identity has three spellings. This is intentional: the example lets you see the difference between inventory and cleanup.

#### Step 3 — Open the complete A–Z inventory

Choose `Research → Tags`, then press **All tags A–Z**.

That button is the safe way back to the complete vocabulary. It performs four presentation-only resets:

- clears Search;
- selects **All authorities**;
- turns **Variants only** off;
- selects **Name (A–Z)**.

The status line explicitly says **All tags A–Z**. You should see `ecclesiology`, `reception` and `tradition` in alphabetical order. The list is derived; pressing the button never changes a Markdown file.

Select `tradition`. Its count should combine all three authorities. The row reports:

- **R** for References;
- **N** for Source Notes;
- **S** for Scratchpad.

The warning mark means that at least two exact spellings in this logical group differ. It is a request for review, not an automatic diagnosis that one spelling is wrong.

#### Step 4 — Read exact uses before changing anything

With `tradition` selected, read the lower list. It should identify:

- `ratzinger1968` and the Reference title;
- the Source Note ID and its text summary;
- the Scratchpad entry ID and title.

Each use also states the exact stored spelling. Select the Reference use and press **Open**. Calamus opens References and selects the stable key. Return to Tags and repeat with the Source Note and Scratchpad entry.

This round trip is important. Before changing a vocabulary, verify that the uses really express the same category. Two identical words can still mean different things in different contexts.

#### Step 5 — Learn Search without losing the inventory

Search for `ratzinger1968`. The result appears because owner identifiers are searchable. Search for `living memory`; the Scratchpad-owned tags appear because owner labels are searchable. Search for `trad` and the logical tag appears as a prefix match.

Clear Search manually, or press **All tags A–Z**. Exact tag-name matches rank before prefix matches; prefix matches rank before ordinary substring and owner-only matches. This ranking changes presentation only.

#### Step 6 — Learn scope with a question

Ask three different questions:

- “Which labels exist anywhere?” Choose **All authorities**.
- “How have I classified my bibliography?” Choose **References**.
- “Which labels belong only to the thinking work of this article?” Compare **Source Notes** and **Scratchpad**.

Scope also limits mutations. If **Source Notes** is selected, Remove or Rename does not touch References or Scratchpad. Always read the scope immediately before approving a preview.

#### Step 7 — Distinguish Normalize, Rename and Merge

These operations answer different scholarly questions.

**Normalize spelling** keeps one logical identity and chooses one display form. Example:

```text
Tradition
tradition
␠tradition␠
        ↓
tradition
```

**Rename** changes an identity to a new identity that does not yet exist. Example:

```text
reception → reception history
```

**Merge** combines a source identity with a target identity that already exists. Example:

```text
church tradition → tradition
```

A merge is not a spelling correction. It is an intellectual judgment that two categories should become one. Inspect all uses before approving it.

#### Step 8 — Perform one safe normalization

Press **All tags A–Z**, select `tradition`, then choose **Rename / Merge…**. Enter `tradition` as the target. Because the logical identity is unchanged, the dialog must say **Mode: Normalize spelling**.

Read the preview. It should list the exact number of changed References, Source Notes and Scratchpad entries. Confirm only when those counts match the uses you inspected. After success, press **Refresh**. The warning mark for `tradition` should disappear, while all three uses remain.

#### Step 9 — See stale detection protect your work

Prepare another operation but leave its preview open. In a text editor, change one selected authority and save it. Then return to Calamus and confirm.

Calamus should refuse the operation as stale. This is not a nuisance: the preview was calculated from an older snapshot. Press **Refresh**, inspect the new state and prepare the operation again. Calamus must never silently overwrite a change made after preview.

#### Step 10 — Understand rollback without testing a failure on real work

A mutation may involve three files. Calamus writes in a controlled order and compensates earlier writes if a later authority fails. The result dialog reports success, stale cancellation, controlled failure or manual recovery required. Do not repeat a failed operation blindly. Read the message, inspect the Markdown files and refresh.

The manuscript remains byte-identical throughout these operations. Tags changes explicit metadata authorities, never article prose, headings or citations.

#### Step 11 — Three daily workflows

**Morning orientation**

1. Open the article.
2. Choose Tags.
3. Press **All tags A–Z**.
4. Scan the vocabulary before creating new labels.
5. Search an existing term before inventing a synonym.

**During source work**

1. Add tags while creating a Reference or Source Note.
2. Return to Tags.
3. Search the new label.
4. Open its uses to verify ownership and spelling.

**End-of-session cleanup**

1. Enable **Variants only**.
2. Inspect one warning group at a time.
3. Normalize spelling when identity is already the same.
4. Merge only after reading every use.
5. Finish with **All tags A–Z** and confirm that the vocabulary remains understandable.

#### Step 12 — A good stopping rule

Do not try to perfect the entire vocabulary in one session. Stop when:

- every new label has a clear retrieval purpose;
- accidental spelling variants are resolved;
- distinct concepts remain distinct;
- the article, References and sidecars still open normally;
- the A–Z list is short enough to scan and specific enough to be useful.

A useful tag system is not the one with the most labels. It is the one whose labels help you recover sources, notes and ideas without requiring you to remember where they were stored.

### First guided exercise

Use a disposable document while learning.

1. Open `Research → References` and create or edit one Reference. Add the tags `tradition` and `ecclesiology`.
2. Open `Research → Source Notes`, create a Comment and give it the tag `Tradition` with an uppercase `T`.
3. Open `Research → Scratchpad`, create an Idea and give it the tag `tradition`.
4. Choose `Research → Tags`.
5. Select the logical tag `tradition` in the upper list.
6. Read the lower **Uses** list. It should show the Reference, Source Note and Scratchpad entry separately, including the exact spelling stored by each authority.
7. Double-click one use, or select it and press **Open**. Calamus opens the owning client and selects the exact record.
8. Return to Tags and activate **Variants only**. The logical tag is shown because `tradition` and `Tradition` have different recorded display forms.

This exercise demonstrates the central rule: Tags groups equivalent identities for inspection, but it preserves exact stored spellings until you approve a mutation.

### Reading the tag list

The upper list contains one row per logical identity.

- **Tag** is the first-use canonical display spelling for the current scope.
- **Uses** is the total number of explicit occurrences.
- **R** counts Reference records.
- **N** counts Source Notes.
- **S** counts Scratchpad entries.
- The warning mark identifies a logical group whose spellings or whitespace need review.

Identity comparison uses Unicode NFC, collapsed whitespace and case-insensitive comparison. Therefore all of these belong to one logical group:

```text
Tradition
tradition
  TRADITION
```

This comparison never changes the authorities by itself.

### Search, scope, sorting and Variants only

The search field matches tag spellings and the labels of their exact owners. Searching for a Reference key, Source Note identifier or Scratchpad title can therefore reveal the tags used by that item.

The scope selector offers:

- **All authorities**;
- **References**;
- **Source Notes**;
- **Scratchpad**.

Scope affects both the inventory and any subsequent mutation. Before pressing Rename, Remove or Normalize, verify the selected scope. A Reference-only operation never writes the document sidecars; a Scratchpad-only operation never writes `references.md`.

The sorting selector offers:

- **Name (A–Z)** for the complete stable alphabetical vocabulary view;
- **Most used** for review work, placing the highest explicit-use counts first.

Press **All tags A–Z** whenever you want to clear Search and filters, return to all authorities, turn Variants only off and restore the complete alphabetical list.

When a search is active, exact tag-name matches appear before prefix matches, which appear before ordinary substring and owner-label matches. Sorting remains derived presentation only: Calamus never writes a preferred order into a hidden tag authority.

Use **Variants only** when cleaning spelling inconsistencies. Turn it off when browsing the full vocabulary.

### Show Uses and Open

Selecting a tag populates the lower list with exact uses. Each use contains:

- authority type;
- stable owner identifier;
- human-readable owner label;
- exact stored variant.

**Open** navigates by the stable identifier. It does not search for similar prose and does not infer a relationship. Opening a Reference selects its key; opening a Source Note selects its note ID; opening a Scratchpad use selects its entry ID.

### Rename or merge a tag

Use **Rename / Merge…** when the vocabulary should have one deliberate display form.

Example: `Tradition`, `tradition` and `traditions` should become `tradition`.

1. Select `Tradition`.
2. Verify the scope.
3. Press **Rename / Merge…**.
4. Enter `tradition`. The dialog states the operation mode before preview:
   - **Mode: Rename** when the target logical identity does not exist;
   - **Mode: Merge** when the target already exists;
   - **Mode: Normalize spelling** when source and target have the same logical identity.
5. Read the impact preview. Its title and confirmation button repeat the detected mode and list changed References, Source Notes, Scratchpad entries and total affected occurrences.
6. Apply only when both the mode and counts are expected.

Entering an already existing logical tag performs an explicit merge. Duplicate target tags inside the same record are removed. Only the logical variants of `Faith` become `doctrine` in a `Faith → doctrine` operation; unrelated tags and free text remain unchanged.

### Remove a tag

**Remove…** removes only the selected logical tag in the selected scope. It does not delete the owning Reference, Source Note or Scratchpad entry.

Before confirming, distinguish between a genuinely obsolete tag and a tag that is merely unused in the current document. References are global, so a tag may remain useful in another project.

### Normalize all variants

**Normalize All…** rewrites inconsistent variants to the first-use canonical display for every logical group in the selected scope. This is useful after importing or manually editing Markdown authorities.

Do not use Normalize All as a substitute for choosing good vocabulary. It fixes spelling identity and duplicate occurrences; it does not decide whether two different concepts are synonyms.

### Transaction safety

Every mutation follows the same controlled sequence:

1. load fresh authority snapshots;
2. prepare an immutable impact plan;
3. obtain explicit confirmation;
4. verify that selected files still match their preview tokens;
5. write atomically;
6. compensate earlier writes if a later authority fails;
7. refresh all three clients after success.

If any selected authority changes after preview, Calamus cancels the operation and writes nothing. If the final Scratchpad save fails after earlier writes, Calamus attempts to restore Source Notes and References in reverse order. A failed compensation is reported as manual recovery required rather than hidden.

### Tags versus Tag Integrity

`Research → Tags` is the normal W94 workspace: browse, filter, inspect exact uses, navigate and maintain tags across all three authorities.

`Research → Tag Integrity…` remains as the earlier compatibility dialog focused on References and current Source Notes. Prefer the Tags client for ordinary work and whenever Scratchpad must be included.

### What Tags deliberately does not do

Tags does not:

- create unused tags detached from records;
- add hidden tags to arbitrary manuscript selections;
- scan document prose for hashtags;
- infer synonyms, concepts or themes;
- build hierarchies or parent-child categories;
- assign semantic meaning to colours;
- rank or recommend tags;
- run a filesystem watcher or background index.

The Entry 061 idea **Add Tag to Selection** is therefore deferred until Calamus has an explicit, transparent document-level authority. W94 does not invent one merely to satisfy a menu label.

### Common mistakes

- **I expected text occurrences in the manuscript.** Tags shows explicit metadata fields, not word-search results. Use Find for document text.
- **The same idea appears as two rows.** The spellings are not logically equivalent; decide whether an explicit merge is scientifically correct.
- **One row has several spellings.** Use Variants only, inspect uses, then rename or normalize.
- **A document-local tag disappeared when I changed documents.** Source Notes and Scratchpad are document-local by design; References remain global.
- **A mutation was cancelled as stale.** Another process or manual edit changed an authority after preview. Refresh, inspect the new state and prepare a new plan.
- **Open does nothing.** The owner may have been removed after the projection was built. Press Refresh and retry.

### A small, sustainable tagging practice

Use short noun phrases, keep capitalization consistent, and prefer a limited vocabulary that helps retrieval. Review Variants only at the end of a writing session. Merge tags only when you can explain why they represent the same category; otherwise retain the distinction.

## Related References

Related References record an **explicit scholarly relationship between two References**. They are not recommendations and Calamus never infers them from titles, tags, authors or citation frequency. Use them when you can state a real reason why two works belong together: one replies to the other, develops the same argument, provides a contrasting position, or is a primary source for the same question.

The relation is stored transparently inside the two records in `references.md`:

    Related Keys: newman1870, delubac1949

The field owns only canonical Reference keys. It does not copy titles, authors or any other bibliographic data. A relation is **symmetric**: if `ratzinger1968` is related to `newman1870`, Calamus writes the relation in both records. Removing it removes both halves in the same atomic save.

### Add or remove Related References

1. Open `Research → References`.
2. Select the Reference that will be the subject, for example `ratzinger1968`.
3. Press **Related References…**.
4. Search or scroll through the library and select one or more explicit relations.
5. Press **Review Impact**.
6. Check the exact keys to add and remove and the number of Reference records that will change.
7. Press **Apply** only when the impact is correct.

Example: an article compares Ratzinger's account of tradition with Newman's development of doctrine. Select `ratzinger1968`, choose `newman1870`, review the impact, and apply. Opening either Reference later shows the same relation from the other side.

Calamus accepts an alias as input only when it resolves uniquely, then stores the canonical primary key. It refuses self-relations, missing keys, ambiguous aliases and duplicate identities. A one-sided relation introduced by an older file or manual editing is reported by `Research → Research Check…`; opening and confirming the Related References dialog repairs the pair explicitly rather than silently.

### Navigate Related References

Open `Research → Authoring Bridge`, choose **Related References**, and select a subject Reference. Each row represents one related canonical Reference. **Open** or double-click navigates directly to that known Reference; it does not perform a text search or create a graph. The projection is derived on demand from `references.md` and stores no background index or persistent count.

### Rename safety

Use `Research → Rename Reference Key…` rather than editing a key manually. The impact preview includes Related References and Reference Set memberships. A successful rename updates citations, Source Notes, Related Keys and Reference Sets as one controlled multi-authority operation. If any file changed after the preview or one save fails, Calamus stops and attempts to restore every authority already written.

## Reference Sets

Reference Sets are **static, named, ordered lists of existing References**. They help organise a concrete task without changing the bibliographic records themselves. Typical examples are `Core sources`, `Primary texts`, `Chapter 2 sources`, `Review before submission` or `Contrasting positions`.

Use a Related Reference when two works have an explicit relationship. Use a Reference Set when several works simply belong to the same working collection. Membership in a set does not imply that every member is related to every other member.

The canonical authority is the readable UTF-8 Markdown file:

`$XDG_DATA_HOME/calamus/research/reference-sets.md`

When `XDG_DATA_HOME` is not set, the usual path is:

`~/.local/share/calamus/research/reference-sets.md`

A file may look like this; the indented lines are literal Markdown content:

    # Calamus Reference Sets v1

    ## Core sources

    Description: Sources that carry the central argument of the article.

    - ratzinger1968
    - newman1870

    ## Historical background

    Description: Context for the first section.

    - delubac1949

The file stores only set names, descriptions, order and canonical member keys. Bibliographic metadata remains exclusively in `references.md`. Calamus does not add membership fields to each Reference and does not create a database, smart query, hierarchy or inferred collection.

### Create a Reference Set

1. Register the required sources in `Research → References`.
2. Open `Research → Reference Sets`.
3. Press **Add**.
4. Enter a clear name, for example `Core sources`.
5. Add a short description explaining the purpose of the set.
6. Select the member References. The filter helps when the library is long.
7. Press **Save**.
8. Select a member and press **Open Reference**, or double-click it, to open the canonical Reference record.

Example for a short article:

- `Core sources`: the two or three works on which the thesis directly depends;
- `Historical background`: sources used mainly in the contextual section;
- `Check before submission`: works whose citation, page locator or bibliographic data still needs verification.

A Reference may belong to several sets. The order of sets and members is preserved. Editing a set changes only `reference-sets.md`; deleting a set never deletes any Reference.

### Edit, delete and recover safely

Select a set and press **Edit** to change its name, description or members. Press **Delete** only after reading the confirmation; the dialog states how many members will be removed from the set while preserving the References.

If `reference-sets.md` changed outside Calamus after it was loaded, the save fails closed. Choose **Reload** to accept the external file, **Overwrite** only when you intentionally want the reviewed Calamus version, or **Cancel** to write nothing. A malformed set file is displayed as needing correction and remains read-only until its blocking diagnostics are fixed.

`Research → Research Check…` reports missing, ambiguous or alias-based set members. `Research → Rename Reference Key…` migrates set memberships to the new canonical key and shows the count in the impact preview. The set file never contains aliases after a successful UI save.

### Worked example: relate, collect and rename one source safely

Assume the library contains `ratzinger1968`, `newman1870` and `delubac1949`. The active article cites `[@newman1870, p. 55]`, and one Source Note also points to `newman1870`.

1. In References select `ratzinger1968`, press **Related References…**, select `newman1870`, and review the impact. The plan adds one relation and updates two Reference records.
2. Open `Research → Reference Sets`, add `Core sources`, describe it as `Primary works for the article`, and select all three keys.
3. Open `Research → Authoring Bridge`, choose **Related References**, select `ratzinger1968`, and open the `newman1870` row to verify direct navigation.
4. Choose `Research → Rename Reference Key…`, select `newman1870`, enter `newman1870-revised`, and preserve the old key as an alias.
5. The impact preview should report one active-document citation, one current Source Note, one Related-key occurrence and one Reference Set membership. Confirm only when those counts match the known authorities.
6. After the rename, verify the article contains `[@newman1870-revised, p. 55]`; the Source Note and `Core sources` use `newman1870-revised`; the two Related Keys remain symmetric; and `newman1870` appears only as an alias.
7. Run `Research → Research Check…`. There should be no missing, ambiguous, alias-based, self, duplicate or asymmetric relation/set issue.

This example shows why Related References and Reference Sets are different authorities but must participate in the same controlled key migration. Undoing only the document edit may restore the old citation spelling, but the preserved alias keeps it resolvable; it does not roll back the Reference, Source Note or Reference Set files.

## Source Notes

`Research → Source Notes` manages notes belonging to the current saved document. For:

`~/Documents/Book/Chapter-01.md`

Calamus stores the sidecar at:

`~/Documents/Book/Chapter-01.md.source-notes.md`

A Source Note may contain a quotation, paraphrase or comment, a Reference key, a page locator, tags and a target heading.

Practical example: create a quotation note linked to `ratzinger1968`, page `42`, target `#introduction`, with the tag `faith`.

## Create Source Note from Selection

`Research → Create Source Note from Selection…` bridges the editor and the current document Source Notes sidecar. The command requires a saved document and a non-empty selection.

Calamus captures the selected text and its document position before the modal dialog opens. A focus change cannot replace the captured source with another cursor position. Calamus then opens the normal Source Note dialog with:

- the selected document text already copied into **Text**;
- the currently selected Reference preselected when available;
- the current heading preselected as **Document Target** only when it has one explicit, unique Pandoc-compatible identifier such as `{#introduction}`.

The dialog remains authoritative for the final type, Reference, locator, tags, comment and target. Choosing **Cancel** writes nothing. Choosing **Save** persists through the existing atomic Source Notes store and stale-file conflict gate. The active document and `references.md` remain unchanged.

### Practical click-by-click example

1. Save `Chapter-01.md`.
2. Ensure the document contains `## Introduction {#introduction}`.
3. In `Research → References`, select `ratzinger1968` if the note should be linked to that source.
4. Select one sentence in the editor.
5. Open `Research → Create Source Note from Selection…`.
6. Confirm the selected sentence appears in **Text**.
7. Confirm the intended Reference and `#introduction` target, then add a locator or tags if needed.
8. Press **Save**.
9. Open `Research → Source Notes` and verify the new note is selected.

Stop and cancel when the prefilled text, Reference or target is not the expected one. An unsaved document, empty selection, malformed sidecar, missing Reference, missing target or stale external sidecar change fails closed.

## Insert Link to Heading

`Research → Insert Link to Heading…` inserts a standard Markdown internal link such as:

`[Introduction](#introduction)`

Only headings with an explicit, unique `{#heading-id}` are offered. Automatic heading slugs are not treated as stable Calamus targets. A selected single-line phrase becomes the default link text; with no selection, the heading title is proposed. The dialog shows the exact Markdown preview before insertion.

The command captures the document and replacement range before the modal dialog opens. Even if dialog focus moves the visible editor cursor, insertion still uses that captured range. It then replaces the selection or inserts at the captured cursor through the canonical document mutation gateway. It is one Undo unit, updates dirty state normally and never changes References or Source Notes.

### Practical click-by-click example

1. Add `## Method {#method}` to the document.
2. Select the words `see the method` or place the cursor where the link belongs.
3. Open `Research → Insert Link to Heading…`.
4. Choose `Method — #method`.
5. Review the link text and preview.
6. Press **Insert**.
7. Verify the editor contains `[see the method](#method)` or `[Method](#method)`.
8. Use Undo once and verify the exact pre-insertion document text returns; the menu callback itself does not display a separate success value.

The command refuses empty or multiline labels, missing or duplicate heading IDs, stale document snapshots and invalid targets.

## Authoring Bridge

`Research → Authoring Bridge` opens a read-only, on-demand projection of relationships already present in the current document, `references.md` and the document Source Notes sidecar. It creates no database, graph, cache, persisted count, watcher or background index.

The mode selector provides:

- **Backlinks by Reference**: Pandoc citation occurrences and Source Notes linked to one canonical Reference, including alias resolution;
- **Backlinks by Heading**: Markdown links and Source Notes targeting one explicit, unique heading ID;
- **Broken Research Links**: missing or ambiguous citation keys, heading links, Source Note References, Source Note targets and heading-ID diagnostics.

Each row stores the concrete source identity. **Open** or double-click selects the exact document range, or opens Source Notes and selects the known stable note ID. Calamus does not rerun a text search or scan the GTK list to rediscover the item.

### Practical click-by-click example

1. Open a saved document containing `[@ratzinger1968]`, `[Introduction](#introduction)` and at least one linked Source Note.
2. Open `Research → Authoring Bridge`.
3. Choose **Backlinks by Reference**, then select `ratzinger1968`.
4. Confirm the list shows the citation and linked Source Notes.
5. Activate the citation row and verify the exact citation is selected in the editor.
6. Return to Authoring Bridge, activate a Source Note row and verify Source Notes opens with that note selected.
7. Choose **Backlinks by Heading**, then `#introduction`; verify document links and targeted Source Notes.
8. Choose **Broken Research Links** and inspect any reported target or key.
9. After editing the document or Research files, press **Refresh** before opening an old result.

A projection is intentionally a snapshot. Refresh after document, References or Source Notes changes. If the document changes after it is built, opening an old document occurrence fails closed and asks for Refresh. The Authoring Bridge itself never mutates an authority.

## Quick Cite

`Research → Quick Cite…` inserts one or more Pandoc-style citation keys at the cursor.

Practical example: choose `ratzinger1968` and Calamus inserts:

`[@ratzinger1968]`

Choose two keys to obtain a combined citation such as:

`[@ratzinger1968; @guardini1950]`

Quick Cite does not format a final bibliography. Final citation styling belongs to Pandoc/citeproc or another external processor.

## Open Citation in References

Place the cursor inside or next to a citation and use `Research → Open Citation in References`. Calamus resolves the citation key and selects the matching Reference.

Practical example: with the cursor in `[@guardini1950]`, the command opens References and selects `guardini1950`.

## Research Check

`Research → Research Check…` performs a read-only consistency audit across the current document, References and Source Notes.

It may report missing citation keys, invalid aliases, broken Source Note targets, duplicate identifiers and logical tag collisions. It never silently rewrites the authorities.

Practical example: if References contains the tag `Faith` and a Source Note contains ` faith `, Research Check reports a tag-identity collision so that it can be reviewed in Tag Integrity.

## Tag Integrity

`Research → Tag Integrity…` builds a transient inventory from References and the current document Source Notes. It does not scan or rewrite the document text.

Logical identity uses Unicode NFC normalization, collapsed whitespace and case-insensitive comparison. Therefore `Faith`, `faith`, ` FAITH ` and Unicode-equivalent spellings are treated as variants of one logical tag.

Available operations:

- `Show Uses`: list the exact References and Source Notes that use the selected tag.
- `Rename / Merge…`: rename all selected variants in the chosen scope; if the target already exists, duplicates are merged.
- `Remove Everywhere…`: remove the selected logical tag in the chosen scope.
- `Normalize All…`: rewrite variant spellings to the first canonical display spelling.

Scopes are `References and Source Notes`, `References only`, and `Current Source Notes only`.

Practical example: the current Reference has tags `Faith`, `church history`, `temporary`; a Source Note has `FAITH`, `church history`, `temporary`. Select `Faith`, choose `Rename / Merge…`, enter `doctrine`, review the impact preview and confirm. Only the logical variants of `Faith` become `doctrine`; unrelated tags such as `church history` and `temporary` remain unchanged. The active document remains byte-identical.

The colour swatch is deterministic and derived from tag identity. It is presentation only: it is not stored in References or Source Notes and cannot create a colour-only tag.

### Relationship with the W94 Tags client

`Research → Tags` is the persistent W94 client for everyday tag inspection and maintenance. It adds search, authority filters, exact-use navigation, Scratchpad coverage, derived sorting, and explicit Rename/Merge/Normalize modes. The older `Research → Tag Integrity…` workflow remains available for compatibility. Both use the same logical-identity and transaction rules; neither creates a tag database or rewrites document prose.

## Import BibTeX/BibLaTeX

`Research → Import BibTeX/BibLaTeX…` imports selected entries from a local `.bib` file into the canonical References library:

`$XDG_DATA_HOME/calamus/research/references.md`

The `.bib` file is input only, never a second authority. Calamus asks for an explicit BibTeX or BibLaTeX mode, parses without writing, reports malformed or non-entry blocks, then opens **Review Entries**.

The review table has one transient decision per entry. Select a row and use the fixed **Choose one action** controls on the right:

- `Import`: add a new, non-colliding key.
- `Skip`: leave the existing library unchanged for that entry.
- `Replace existing`: replace the record with the same primary key.
- `Merge missing fields`: retain existing values and fill only missing data; tags are combined.
- `Import with new key`: create a deterministic unique key and keep the incoming record separate.

New references may start as `Import`; invalid entries are locked to `Skip`. A collision with different content has no implicit decision. Review Impact… remains disabled until every ambiguous collision has an explicit action. The right side shows **Current local reference** and **Incoming reference** so the choice is informed. Selection never changes data by itself.

### Practical click-by-click example

1. Open `Research → Import BibTeX/BibLaTeX…`.
2. Choose `~/Downloads/theology-library.bib`.
3. Choose `BibLaTeX` explicitly and press `Continue`.
4. In **Review Entries**, select the colliding row `ratzinger1968`.
5. Compare the current and incoming summaries. If the local title must remain but the incoming record supplies a missing DOI, activate `Merge missing fields`.
6. Select the new row `guardini1950`; leave `Import` active.
7. Confirm malformed entries remain `Skip` and their action controls are disabled.
8. Confirm the unresolved-collision message has disappeared and `Review Impact…` is enabled.
9. Press `Review Impact…` and check the exact Import, Replace, Merge, Re-keyed and Skip counts.
10. Confirm that only `references.md` will change, then press `Apply Import`.
11. Open `Research → References` and verify the imported and merged records.

**STOP without applying** when the current/incoming summaries do not match the selected row, an invalid entry becomes importable, `Review Impact…` is enabled while a collision is unresolved, the impact counts differ from the selected decisions, or the dialog stops responding.

Parser diagnostics remain visible. Duplicate keys, duplicate fields and malformed blocks are never handled by silent “last value wins”. `@string` values may be consumed to resolve entry data and are reported as a lossy conversion. `@comment` and `@preamble` blocks are reported but not imported because they have no valid owner in a Reference record. Unsupported scalar fields are preserved in `extra_fields` when possible.

If the `.bib` source or `references.md` changes after preview, Calamus fails closed and writes nothing. The import never modifies the `.bib` source, the active document or Source Notes.

## Export References as BibTeX/BibLaTeX

`Research → Export References as BibTeX/BibLaTeX…` creates a derived `.bib` representation of the global References library. It does not alter `references.md`.

Practical example: choose `BibLaTeX`, inspect the read-only preview and representability warnings, then save to:

`~/Documents/Book/Exports/calamus-references.bib`

The export is deterministic UTF-8 with a fixed field order. Unknown scalar fields are emitted when their names are representable. Calamus reports lossy type or field mappings, does not recreate original `@string`, `@comment` or `@preamble` factoring, and does not claim byte-for-byte round trip. BibTeX and BibLaTeX are explicit modes because fields such as `date`, `journaltitle`, `location` and `langid` have different conventions.

The destination cannot replace the canonical `references.md` authority. If References changes after the preview, no `.bib` output is written.

## Export Research Apparatus

`Research → Export Research Apparatus…` first asks which product to create, then opens a standard Markdown save dialog.

Products:

- Source Notes in Document Order
- Source Notes by Reference
- Bibliography of Cited Sources
- Annotated Bibliography
- Complete Research Dossier

Practical example: with `Chapter-01.md` open, select `Complete Research Dossier`, choose:

`~/Documents/Book/Exports/Chapter-01-research-dossier.md`

The output is derived Markdown. Calamus refuses to overwrite the current document, `references.md` or the current Source Notes sidecar.

## Writing Workspace

Use `File → Writing Workspace` commands to choose a folder containing `.txt` and `.md` files. The Workspace supports opening, creating, renaming, duplicating and moving one item to the system Trash. Managed Source Notes sidecars follow the document operations that own them.

Practical example: choose `~/Documents/Book` as the Workspace, create `Chapter-02.md`, and keep chapter files and their sidecars together.


## References tutorial: from an empty library to a checked article

This tutorial assumes that you have never used a bibliography manager. It builds a small transparent library, cites it in a document, relates two works, creates a working set and finishes with an integrity check. Follow the stages in order the first time.

### Stage R1 — Understand the three things that look similar

A **Reference** is one bibliographic record stored in the global `references.md` library. A **citation** is a short marker in a document, such as `[@ratzinger1968, p. 42]`. A **Source Note** is a separate note owned by the current document and linked to a Reference key.

The citation key is the stable identifier that joins these objects. Store it without `@` in References:

```text
ratzinger1968
```

Use it with `@` only inside a citation:

```markdown
[@ratzinger1968, p. 42]
```

Calamus keeps `references.md` as the only canonical bibliography. Exported `.bib`, Markdown or plain-text bibliographies are derived products, not second libraries.

### Stage R2 — Open References and add a book

1. Choose `Research → References`.
2. Press `Add`.
3. In **Basic**, enter:

```text
Key: ratzinger1968
Type: book
Authors: Ratzinger, Joseph
Title: Introduction to Christianity
Year / Date: 1968
Tags: faith, theology, christology
```

4. Add an annotation such as:

```text
Central source for the relation between faith, confession and understanding.
```

5. In **Publication**, add only metadata you actually know, for example:

```text
Publisher: Burns & Oates
Location: London
Language: en
```

6. Press `Save`.

Do not invent missing DOI, ISBN, page or publisher data. An incomplete accurate record is better than a complete false one.

### Stage R3 — Add an article and a chapter

For a journal article, use separate fields for the article and the journal:

```text
Key: rossi2024
Type: article
Authors: Rossi, Maria
Title: Tradition and Renewal in Contemporary Theology
Year / Date: 2024
Container Title: Journal of Theological Studies
Volume: 18
Issue: 2
Pages: 115-138
Tags: tradition, renewal
```

For a chapter in an edited book:

```text
Key: bianchi2022
Type: chapter
Authors: Bianchi, Luca
Title: Scripture and Tradition
Year / Date: 2022
Editors: Verdi, Paolo; Neri, Anna
Container Title: Sources of Christian Theology
Publisher: Academic Press
Location: Rome
Pages: 81-104
```

Separate multiple authors or editors with semicolons. Do not put the journal or book title into the chapter/article `Title` field.

### Stage R4 — Choose a stable citation key

The `Suggest` button can propose a key from author and year. Review the proposal before saving.

Good keys are short, readable and stable:

```text
newman1870
lubac1949
rossi2024a
rossi2024b
```

Avoid temporary names such as `book1`, `new-source` or `final-article`. Do not change a key merely to improve spelling after it has been used in documents.

### Stage R5 — Search and edit without changing identity

Use **Search references…** to filter the in-memory projection by key, author, title, year, tags and other recorded fields. Searching never rewrites `references.md`.

Select a row and press `Edit` to correct title, author, publication details, identifiers, tags, annotation or local file path. The normal editor deliberately does not rename the citation key.

For a key change use only `Research → Rename Reference Key…`. Its impact preview can migrate:

- the active document citation;
- current Source Notes;
- Related Keys;
- Reference Set memberships.

Leave **Preserve the old key as an alias** enabled when older documents may still contain the old spelling.

### Stage R6 — Insert citations with Quick Cite

1. Place the cursor in the document.
2. Choose `Research → Quick Cite…` or press `Ctrl+Alt+Q`.
3. Select a Reference.
4. Add a locator when needed.

Examples:

```markdown
[@ratzinger1968]
[@ratzinger1968, p. 42]
[@newman1870, pp. 55-57]
[@ratzinger1968, p. 42; @newman1870, pp. 55-57]
```

Use `Research → Open Citation in References` when the cursor is in a citation. Calamus resolves aliases to the canonical Reference rather than creating a duplicate.

### Stage R7 — Create an explicit Related Reference

Use Related References only when two works have a real scholarly relationship: response, development, contrast, source or direct thematic dependence.

1. Select `ratzinger1968`.
2. Press `Related References…`.
3. Select `newman1870`.
4. Press `Review Impact`.
5. Verify:

```text
Add: newman1870
Remove: none
Reference records updated: 2
```

6. Press `Apply`.

The relation is symmetric. Opening `newman1870` must show `ratzinger1968` as related. A Reference cannot relate to itself.

### Stage R8 — Create a Reference Set for one task

A Reference Set is a static ordered list. It does not copy bibliographic metadata and deleting the set never deletes a Reference.

1. Choose `Research → Reference Sets`.
2. Press `Add`.
3. Enter exactly:

```text
Name: Core sources
Description: Primary works for the article.
```

4. Select `ratzinger1968`, `newman1870` and `delubac1949`.
5. Press `Save`.

Reference Set names are **case-sensitive and preserved exactly**. `Core sources` and `Core Sources` are different visible spellings even though Calamus rejects them as duplicate logical identities. Copy a validation or project name exactly when exact output matters.

Use a Related Reference for an explicit relation between two works. Use a Reference Set for a working collection such as `Chapter 2 sources`, `Primary texts` or `Check before submission`.

### Stage R9 — Rename a key across four authorities

Suppose `newman1870` must become `newman1870-revised`.

1. Select `newman1870` in References.
2. Choose `Research → Rename Reference Key…`.
3. Enter `newman1870-revised`.
4. Keep **Preserve the old key as an alias** enabled.
5. Press `Preview Impact`.
6. Confirm the exact counts for the document, Source Notes, Related Keys and Reference Sets.
7. Press `Rename Key` only when the preview matches the intended scope.

After a successful rename, verify all four places. Do not perform a manual search-and-replace in `references.md` while Calamus is open.

### Stage R10 — Import and export without creating a second authority

`Research → Import BibTeX/BibLaTeX…` reads a local `.bib` file, shows collisions and asks for an explicit action. `Research → Export References as BibTeX/BibLaTeX…` creates a derived file.

The ownership rule remains:

```text
references.md = canonical library
.bib / .md / .txt = import input or derived export
```

Correct the library in Calamus, then regenerate exports. Do not edit an exported `.bib` and assume the change has returned to `references.md`.

### Stage R11 — Delete safely

Before deleting a Reference:

1. inspect its uses;
2. inspect current Source Notes;
3. inspect Related References;
4. inspect Reference Sets;
5. run `Research → Research Check…`.

Deleting a bibliographic record does not make an existing citation valid. A remaining citation to a deleted key becomes an integrity error.

### Stage R12 — Complete worked example

Library:

```text
ratzinger1968
newman1870
delubac1949
```

Related pair:

```text
ratzinger1968 ↔ newman1870
```

Static set:

```text
Core sources
- ratzinger1968
- newman1870
- delubac1949
```

Article paragraph:

```markdown
# Tradition and Renewal

Tradition is not a mechanical repetition of the past
[@ratzinger1968, p. 42]. Newman helps explain how development can
preserve doctrinal identity [@newman1870, p. 55]. The ecclesial
context prevents this continuity from becoming a purely individual
process [@delubac1949, pp. 101-103].
```

Finish by opening Authoring Bridge, checking the Related pair, reopening `Core sources`, running Research Check and exporting only after errors and warnings have been resolved.

### Common Reference mistakes and recovery

- **The key contains `@`:** remove it from the record; `@` belongs only in document citations.
- **A title or journal is in the wrong field:** edit metadata; do not create a second Reference.
- **Two records describe one work:** inspect all uses before deleting or consolidating either one.
- **A key was changed manually:** restore the last known-good file and use `Rename Reference Key…`.
- **A relation appears on one side only:** run Research Check and repair through Related References; do not edit one record in isolation while Calamus is open.
- **A set contains an obsolete key:** use the controlled key rename so all authorities migrate together.
- **Quick Cite cannot find a source:** clear the search filter and verify that the Reference was saved.
- **Research Check reports a missing key:** correct the citation/Source Note or restore/import the canonical Reference.

A reliable References workflow is simple: register each source once, use stable keys, cite through Quick Cite, group sources transparently, and run Research Check before export or submission.

## Guida canonica completa del pannello Research

Questa è la guida operativa completa dell’apparato Research di Calamus. È pensata per chi scrive saggi, articoli, tesi, omelie documentate, libri o ricerche teologiche e desidera lavorare con fonti, citazioni e note senza affidare il proprio materiale a un database opaco.

Lo **Scratchpad Basic** e il client **Tags** sono parte del pannello Research. Tutto ciò che segue riguarda le funzioni Research disponibili: Clip Collection, Scratchpad, References, Tags, Related References, Reference Sets, Source Notes, Create Source Note from Selection, Insert Link to Heading, Authoring Bridge, Quick Cite, Open Citation in References, Rename Reference Key, Research Check, Tag Integrity, import/export BibTeX o BibLaTeX ed Export Research Apparatus.

Le etichette dei menu e dei pulsanti sono riportate in inglese perché corrispondono all’interfaccia reale. Le spiegazioni sono in italiano.

### 1. Prima idea fondamentale: Research non è un unico archivio

Il pannello Research presenta più strumenti nello stesso spazio laterale, ma i dati non appartengono tutti allo stesso file. Questa separazione è intenzionale: rende ogni informazione leggibile, esportabile e recuperabile anche senza Calamus.

Le autorità sono cinque:

1. **Documento attivo**: il file `.md` o `.txt` che stai scrivendo. Contiene il testo, le citazioni Pandoc e gli eventuali link interni alle intestazioni.
2. **References**: la biblioteca globale in `references.md`. Contiene una sola scheda canonica per ogni fonte.
3. **Source Notes**: il sidecar del documento, per esempio `Chapter-01.md.source-notes.md`. Contiene note di lettura appartenenti a quel documento.
4. **Scratchpad**: il sidecar `Chapter-01.md.scratchpad.md`. Contiene Note, Idea, Draft e Task che appartengono al lavoro intellettuale sul documento prima di diventare testo definitivo.
5. **Reference Sets**: il file globale `reference-sets.md`. Contiene liste statiche e ordinate di citation key.

Authoring Bridge, Research Check e gli export sono **proiezioni derivate**: leggono le autorità e mostrano o producono risultati. Non diventano una sesta autorità e non conservano un grafo o un indice nascosto.

Schema mentale:

```text
Documento.md
    ├── citazioni [@key]
    └── link interni [testo](#heading-id)

references.md
    ├── schede bibliografiche
    ├── alias
    └── Related Keys

Documento.md.source-notes.md
    └── note di lettura del documento

Documento.md.scratchpad.md
    ├── Note / Idea / Draft / Task
    ├── tag manuali
    └── collegamenti espliciti alle sezioni

reference-sets.md
    └── insiemi statici di citation key

Authoring Bridge / Research Check / Export
    └── risultati ricostruiti leggendo le cinque autorità
```

Questa mappa risolve molti dubbi:

- una Reference non è una citazione;
- una citazione non è una Source Note;
- un Related Reference non è un membro di set;
- una Source Note non è una voce Scratchpad: la prima conserva materiale proveniente da una fonte, la seconda sviluppa il pensiero dell'autore;
- una clip riutilizzabile non è una voce Scratchpad locale al documento;
- un set non copia i dati bibliografici;
- Authoring Bridge non memorizza backlink;
- un export non sostituisce `references.md`.

### 2. Dove sono conservati i dati

La libreria globale è normalmente:

```text
~/.local/share/calamus/research/references.md
```

Se `XDG_DATA_HOME` è impostato, il percorso è:

```text
$XDG_DATA_HOME/calamus/research/references.md
```

I Reference Sets sono normalmente:

```text
~/.local/share/calamus/research/reference-sets.md
```

Le Source Notes e lo Scratchpad stanno accanto al documento:

```text
~/Documents/Libro/Capitolo-01.md
~/Documents/Libro/Capitolo-01.md.source-notes.md
~/Documents/Libro/Capitolo-01.md.scratchpad.md
```

Questo significa che un backup serio deve includere:

- i documenti `.md` e `.txt`;
- tutti i sidecar `.source-notes.md`;
- tutti i sidecar `.scratchpad.md`;
- `references.md`;
- `reference-sets.md`;
- gli eventuali file locali collegati nelle References.

Gli export `.bib`, `.md` e `.txt` possono essere rigenerati e non sono l’autorità principale.

### 3. Percorso rapido: dal documento vuoto al controllo finale

La prima volta segui questo itinerario senza saltare passaggi.

1. Crea un documento e salvalo subito, per esempio `Articolo-Tradizione.md`.
2. Inserisci una struttura minima con intestazioni dotate di ID espliciti:

```markdown
# Tradizione e rinnovamento nella vita parrocchiale

    ## Introduzione {#introduzione}

    ## Fondamenti teologici {#fondamenti-teologici}

    ## Discernimento pastorale {#discernimento-pastorale}

    ## Conclusione {#conclusione}
```

3. Apri `Research → Scratchpad` (`Ctrl+Alt+S`) e annota la prima Idea collegandola alla sezione corrente.
4. Seleziona un passaggio provvisorio e usa `Capture Selection in Scratchpad…` (`Ctrl+Alt+Shift+S`) per conservarlo senza lasciarlo nel manoscritto.
5. Apri `Research → References` e registra due o tre fonti.
6. Inserisci una prima citazione con `Research → Quick Cite…`.
7. Crea una Source Note da una frase selezionata.
8. Collega la Source Note a una Reference e, quando utile, a una heading del documento.
9. Sviluppa nello Scratchpad le idee che collegano fonti e struttura; usa **Insert** soltanto quando il testo è pronto.
10. Apri `Research → Authoring Bridge` per vedere citazioni, note e link derivati.
11. Crea una relazione esplicita tra due References solo se esiste un motivo scientifico.
12. Crea un Reference Set per il lavoro corrente.
13. Esegui `Research → Research Check…`.
14. Correggi errori e warning, quindi esporta soltanto alla fine.

Questo itinerario è il modo più semplice per apprendere il sistema: prima le autorità, poi i collegamenti, infine i controlli e gli export.

### 4. Aprire, cambiare e chiudere il Research Panel

`Research → Research Panel` oppure `Ctrl+Alt+C` mostra o nasconde il pannello destro.

I client disponibili sono:

- **Clip Collection**;
- **Scratchpad**;
- **References**;
- **Reference Sets**;
- **Source Notes**;
- **Authoring Bridge**.

Quando scegli uno di questi comandi, Calamus apre il pannello se necessario e mostra il client richiesto. Il pulsante `X` nell’intestazione nasconde il pannello attraverso lo stesso gateway del menu: non elimina dati e non chiude il documento.

Buona abitudine: tieni aperto un solo client alla volta e usa il menu Research per cambiare contesto. Il pannello è uno spazio di lavoro, non una seconda finestra indipendente.

### 5. Clip Collection: frammenti riutilizzabili, non fonti

`Research → Clip Collection` gestisce una biblioteca globale di testi riutilizzabili. Ogni record possiede uno stable ID, un titolo, una shortcut mnemonica opzionale e un corpo Markdown. La shortcut è un indirizzo univoco come `firma` o `intro-articolo`: non è un tag e non classifica il contenuto.

Nel client puoi usare **New**, **Capture Selection**, **Insert**, **Copy Body** e il menu **Manage** con Edit, Duplicate, Delete, Refresh e Open Clip File. Search controlla shortcut, titolo e corpo; la riga mostra shortcut, titolo e anteprima; il dettaglio mostra il corpo completo senza modificarlo.

`Research → Insert Clip…` o `Ctrl+Alt+K` apre il selettore rapido. A query vuota mostra la lista completa delle shortcut. Digita una shortcut o una parola, usa Su/Giù e premi Enter. L’inserimento passa dal gateway del documento ed è un solo Undo. Il marcatore `{{cursor}}`, ammesso una sola volta, stabilisce dove deve trovarsi il cursore dopo l’inserimento.

`Ctrl+Alt+1…9` resta disponibile come insieme di **numeric quick slots** collegati ai primi nove record nell’ordine canonico del file. Non è una forma di identità stabile: per richiamare una clip per nome usa `Ctrl+Alt+K`.

L’autorità è `~/.config/calamus/clips.md`. Refresh rilegge realmente il file. Le scritture sono atomiche e protette da stale detection; una modifica esterna non viene sovrascritta in modo silenzioso. Clip Collection non è uno Scratchpad, non è una cronologia degli appunti e non controlla il clipboard.

Usa Clip Collection per formule, schemi, clausole, firme o strutture Markdown indipendenti dal documento corrente. Usa Scratchpad per idee e bozze legate a un documento; Source Notes per materiale tratto da una fonte; References per la sua identità bibliografica.

### 6. References: la biblioteca globale

`Research → References` apre il client della biblioteca canonica.

Ogni Reference rappresenta **una sola opera o risorsa**. Una scheda può descrivere un libro, un capitolo, un articolo, una voce enciclopedica, una tesi, un intervento a convegno, un rapporto, un documento istituzionale, un sito, un manoscritto o altro materiale.

Tipi disponibili:

```text
book
book-chapter
journal-article
encyclopedia-entry
thesis
conference-paper
report
institutional-document
website
manuscript
other
```

#### 6.1 La citation key

La key è l’identità stabile della Reference. Esempi:

```text
ratzinger1968
newman1870
lubac1949
rossi2024-a
```

Regole pratiche:

- niente spazi;
- niente `@`;
- usa lettere, numeri e pochi separatori leggibili;
- scegli una forma che possa restare stabile per anni;
- non rinominare per ragioni estetiche dopo aver iniziato a citarla;
- non creare due schede per la stessa opera.

Il pulsante **Suggest** propone una key basata su autore, anno e titolo. Controllala sempre. Se esiste già, Calamus aggiunge un suffisso prevedibile.

Esempio:

```text
Authors: Rossi, Maria
Year / Date: 2024
Title: Tradition and Renewal
```

Possibile proposta:

```text
rossi2024tradition
```

#### 6.2 Scheda Basic

Campi principali:

- **Key**: identità canonica;
- **Type**: tipo della fonte;
- **Authors**: autori separati da `;`, preferibilmente `Cognome, Nome`;
- **Title**: titolo dell’opera o del contributo;
- **Year / Date**: anno o data;
- **Tags**: tag separati da virgole;
- **Annotation**: nota bibliografica o valutativa estesa.

Esempio libro:

```text
Key: ratzinger1968
Type: book
Authors: Ratzinger, Joseph
Title: Introduction to Christianity
Year / Date: 1968
Tags: fede, cristologia, teologia
Annotation: Fonte centrale per il rapporto tra confessione, comprensione e fede.
```

Esempio con più autori:

```text
Authors: Rossi, Maria; Bianchi, Luca
```

#### 6.3 Scheda Publication

Campi disponibili:

- **Editors**;
- **Container Title**;
- **Publisher**;
- **Location**;
- **Volume**;
- **Issue**;
- **Pages**;
- **DOI**;
- **ISBN**;
- **ISSN**;
- **URL**;
- **Language**;
- **Local File**.

`Container Title` è la rivista, il volume collettaneo o il contenitore della parte descritta.

Esempio articolo:

```text
Key: rossi2024
Type: journal-article
Authors: Rossi, Maria
Title: Tradition and Renewal in Contemporary Theology
Year / Date: 2024
Container Title: Journal of Theological Studies
Volume: 18
Issue: 2
Pages: 115-138
DOI: 10.0000/example
Language: en
```

Esempio capitolo:

```text
Key: bianchi2022
Type: book-chapter
Authors: Bianchi, Luca
Title: Scripture and Tradition
Year / Date: 2022
Editors: Verdi, Paolo; Neri, Anna
Container Title: Sources of Christian Theology
Publisher: Academic Press
Location: Rome
Pages: 81-104
```

Non inventare metadati. Se un campo non è noto, lascialo vuoto e completalo dopo una verifica.

#### 6.4 Annotation, Tags e Local File

**Annotation** serve per una nota sulla fonte nel suo complesso:

```text
Utile per la distinzione tra trasmissione viva e ripetizione materiale.
Controllare l’edizione italiana prima della citazione definitiva.
```

Non usarla per accumulare tutte le citazioni testuali: quelle appartengono alle Source Notes.

**Tags** descrivono temi o funzioni:

```text
tradizione, ecclesiologia, fonte-primaria, da-verificare
```

**Local File** può contenere il percorso di un PDF o altro file locale:

```text
/home/luciano/Work/01_Studio/PDF_Studio/Ratzinger-Introduzione.pdf
```

Calamus conserva il percorso; non incorpora né indicizza il PDF.

#### 6.5 Cercare e filtrare

La ricerca del client References usa una proiezione in memoria e può trovare key, alias, titolo, tipo, anno, autori, curatori, contenitore, editore, luogo, DOI, ISBN, ISSN, URL, tag e annotation.

Esempi di ricerca:

```text
ratzinger
1968
tradizione
10.0000
fonte-primaria
```

La ricerca non modifica `references.md`. Cancella il testo per tornare all’elenco completo.

#### 6.6 Modificare una Reference

Seleziona una riga e premi **Edit**. Correggi metadati, tag, annotation o percorso locale. La key è protetta: per cambiarla usa `Research → Rename Reference Key…`.

Prima di modificare un record chiediti:

- è la stessa opera?
- sto correggendo un dato o creando una fonte diversa?
- il titolo è dell’opera o del contenitore?
- la nuova informazione è bibliografica o appartiene a una Source Note?

#### 6.7 Eliminare una Reference

L’eliminazione rimuove la scheda, non tutte le tracce della key. Prima:

1. apri Authoring Bridge;
2. controlla citazioni e Source Notes;
3. controlla Related References;
4. controlla Reference Sets;
5. esegui Research Check.

Se elimini una Reference ancora citata, Research Check segnalerà una key mancante.

### 7. Related References: relazioni esplicite tra due opere

Una Related Reference dichiara un rapporto scientifico concreto tra due References.

Usala quando puoi completare una frase come:

- «questa opera risponde a…»;
- «questa opera sviluppa…»;
- «questa opera presenta una posizione contraria a…»;
- «questa è una fonte primaria per lo stesso problema…»;
- «questi due testi devono essere letti insieme per comprendere…».

Non usarla solo perché due opere hanno lo stesso tag o sono nello stesso capitolo.

Procedura:

1. apri References;
2. seleziona `ratzinger1968`;
3. premi **Related References…**;
4. seleziona `newman1870`;
5. premi **Review Impact**;
6. controlla il piano;
7. premi **Apply**.

Impatto tipico:

```text
Add: newman1870
Remove: none
Reference records updated: 2
```

La relazione è simmetrica. Se A è legata a B, B è legata ad A. Calamus impedisce:

- self-link;
- duplicati;
- key mancanti;
- alias ambigui;
- scrittura silenziosa di una sola metà.

Esempio ragionato:

```text
ratzinger1968 ↔ newman1870
Motivo: confronto tra tradizione, sviluppo e continuità dell’identità cristiana.
```

Il motivo può essere annotato nelle Annotation o nelle Source Notes; Related Keys conserva soltanto le identità canoniche.

### 8. Reference Sets: liste statiche per un compito

Un Reference Set è una lista nominata, ordinata e trasparente di References esistenti.

Usalo per organizzare un lavoro:

```text
Fonti principali del capitolo 2
Testi patristici
Contrasto delle posizioni
Da verificare prima della consegna
Bibliografia per l’omelia
```

Non è una cartella gerarchica, non è una query dinamica e non implica relazioni tra tutti i membri.

Procedura:

1. `Research → Reference Sets`;
2. **Add**;
3. inserisci nome e descrizione;
4. seleziona i membri;
5. **Save**.

Esempio:

```text
Name: Core sources
Description: Fonti che sostengono direttamente la tesi dell’articolo.
Members:
- ratzinger1968
- newman1870
- lubac1949
```

I nomi sono case-sensitive e vengono conservati esattamente. `Core sources` e `Core Sources` hanno una grafia diversa; non cambiare maiuscole involontariamente.

Un buon set risponde a una domanda operativa:

```text
Quali fonti devo rileggere prima di chiudere questa sezione?
```

Una Reference può appartenere a più set. Eliminare un set non elimina le References.

#### 8.1 Related References o Reference Set?

Usa **Related References** per una relazione binaria motivata:

```text
Newman sviluppa un modello utile per leggere il problema discusso da Ratzinger.
```

Usa **Reference Sets** per una raccolta di lavoro:

```text
Queste cinque fonti devono essere controllate prima della consegna.
```

### 9. Source Notes: il quaderno di ricerca del documento

`Research → Source Notes` apre le note appartenenti al documento attivo. Se il documento non è ancora salvato, salvalo prima: il sidecar deve avere un proprietario stabile.

Tipi:

- **Quote**: trascrizione fedele;
- **Paraphrase**: riformulazione del contenuto della fonte;
- **Comment**: tua osservazione, ipotesi o promemoria.

Quote e Paraphrase richiedono una Reference. Comment può esistere senza Reference.

#### 9.1 Campi della Source Note

- **ID**: identità stabile generata da Calamus;
- **Type**: quote, paraphrase o comment;
- **Reference**: citation key della fonte;
- **Tags**: temi o stato del lavoro;
- **Text**: contenuto principale;
- **Comment**: osservazione ulteriore;
- **Document Target**: heading del documento con ID esplicito;
- **Page / Page End**;
- **Chapter**;
- **Section**;
- **Paragraph**.

Esempio Quote:

```text
Type: Quote
Reference: newman1870
Text: In a higher world it is otherwise, but here below to live is to change...
Page: 40
Tags: sviluppo, tradizione
Document Target: #fondamenti-teologici
Comment: Verificare l’edizione e il testo inglese definitivo.
```

Esempio Paraphrase:

```text
Type: Paraphrase
Reference: ratzinger1968
Text: La fede cristiana implica una forma pubblica e comunitaria di confessione.
Page: 52
Document Target: #fondamenti-teologici
```

Esempio Comment:

```text
Type: Comment
Reference: No reference (Comment only)
Text: Confrontare questo passaggio con la situazione della comunità locale.
Document Target: #discernimento-pastorale
Tags: da-sviluppare
```

#### 9.2 Locator: pagina, capitolo, sezione e paragrafo

Compila soltanto ciò che serve.

Esempi:

```text
Page: 42
```

```text
Page: 42
Page End: 45
```

```text
Chapter: III
Section: 2
Paragraph: 18
```

Il locator deve consentirti di ritrovare il punto nella fonte. Non è un commento libero.

#### 9.3 Document Target

Il target collega la nota a una heading con ID esplicito:

```markdown
    ## Fondamenti teologici {#fondamenti-teologici}
```

Target della Source Note:

```text
#fondamenti-teologici
```

Se rinomini il testo visibile della heading ma mantieni l’ID, il collegamento resta valido. Se cambi o elimini l’ID, Research Check e Authoring Bridge possono segnalare un target rotto.

#### 9.4 Creare, modificare, eliminare e navigare

- **Add** crea una nota vuota;
- **Edit** modifica la nota selezionata;
- **Delete** elimina la nota dal sidecar;
- l’apertura o doppio clic consente la navigazione prevista dal client;
- ricerca e filtri agiscono sulla proiezione, non sul file.

La cancellazione di una Source Note non modifica automaticamente il testo del documento.

### 10. Scratchpad Basic: dal pensiero provvisorio al testo

`Research → Scratchpad` oppure `Ctrl+Alt+S` apre il taccuino locale del documento corrente. Scratchpad non conserva dati bibliografici e non sostituisce Source Notes: organizza il lavoro dell'autore che sta tra le fonti e il manoscritto.

Il sidecar è trasparente:

```text
Capitolo-01.md
Capitolo-01.md.scratchpad.md
```

Ogni voce possiede un ID stabile, un tipo fra **Note**, **Idea**, **Draft** e **Task**, uno stato, tag manuali, zero o più heading target e un Body Markdown. Non esistono Concept o Question come tipi autonomi, priorità, scadenze, notifiche, inferenza semantica o knowledge graph.

#### 10.1 Cattura rapida e scorciatoie

- **New** crea una voce vuota;
- `Capture Selection in Scratchpad…` oppure `Ctrl+Alt+Shift+S` copia la selezione in una nuova Note senza modificare il documento;
- `New Scratchpad Entry for Current Section…` prepara una voce collegata alla heading corrente;
- **Insert** trasferisce il Body al cursore attraverso il normale command gateway e produce un unico Undo;
- **Copy** copia il Body senza cambiare il documento.

Quando la lista Scratchpad possiede il focus, `Insert` crea una voce, `Delete` richiede la cancellazione e `F5` ricarica il sidecar. Il pulsante **Refresh** esegue lo stesso reload esplicito.

#### 10.2 Collegare il pensiero alla struttura

Usa heading con ID Pandoc espliciti e univoci:

```markdown
    ## Fondamenti teologici {#fondamenti-teologici}
```

Una voce può collegarsi a più sezioni del documento corrente. **Open Section** naviga al target; `Show Scratchpad for Current Section` filtra le voci associate alla sezione del cursore. Calamus non usa numeri di riga, offset persistenti o somiglianze semantiche. Un target mancante o ambiguo viene segnalato e deve essere corretto esplicitamente.

#### 10.3 Tag, ricerca e stato

I tag sono manuali, piatti e case-preserving. Servono per ritrovare il materiale, non per costruire una tassonomia. La ricerca comprende ID, titolo, Body, tag e heading target. I filtri Type, Status, Tag e Current Section lavorano su una proiezione in memoria ricostruita dal sidecar.

**Archive** esclude una voce dal lavoro corrente senza eliminarla; premuto di nuovo la ripristina come Active. **Delete** rimuove la voce soltanto dopo conferma e non modifica il manoscritto.

#### 10.4 Modifiche esterne e Workspace

Se il sidecar cambia fuori da Calamus, la scrittura fallisce chiusa e propone Reload, Overwrite o Cancel. **Refresh** è la scelta ordinaria quando vuoi rileggere l'autorità dal disco. Rename, Duplicate e Move to Trash eseguiti dal Writing Workspace trasportano insieme il documento, Source Notes e Scratchpad.

Scratchpad Full aggiungerà References, Source Notes, Related Entries, Show Uses e integrità multi-autorità; Basic resta deliberatamente document-local e privo di database. Per la descrizione completa consulta anche il topic autonomo **Scratchpad Basic** nella colonna sinistra della User Guide.

### 11. Create Source Note from Selection

Questa funzione trasforma una selezione del documento in una bozza di Source Note.

Procedura:

1. seleziona nel documento il testo da conservare;
2. scegli `Research → Create Source Note from Selection…`;
3. Calamus cattura la selezione prima di aprire il dialogo;
4. scegli Quote, Paraphrase o Comment;
5. associa la Reference;
6. completa locator, target, tag e commento;
7. salva.

Esempio: nel documento hai incollato temporaneamente una frase da una fonte.

```text
La tradizione è la presenza viva della parola apostolica nella Chiesa.
```

Selezionala, crea una Source Note di tipo Quote, associa `ratzinger1968`, inserisci `Page: 88`, poi rimuovi dal documento la citazione provvisoria quando hai terminato la redazione.

La selezione iniziale è uno snapshot: modificare il documento mentre il dialogo è aperto non deve sostituire silenziosamente il testo catturato.

### 12. Insert Link to Heading

`Research → Insert Link to Heading…` inserisce un link Markdown verso una heading esplicitamente identificata.

Documento:

```markdown
    ## Discernimento pastorale {#discernimento-pastorale}
```

Link inserito:

```markdown
[vedi il discernimento pastorale](#discernimento-pastorale)
```

Procedura:

1. aggiungi `{#id}` alla heading di destinazione;
2. posiziona il cursore dove vuoi il link;
3. scegli `Insert Link to Heading…`;
4. seleziona la destinazione;
5. modifica, se necessario, il testo del link;
6. inserisci.

Usa ID leggibili e stabili:

```text
#introduzione
#fonti-patristiche
#discernimento-pastorale
```

Evita di basare collegamenti importanti soltanto sul testo visibile della heading.

### 13. Quick Cite: inserire citazioni senza ricordare le key

`Research → Quick Cite…` oppure `Ctrl+Alt+Q` inserisce una citazione Pandoc.

Esempi:

```markdown
[@ratzinger1968]
```

```markdown
[@ratzinger1968, p. 42]
```

```markdown
[@newman1870, pp. 55-57]
```

```markdown
[@ratzinger1968, p. 42; @newman1870, pp. 55-57]
```

Procedura:

1. posiziona il cursore;
2. apri Quick Cite;
3. cerca la Reference;
4. selezionala;
5. aggiungi il locator;
6. inserisci.

Quick Cite non crea una Source Note. Inserisce soltanto il marker citazionale nel documento.

### 14. Open Citation in References

Quando il cursore è dentro o vicino a una citazione, usa:

```text
Research → Open Citation in References
Ctrl+Alt+Shift+Q
```

Esempio:

```markdown
La continuità non coincide con l’immobilità [@newman1870, p. 55].
```

Il comando risolve la key e apre la Reference canonica. Se il documento usa un alias valido, Calamus apre la key primaria.

Se il comando non trova nulla:

- verifica che il cursore sia nella citazione;
- controlla la sintassi Pandoc;
- esegui Research Check;
- verifica che la key o l’alias esista.

### 15. Rename Reference Key: una migrazione controllata

Non rinominare manualmente una key in `references.md`. Usa `Research → Rename Reference Key…`.

Il comando può aggiornare quattro autorità:

1. record e Related Keys in `references.md`;
2. membership in `reference-sets.md`;
3. citazioni nel documento attivo;
4. Reference nelle Source Notes del documento.

Esempio:

```text
Old key: newman1870
New key: newman1870-revised
Preserve the old key as an alias: yes
```

Prima dell’applicazione leggi l’impact preview:

```text
Active-document citation occurrences: 1
Current Source Notes occurrences: 1
Related-key occurrences: 1
Reference Set memberships: 1
Old key preserved as alias: yes
```

Premi **Rename Key** soltanto se i conteggi descrivono la situazione reale.

Dopo la rinomina verifica:

```markdown
[@newman1870-revised, p. 55]
```

```text
Related key: newman1870-revised
Reference Set member: newman1870-revised
Source Note Reference: newman1870-revised
Alias: newman1870
```

Se uno dei file cambia dopo la preview, Calamus deve fermarsi come stale. Se una scrittura fallisce, tenta il rollback delle autorità già aggiornate.

### 16. Authoring Bridge: leggere le relazioni derivate

Authoring Bridge è una mappa ricostruita dai file attuali. Non salva backlink e non mantiene un indice persistente.

Modalità disponibili:

- **By Reference**: occorrenze legate a una Reference;
- **By Heading**: elementi legati a una heading;
- **Related References**: relazioni esplicite tra References;
- **Broken Research links**: problemi navigabili.

#### 16.1 By Reference

Scegli una Reference per vedere, secondo il contenuto presente:

- citazioni nel documento;
- Source Notes collegate;
- problemi di key;
- elementi navigabili.

Esempio:

```text
Subject: ratzinger1968
Results:
- citation, line 18
- Source Note sn-20260726-abc123
```

Aprire una citazione porta al documento. Aprire una Source Note porta alla nota esatta.

#### 16.2 By Heading

Scegli una heading per vedere:

- link Markdown diretti a quell’ID;
- Source Notes con quel Document Target;
- diagnostica della struttura.

È utile per verificare se una sezione possiede fonti e note sufficienti prima della redazione.

#### 16.3 Related References

Scegli una Reference e naviga le relazioni esplicite. Il conteggio deriva da `references.md` e deve aggiornarsi dopo **Refresh**.

#### 16.4 Broken Research links

Questa modalità raccoglie problemi come:

- citation key assente;
- Source Note con Reference mancante;
- link a heading inesistente;
- Source Note target mancante;
- heading ambigua o priva di identità utilizzabile.

Usala come elenco operativo: apri un problema, correggi l’autorità proprietaria, poi premi **Refresh**.

### 17. Research Check: controllo complessivo

`Research → Research Check…` controlla la coerenza delle autorità.

Possibili categorie:

- **errors**: incoerenze bloccanti;
- **warnings**: problemi da correggere o verificare;
- **advisories**: informazioni utili, non necessariamente difetti.

Esempi di errori o warning:

- citation key mancante;
- alias duplicato o ambiguo;
- Related References asimmetriche;
- self-link;
- membro di set inesistente;
- set malformato;
- Source Note con Reference mancante;
- Document Target mancante o ambiguo;
- collisione logica dei tag.

Esempio di advisory legittima:

```text
Reference non usata nel documento attivo
```

Una fonte può essere preparatoria e non ancora citata. Non cancellarla automaticamente.

Workflow consigliato:

1. esegui Research Check prima di esportare;
2. risolvi prima gli errori;
3. valuta i warning uno per uno;
4. leggi le advisories senza trattarle come guasti;
5. riesegui il controllo finché il quadro è comprensibile.

### 18. Tags e Tag Integrity: rinominare e unificare tag senza sostituzioni cieche

`Research → Tags` è il client ordinario: analizza References, Source Notes e Scratchpad, mostra gli usi esatti e permette la navigazione. `Research → Tag Integrity…` resta il dialogo compatibile limitato a References e Source Notes.

Problemi tipici:

```text
Faith
faith
fede
fede-cristiana
```

Le operazioni devono essere esplicite:

- rename;
- merge;
- remove;
- normalize quando previsto.

Esempio:

```text
Faith → doctrine
```

La preview deve mostrare quali occorrenze logiche cambiano. Testo libero, titoli, citazioni e documenti non devono essere modificati da una semplice operazione sui tag.

Non usare Tag Integrity come sostituzione globale di parole.

### 19. Import BibTeX/BibLaTeX

`Research → Import BibTeX/BibLaTeX…` importa un file `.bib` locale attraverso una preview.

Esempio:

```bibtex
@book{ratzinger1968,
  author    = {Ratzinger, Joseph},
  title     = {Introduction to Christianity},
  year      = {1968},
  publisher = {Burns & Oates}
}
```

La preview distingue:

- record nuovi;
- collisioni;
- record invalidi;
- key non risolte;
- azioni scelte per ogni collisione.

Principi:

- il `.bib` è input;
- `references.md` resta l’autorità;
- nessuna collisione deve essere risolta in silenzio;
- controlla sempre key, autori, titolo, anno e tipo;
- i campi non riconosciuti devono essere preservati quando possibile come extra fields.

Dopo l’importazione esegui Research Check.

### 20. Export References as BibTeX/BibLaTeX

Questo comando produce un `.bib` derivato per Pandoc, JabRef, KBibTeX o altri strumenti.

Esempio destinazione:

```text
~/Documents/Libro/Exports/calamus-references.bib
```

Regola:

```text
references.md = autorità
calamus-references.bib = export derivato
```

Se correggi un autore nel file esportato, la modifica non torna automaticamente in Calamus. Correggi la Reference e rigenera l’export.

### 21. Export Research Apparatus

`Research → Export Research Apparatus…` crea prodotti Markdown leggibili.

Prodotti disponibili:

- Source Notes in Document Order;
- Source Notes by Reference;
- Bibliography of Cited Sources;
- Annotated Bibliography;
- Complete Research Dossier.

Esempio:

```text
Documento: Chapter-01.md
Prodotto: Complete Research Dossier
Destinazione: Exports/Chapter-01-research-dossier.md
```

L’export può riunire bibliografia, citazioni e note, ma resta derivato. Calamus deve impedire che sovrascriva:

- il documento attivo;
- `references.md`;
- il sidecar Source Notes corrente;
- altre autorità Research.

### 22. Gestire modifiche esterne e stato stale

I file Research sono leggibili e possono essere aperti da un editor esterno. Questo non significa che sia sicuro modificarli contemporaneamente a Calamus.

Se un file cambia dopo il caricamento o dopo una preview, Calamus può proporre:

- **Reload**: accetta il file esterno;
- **Overwrite**: conserva consapevolmente la versione rivista in Calamus;
- **Cancel**: non scrive nulla.

Regole:

- non scegliere Overwrite senza avere letto l’impatto;
- non correggere metà di una relazione simmetrica a mano;
- non rinominare key con search-and-replace globale;
- chiudi Calamus prima di manutenzioni manuali complesse;
- conserva un backup del file prima di modifiche strutturali.

### 23. Esempio completo: costruire un articolo teologico

Progetto:

```text
Titolo: Tradizione e rinnovamento nella vita parrocchiale
Documento: Tradizione-Rinnovamento.md
```

#### 23.1 Registra le fonti

```text
ratzinger1968 — Introduction to Christianity
newman1870 — An Essay on the Development of Christian Doctrine
lubac1949 — Catholicism
```

#### 23.2 Crea una relazione

```text
ratzinger1968 ↔ newman1870
```

Motivo: entrambe le opere aiutano a comprendere continuità, sviluppo e identità della fede.

#### 23.3 Crea i set

```text
Core sources
- ratzinger1968
- newman1870
- lubac1949
```

```text
Check locators
- newman1870
- lubac1949
```

#### 23.4 Crea Source Notes

Nota 1:

```text
Type: Quote
Reference: newman1870
Page: 40
Document Target: #fondamenti-teologici
Text: To live is to change...
Tags: sviluppo, tradizione
```

Nota 2:

```text
Type: Paraphrase
Reference: ratzinger1968
Page: 52
Document Target: #fondamenti-teologici
Text: La fede assume una forma comunitaria e confessante.
Tags: fede, comunità
```

Nota 3:

```text
Type: Comment
Reference: No reference (Comment only)
Document Target: #discernimento-pastorale
Text: Tradurre il principio teologico in criteri concreti per il consiglio pastorale.
Tags: da-sviluppare
```

#### 23.5 Scrivi con Quick Cite

```markdown
    ## Fondamenti teologici {#fondamenti-teologici}

La tradizione cristiana non coincide con una ripetizione immobile del passato
[@ratzinger1968, p. 52]. Il concetto di sviluppo permette di comprendere una
continuità capace di crescita [@newman1870, p. 40]. La dimensione ecclesiale
impedisce di ridurre questo processo a una scelta puramente individuale
[@lubac1949, pp. 101-103].
```

#### 23.6 Verifica con Authoring Bridge

- By Reference: ogni fonte deve mostrare le occorrenze previste;
- By Heading: `#fondamenti-teologici` deve mostrare le Source Notes collegate;
- Related References: `ratzinger1968` deve mostrare `newman1870`;
- Broken Research links: nessun risultato inatteso.

#### 23.7 Esegui Research Check

Risultato ideale:

```text
0 errors
0 warnings
advisories comprese e giustificate
```

#### 23.8 Esporta

1. genera il `.bib` derivato;
2. genera il Complete Research Dossier;
3. conserva gli export nella cartella `Exports`;
4. continua a correggere i dati soltanto nelle autorità canoniche.

### 24. Workflow per diversi tipi di lavoro

#### 24.1 Articolo breve

- 5-15 References;
- un set `Core sources`;
- Source Notes collegate alle 3-5 heading principali;
- Quick Cite durante la redazione;
- Research Check prima della consegna.

#### 24.2 Capitolo di libro o tesi

- References globali riutilizzate tra capitoli;
- un sidecar Source Notes per capitolo;
- set distinti per capitolo o funzione;
- heading ID stabili;
- dossier Research per revisione e supervisione.

#### 24.3 Omelia o conferenza documentata

- set `Testi biblici`, `Padri`, `Magistero`, `Studi`;
- Source Notes brevi con locator;
- tag per tema pastorale;
- export della bibliografia o dossier per l’archivio.

#### 24.4 Ricerca esplorativa

- References con annotation chiare;
- tag `da-leggere`, `letto`, `da-verificare`;
- set temporanei per domande specifiche;
- evitare relazioni inferite: aggiungere Related References solo dopo una lettura reale.

### 25. Errori comuni e recupero

#### La key contiene `@`

Errato:

```text
@ratzinger1968
```

Corretto nel record:

```text
ratzinger1968
```

La forma con `@` appartiene soltanto alla citazione.

#### Ho creato un duplicato

Non eliminare subito. Controlla citazioni, alias, Source Notes, Related References e set. Scegli una sola identità canonica e migra con gli strumenti controllati.

#### Ho messo il titolo della rivista in Title

Sposta il titolo della rivista in `Container Title`; conserva in `Title` il titolo dell’articolo.

#### Quick Cite non trova la fonte

- cancella il filtro;
- verifica che il record sia stato salvato;
- cerca key o autore;
- controlla Research Check.

#### Una Source Note non accetta Quote o Paraphrase

Quote e Paraphrase richiedono una Reference. Se la nota è una tua osservazione senza fonte, scegli Comment.

#### Il Document Target è mancante

Aggiungi o ripristina l’ID esplicito della heading, poi modifica la Source Note selezionando il target corretto.

#### Authoring Bridge mostra dati vecchi

Premi **Refresh**. Se il file è stato modificato esternamente, risolvi prima l’eventuale stato stale.

#### Related References è asimmetrica

Esegui Research Check e ripara dal dialogo Related References. Non aggiungere manualmente una sola riga.

#### Il set contiene una vecchia key

Usa Rename Reference Key. Una rinomina manuale non garantisce la migrazione di tutte le autorità.

#### Lo Scratchpad non mostra una modifica fatta con un editor esterno

Premi **Refresh** o `F5` con la lista focalizzata. Non usare Overwrite se vuoi conservare la versione esterna. Evita di modificare contemporaneamente lo stesso sidecar in due applicazioni.

#### Una voce Scratchpad non appare nella sezione corrente

Controlla che la heading possieda un ID Pandoc esplicito e univoco e che la voce sia collegata a quel target. Premi **All** per rimuovere il filtro, correggi il collegamento e applica di nuovo `Show Scratchpad for Current Section`.

#### Ho modificato un export pensando che fosse la libreria

Riporta la correzione in References e rigenera l’export. Il file derivato non è l’autorità.

#### Research Check mostra References non usate

È un’advisory, non necessariamente un errore. Decidi se la fonte è preparatoria, appartiene a un altro capitolo o può essere rimossa.

### 26. Disciplina consigliata per una biblioteca che cresce

1. Registra una fonte una sola volta.
2. Usa key stabili e leggibili.
3. Compila soltanto metadati verificati.
4. Usa Annotation per valutare l’opera, Source Notes per estratti e idee puntuali.
5. Usa tag coerenti e periodicamente apri Tags con **Variants only**.
6. Collega Related References soltanto quando sai spiegare il rapporto.
7. Crea set con uno scopo operativo chiaro.
8. Usa heading ID stabili nei documenti lunghi.
9. Esegui Research Check prima di export, consegna o archiviazione.
10. Conserva backup di documenti, sidecar e file globali Research.
11. Tratta gli export come prodotti rigenerabili.
12. Non modificare simultaneamente le stesse autorità in Calamus e in un editor esterno.

### 27. Checklist finale prima di consegnare un lavoro

Documento:

- tutte le citazioni hanno key valide;
- i locator importanti sono presenti;
- i link interni puntano a heading esistenti;
- il documento è salvato.

References:

- nessun duplicato evidente;
- autori, titoli e anni controllati;
- DOI/ISBN/URL verificati quando presenti;
- alias comprensibili;
- Local File ancora raggiungibile quando usato.

Source Notes:

- Quote e Paraphrase hanno una Reference;
- i locator consentono di ritrovare il testo;
- i target sono ancora validi;
- i commenti personali sono distinti dal testo della fonte.

Scratchpad:

- le voci ancora utili non sono rimaste per errore in Archived;
- i tag sono coerenti e i target di sezione sono validi;
- Draft e Idea pronti sono stati inseriti o marcati Resolved;
- il sidecar `.scratchpad.md` è incluso nel backup del documento.

Relations and Sets:

- Related References sono motivate e simmetriche;
- i set contengono membri esistenti;
- nomi, descrizioni e ordine sono corretti;
- nessuna vecchia key è rimasta dopo una rinomina.

Integrity and export:

- Research Check non presenta errori;
- warning compresi e risolti o motivati;
- Tags controllati con **Variants only** quando necessario;
- `.bib` e dossier rigenerati dopo le ultime correzioni.

### 28. Glossario essenziale

- **Authority**: file che possiede un dato e può essere modificato come fonte canonica.
- **Reference**: scheda bibliografica globale.
- **Citation key**: identità stabile di una Reference.
- **Alias**: key precedente o alternativa che risolve alla key primaria.
- **Citation**: marker Pandoc nel documento.
- **Source Note**: nota di lettura appartenente a un documento e fondata, quando richiesto, su una Reference.
- **Scratchpad Entry**: Note, Idea, Draft o Task appartenente al lavoro intellettuale sul documento corrente.
- **Sidecar**: file compagno del documento.
- **Locator**: pagina, capitolo, sezione o paragrafo della fonte.
- **Document Target**: heading ID a cui una Source Note è collegata.
- **Related Reference**: relazione esplicita e simmetrica tra due fonti.
- **Reference Set**: lista statica, nominata e ordinata di References.
- **Projection**: risultato calcolato leggendo le autorità senza diventare autorità.
- **Stale**: stato in cui un file è cambiato dopo il caricamento o la preview.
- **Impact preview**: piano dettagliato delle modifiche prima della scrittura.
- **Derived export**: file prodotto dalle autorità e rigenerabile.

### 29. Regola conclusiva

Il Research Panel funziona bene quando ogni informazione viene collocata nel posto giusto:

```text
Dati bibliografici        → References
Citazione nel testo       → documento
Estratto fondato su fonte → Source Notes
Idea, bozza o task locale   → Scratchpad
Rapporto tra due opere      → Related References
Gruppo per un compito     → Reference Sets
Navigazione e controllo   → Authoring Bridge / Research Check
Scambio con altri tool    → import/export derivati
```

La ricchezza del sistema richiede una curva di apprendimento, ma il vantaggio è concreto: il lavoro accademico rimane trasparente, verificabile, navigabile e ricostruibile attraverso normali file di testo.


## Export with Pandoc/citeproc

### A cosa serve

`Research → Export with Pandoc/citeproc…` usa un'installazione locale di Pandoc
per produrre un file formattato. Il comando può creare una bibliografia oppure
convertire il documento corrente applicando citeproc alle citazioni Pandoc.

Questa funzione non cambia il modo in cui Calamus conserva il lavoro:

- `references.md` resta la biblioteca canonica;
- `reference-sets.md` resta l'elenco trasparente dei set statici;
- il documento corrente resta il testo autorevole;
- il file CSL scelto è soltanto uno stile locale in lettura;
- il risultato Pandoc è un **derived export**, quindi può essere rigenerato.

Correggi sempre metadati e citazioni nelle autorità originali. Non usare un DOCX,
un ODT o un HTML esportato come nuova biblioteca bibliografica.

### Prima di iniziare

1. Salva il documento se vuoi esportare **Current Document with Citations**.
2. Controlla References con `Research → Research Check`.
3. Verifica che le citazioni usino la sintassi Pandoc, per esempio
   `[@ratzinger1968, p. 42]`.
4. Installa Pandoc nel sistema. Calamus non incorpora né scarica Pandoc.
5. Se vuoi uno stile particolare, prepara un file CSL locale con estensione
   `.csl`. Calamus non scarica stili dalla rete.

Se Pandoc non è installato, Calamus interrompe il workflow prima della preview e
mostra il messaggio **Pandoc is not installed or is not available on PATH**.
Nessun file viene scritto.

### Tutorial completo: esportare con Pandoc passo per passo

Questa sezione accompagna anche chi non ha mai usato Pandoc. Il principio da
ricordare è semplice: **Calamus prepara gli input, Pandoc produce una copia
formattata, le autorità originali non vengono cambiate**.

#### Passo P1 — Controlla il documento che hai davvero aperto

Il prodotto **Current Document with Citations** usa il documento attualmente
aperto in Calamus. Prima di avviare l'export:

1. guarda il percorso nella barra del titolo;
2. salva il documento con `File → Save`;
3. verifica che le citazioni presenti appartengano proprio a quel file;
4. non confondere due file con lo stesso nome conservati in cartelle diverse.

Esempio: se vuoi esportare
`~/Studio/Articolo/Grace-and-reason.md`, assicurati che nella barra del titolo
compaia proprio quel percorso, non `~/Downloads/Grace-and-reason.md`.

Il prodotto **Formatted Bibliography** può funzionare anche senza citazioni nel
documento, ma il documento aperto determina comunque quali References risultano
"cited" quando scegli lo scope delle fonti citate.

#### Passo P2 — Verifica che Pandoc sia disponibile

Pandoc deve essere installato nel sistema e raggiungibile tramite `PATH`.
Calamus lo controlla all'inizio di ogni nuovo workflow. Se non lo trova, mostra
un errore controllato e non crea alcun file.

Dopo aver installato Pandoc puoi riaprire immediatamente
`Research → Export with Pandoc/citeproc…`. Non devi ricreare References o
Reference Sets. Se il sistema non rende subito visibile il nuovo eseguibile,
chiudi e riapri Calamus.

#### Passo P3 — Apri il comando

Scegli:

`Research → Export with Pandoc/citeproc…`

Il primo dialogo raccoglie quattro decisioni:

1. **Product** — che cosa vuoi produrre;
2. **Reference scope** — quali fonti devono essere incluse;
3. **Output format** — il tipo di file finale;
4. **Citation style** — stile predefinito oppure file CSL locale.

Nessuna scelta viene ancora scritta su disco. Puoi premere **Cancel** in
qualsiasi momento.

#### Passo P4 — Scegli Product

Hai due possibilità.

##### Opzione Product 1: Formatted Bibliography

Produce soltanto la bibliografia. Non include il corpo del documento.

Usala quando vuoi:

- allegare una bibliografia a un file preparato con un altro programma;
- controllare il risultato di uno stile CSL;
- creare una bibliografia per un corso, un progetto o un Reference Set;
- consegnare un elenco di fonti senza esportare il manoscritto.

Esempio:

```text
Product: Formatted Bibliography
Reference scope: One Reference Set
Reference Set: Core sources
Output format: Plain text (.txt)
```

Risultato possibile:

```text
Ratzinger, Joseph. Introduction to Christianity. 1968.
Guardini, Romano. The Lord. 1950.
```

##### Opzione Product 2: Current Document with Citations

Produce una copia formattata del documento attualmente aperto. Citeproc elabora
le citazioni e aggiunge la bibliografia secondo lo scope scelto.

Usala quando vuoi:

- consegnare un DOCX o un ODT;
- creare un EPUB;
- produrre HTML o LaTeX;
- controllare il documento completo con citazioni formattate.

Il Markdown originale non viene modificato. Anche l'eventuale sostituzione di un
alias con la key primaria avviene soltanto nella copia temporanea.

Esempio di documento sorgente:

```markdown
# Grazia e ragione

La fede coinvolge l'intera persona
[@ratzinger-old, pp. 12-14; @guardini1950].
```

Se `ratzinger-old` è un alias di `ratzinger1968`, il file derivato usa la fonte
corretta senza riscrivere il documento aperto.

#### Passo P5 — Scegli Reference scope

Hai tre possibilità. La scelta determina quali record di `references.md`
vengono proiettati nella bibliografia temporanea.

##### Opzione scope 1: References cited in the current document

Include soltanto le fonti citate nel documento aperto, nell'ordine della loro
prima occorrenza.

Esempio:

```markdown
Prima citazione [@guardini1950].
Seconda citazione [@ratzinger1968].
```

La selezione iniziale delle key sarà:

```text
guardini1950, ratzinger1968
```

È la scelta più adatta per un articolo o un capitolo che deve contenere soltanto
le fonti realmente utilizzate. Se non esiste alcuna citazione Pandoc valida,
Calamus blocca l'operazione.

##### Opzione scope 2: All References

Include tutte le schede valide di `references.md`, anche quelle non citate nel
documento.

Usala per:

- bibliografia generale di un progetto;
- catalogo completo della biblioteca Calamus;
- documento che deve includere anche letture consigliate non citate.

Nel prodotto **Current Document with Citations**, Calamus aggiunge `nocite: @*`
soltanto alla copia temporanea. Il file Markdown originale rimane invariato.

##### Opzione scope 3: One Reference Set

Include i membri di un Reference Set statico nell'ordine memorizzato.

Esempio di `reference-sets.md`:

```markdown
# Calamus Reference Sets v1

 ## Core sources
Description: Fonti principali del capitolo.
Members: ratzinger1968, guardini1950
```

Nel dialogo devi scegliere esattamente `Core sources`. I nomi sono
case-sensitive: `Core sources` e `Core Sources` sono nomi diversi.

Questo scope è utile per:

- bibliografia di un singolo capitolo;
- reading list di un corso;
- fonti primarie separate dalle secondarie;
- selezione ordinata per una conferenza o una pubblicazione.

Per **Current Document with Citations**, il set deve contenere tutte le fonti
citate. Se il testo cita `newman1870` ma il set non la include, Calamus blocca
l'export e mostra la key mancante.

#### Passo P6 — Scegli Output format

Le opzioni dipendono dal Product.

##### Formati per Formatted Bibliography

- **Plain text (.txt)** — elenco semplice e leggibile ovunque. Esempio:
  `bibliografia-capitolo.txt`.
- **HTML (.html)** — pagina Web completa, utile per pubblicazione o anteprima in
  browser. Esempio: `bibliografia-seminario.html`.
- **OpenDocument Text (.odt)** — documento modificabile con LibreOffice Writer.
  Esempio: `bibliografia-tesi.odt`.
- **Microsoft Word (.docx)** — documento modificabile in Word o programmi
  compatibili. Esempio: `bibliografia-rivista.docx`.
- **Rich Text Format (.rtf)** — formato di scambio per editor che non gestiscono
  bene ODT o DOCX. Esempio: `bibliografia.rtf`.
- **LaTeX source (.tex)** — sorgente LaTeX, utile in un progetto TeX già
  esistente. Esempio: `bibliografia.tex`.

##### Formati per Current Document with Citations

- **HTML (.html)** — documento Web autonomo con citazioni e bibliografia.
- **OpenDocument Text (.odt)** — scelta consigliata per LibreOffice Writer.
- **Microsoft Word (.docx)** — scelta consigliata quando l'editore richiede
  Word.
- **EPUB (.epub)** — libro elettronico; controlla il risultato con un lettore
  EPUB esterno.
- **Rich Text Format (.rtf)** — compatibilità con editor tradizionali.
- **LaTeX source (.tex)** — sorgente da rifinire in un progetto LaTeX esterno.

PDF non è disponibile in W90. Per produrre PDF usa successivamente il file ODT,
DOCX o LaTeX con lo strumento esterno appropriato.

Regola pratica:

```text
Devo continuare a correggere il testo in LibreOffice  → ODT
L'editore vuole Microsoft Word                       → DOCX
Devo pubblicare sul Web                              → HTML
Sto preparando un ebook                              → EPUB
Mi serve massima compatibilità tradizionale          → RTF
Lavoro già in un progetto TeX                        → LaTeX
Mi serve soltanto un elenco leggibile                → TXT
```

#### Passo P7 — Scegli Citation style

Hai due possibilità.

##### Opzione style 1: Use Pandoc Default

Pandoc usa il proprio stile predefinito. È la scelta più semplice per una prima
prova e non richiede file aggiuntivi.

Usala quando:

- vuoi verificare che citazioni e bibliografia funzionino;
- non hai ancora ricevuto lo stile richiesto dalla rivista;
- il formato esatto non è ancora importante.

##### Opzione style 2: Local CSL file

Scegli un file `.csl` già presente sul computer. Calamus lo legge senza copiarlo
né modificarlo.

Usala quando:

- la rivista richiede Chicago, APA o un proprio stile;
- il relatore ti ha fornito un file CSL;
- vuoi confrontare due stili diversi sullo stesso documento.

Esempio:

```text
Citation style: Local CSL file
File: ~/Studio/Stili/chicago-author-date.csl
```

Il file deve essere regolare, leggibile, non simbolico e inferiore al limite
indicato. Se cambi il CSL dopo la preview, il piano diventa stale e devi ripetere
l'operazione.

#### Passo P8 — Scegli la destinazione

Dopo le opzioni, Calamus propone un nome coerente con Product e format.

Esempi:

```text
capitolo-bibliography.txt
capitolo-bibliography.odt
capitolo-with-citations.docx
capitolo-with-citations.epub
```

Controlla attentamente la cartella. Il verificatore umano più semplice è leggere
l'intero percorso mostrato dal file chooser prima di confermare.

La destinazione non può coincidere con:

- `references.md`;
- `reference-sets.md`;
- il documento corrente;
- il relativo file Source Notes;
- il CSL scelto.

Se il file esiste già, Calamus chiede conferma. Se quel file viene modificato da
un altro programma dopo la preview, l'export viene bloccato come stale.

#### Passo P9 — Leggi la semantic preview

La preview non imita graficamente ODT, DOCX o EPUB. Mostra invece i dati che
determinano l'export.

Controlla sempre:

1. **Product**;
2. **Scope**;
3. nome esatto del Reference Set, se presente;
4. numero delle References;
5. ordine delle key;
6. output format;
7. destinazione completa;
8. stile CSL o Pandoc default;
9. warning BibLaTeX;
10. warning Pandoc;
11. testo bibliografico prodotto da citeproc.

Esempio corretto:

```text
Product: Formatted Bibliography
Scope: One Reference Set
Reference Set: Core sources
References: 2
Keys: ratzinger1968, guardini1950
Output format: Plain text (.txt)
```

Se una key è inattesa, premi **Cancel** e correggi References, citazioni o
Reference Set. Non confermare sperando di sistemare il file derivato in seguito.

#### Passo P10 — Conferma, annulla e riapri

Premi **Export** soltanto dopo avere controllato la preview. Calamus avvia Pandoc,
mostra lo stato del processo e pubblica il file soltanto dopo tutti i controlli.

Premi **Cancel** per interrompere senza creare il file finale. Puoi riaprire
subito il comando: il dialogo deve ripartire da uno stato coerente.

Se chiudi Calamus durante una conversione, il programma termina il processo
Pandoc attivo, rimuove lo staging e completa la chiusura soltanto quando il
worker è terminato.

#### Passo P11 — Esempi completi

##### Esempio A — Bibliografia TXT di un Reference Set

```text
Product: Formatted Bibliography
Reference scope: One Reference Set
Reference Set: Core sources
Output format: Plain text (.txt)
Citation style: Use Pandoc Default
Destination: ~/Esportazioni/core-sources-bibliography.txt
```

Controlla che la preview contenga soltanto i membri del set.

##### Esempio B — Bibliografia HTML con stile locale

```text
Product: Formatted Bibliography
Reference scope: All References
Output format: HTML (.html)
Citation style: Local CSL file
CSL: ~/Studio/Stili/apa.csl
Destination: ~/Esportazioni/bibliografia-completa.html
```

Apri poi l'HTML in un browser e controlla ordine, corsivi e punteggiatura.

##### Esempio C — Documento ODT con le sole fonti citate

```text
Product: Current Document with Citations
Reference scope: References cited in the current document
Output format: OpenDocument Text (.odt)
Citation style: Use Pandoc Default
Destination: ~/Esportazioni/capitolo-with-citations.odt
```

È il percorso più semplice per continuare in LibreOffice.

##### Esempio D — Documento DOCX richiesto da una rivista

```text
Product: Current Document with Citations
Reference scope: References cited in the current document
Output format: Microsoft Word (.docx)
Citation style: Local CSL file
CSL: ~/Studio/Stili/rivista-teologica.csl
Destination: ~/Consegna/articolo-with-citations.docx
```

Dopo l'export apri il DOCX e controlla citazioni, bibliografia, titoli e corsivi.

##### Esempio E — EPUB con tutte le References

```text
Product: Current Document with Citations
Reference scope: All References
Output format: EPUB (.epub)
Citation style: Use Pandoc Default
Destination: ~/Esportazioni/libro-with-citations.epub
```

Usa questa combinazione soltanto quando vuoi che la bibliografia contenga anche
fonti non citate. Verifica il risultato con un lettore EPUB esterno.

##### Esempio F — Sorgente LaTeX per un progetto esterno

```text
Product: Current Document with Citations
Reference scope: One Reference Set
Reference Set: Fonti capitolo 3
Output format: LaTeX source (.tex)
Citation style: Local CSL file
Destination: ~/Progetto-TeX/capitolo-3-with-citations.tex
```

Il Reference Set deve includere tutte le key citate nel capitolo.

#### Passo P12 — Controllo dopo l'export

Dopo il messaggio di completamento:

1. verifica che il file esista nella cartella scelta;
2. controlla che non sia vuoto;
3. aprilo con un programma adatto al formato;
4. verifica almeno una citazione e due voci bibliografiche;
5. accertati che il documento Markdown e i file Research siano invariati;
6. conserva l'output come file derivato, non come nuova autorità.

Se il file non si trova, non dichiarare l'export riuscito: riapri il comando e
controlla l'intero percorso di destinazione.

### Scegli il prodotto

Il primo campo offre due prodotti.

#### Formatted Bibliography

Produce soltanto la bibliografia formattata. I formati disponibili sono:

- Plain text `.txt`;
- HTML `.html`;
- OpenDocument Text `.odt`;
- Microsoft Word `.docx`;
- Rich Text Format `.rtf`;
- LaTeX source `.tex`.

Questo prodotto è utile per allegare una bibliografia a un documento preparato
altrove o per controllare rapidamente l'effetto di uno stile CSL.

#### Current Document with Citations

Converte una copia temporanea del documento corrente e applica citeproc. I
formati disponibili sono HTML, ODT, DOCX, EPUB, RTF e LaTeX. Il documento aperto
non viene riscritto. Se una citazione usa un alias, Calamus inserisce la key
primaria soltanto nella copia temporanea inviata a Pandoc.

PDF non è incluso in W90: richiede un ulteriore motore LaTeX/PDF e una diversa
matrice di errori e dipendenze.

### Scegli le References

Sono disponibili tre scope.

#### References cited in the current document

Include soltanto le fonti citate, nell'ordine della prima occorrenza. Se il
documento non contiene citazioni Pandoc, l'operazione viene bloccata.

#### All References

Include tutte le schede valide di `references.md`, nell'ordine canonico della
biblioteca. Nel prodotto documento, Calamus aggiunge alla copia temporanea il
metadato `nocite: @*`, così citeproc può inserire anche le fonti non citate.

#### One Reference Set

Include i membri di un set statico nell'ordine memorizzato. Reference Set names are case-sensitive: `Core sources` e `Core Sources` non sono lo stesso nome.
Calamus richiede la grafia esatta. Lo stile CSL può comunque scegliere un ordine
bibliografico finale diverso, per esempio alfabetico.

Per il prodotto documento, il set deve contenere tutte le fonti realmente citate.
Se manca anche una sola key, Calamus mostra quali citazioni sarebbero escluse e
non avvia Pandoc.

### Scegli lo stile CSL

Lascia **Use Pandoc Default** per usare lo stile predefinito di Pandoc, oppure
scegli un file `.csl` locale. Il file deve essere regolare, non un collegamento
simbolico, e non può superare 4 MiB. Lo stile viene letto ma non copiato nella
biblioteca Calamus.

Uno stile CSL può modificare punteggiatura, ordine, abbreviazioni e
capitalizzazione visuale. Questa trasformazione riguarda soltanto l'output: il
titolo conservato in References non cambia.

### Scegli la destinazione

Il nome proposto distingue i due prodotti:

```text
paper-bibliography.txt
paper-with-citations.docx
```

L'estensione deve corrispondere al formato scelto. La destinazione non può
sostituire References, Reference Sets, il documento corrente, le sue Source Notes
o il CSL selezionato. Un collegamento simbolico non viene accettato.

Se il file esiste, il dialogo chiede conferma, ma la sostituzione finale avviene
soltanto se quel file è rimasto identico dopo la preview.

### Leggi la semantic preview

Prima dell'export finale Calamus mostra una semantic preview in testo semplice.
Non è un'anteprima grafica di DOCX, ODT o EPUB. Serve a controllare:

- percorso e versione di Pandoc;
- prodotto, scope e Reference Set;
- numero e ordine delle key;
- formato e destinazione;
- stile CSL;
- warning della proiezione BibLaTeX;
- warning restituiti da Pandoc;
- contenuto bibliografico elaborato da citeproc.

Premi **Export** soltanto se fonti e contenuto sono corretti. **Cancel** non crea
il file finale.

### Cosa significa stale

Calamus congela un piano esatto prima della preview. Se nel frattempo cambia una
Reference, il set, il buffer, il file salvato, il CSL, Pandoc, la destinazione o
la cartella di destinazione, il piano diventa stale. L'export viene annullato e
il file preesistente viene conservato.

Riapri il comando, controlla la nuova preview e conferma un nuovo piano. Non
cercare di aggirare questo controllo: protegge da sovrascritture e risultati
costruiti con input non più coerenti.

### Sicurezza del processo e della scrittura

Calamus avvia Pandoc senza shell e con argomenti chiusi. Non permette custom
arguments, template, filtri Lua, CSS, profili persistenti o estensioni arbitrarie.
I file temporanei sono privati. Pandoc scrive prima in uno staging file nella
cartella di destinazione; Calamus pubblica il risultato soltanto dopo exit code
zero, output non vuoto, fsync e secondo controllo stale.

Remote images or media non sono accettati nel prodotto documento, perché Pandoc
potrebbe tentare un accesso di rete. Un normale collegamento Web è consentito e
rimane un collegamento nell'output. Usa file locali per immagini e media.

Durante una conversione puoi premere **Cancel**. Chiudere Calamus con X,
`File → Quit` o `Ctrl+Q` richiede la terminazione del processo Pandoc e del worker
prima di completare la chiusura.

### Esempio: bibliografia di un Reference Set

1. Apri `Research → Export with Pandoc/citeproc…`.
2. Scegli **Formatted Bibliography**.
3. Scegli **One Reference Set**.
4. Seleziona esattamente `Core sources`.
5. Scegli **OpenDocument Text**.
6. Usa lo stile predefinito oppure un CSL locale.
7. Salva come `core-sources-bibliography.odt`.
8. Controlla key, conteggio e semantic preview.
9. Conferma **Export**.
10. Apri l'ODT con il programma esterno abituale.

### Esempio: documento DOCX con citazioni

Documento:

```markdown
# Introduzione

La fede cristiana possiede una struttura ecclesiale
[@ratzinger1968, pp. 42-44].
```

Workflow:

1. salva il documento;
2. scegli **Current Document with Citations**;
3. scegli **References cited in the current document**;
4. scegli **Microsoft Word**;
5. controlla che `ratzinger1968` compaia nella preview;
6. salva come `capitolo-with-citations.docx`;
7. conferma l'export;
8. verifica esternamente citazione e bibliografia.

Il Markdown originale, `references.md`, Reference Sets e Source Notes devono
rimanere byte-identici.

### Errori e recupero

#### Pandoc non è disponibile

Installa Pandoc con il metodo previsto dalla distribuzione, chiudi e riapri il
workflow. Calamus non modifica il sistema e non scarica binari.

#### Versione non supportata

Aggiorna Pandoc almeno alla versione minima indicata dal messaggio. Non sostituire
l'eseguibile durante una preview già aperta.

#### Citation refers to a missing Reference

Apri References e crea o correggi la scheda. Se la key è stata rinominata, usa
Rename Reference Key o aggiungi l'alias appropriato; poi esegui Research Check.

#### Il Reference Set omette una citazione

Aggiungi la Reference al set oppure scegli **References cited in the current
document** o **All References**. Non eliminare la citazione per forzare l'export.

#### BibLaTeX mapping warnings

Alcuni campi locali non hanno una corrispondenza perfetta. Controlla l'anteprima.
La correzione va fatta nella scheda Reference, non nel `.bib` temporaneo.

#### Pandoc restituisce un errore

Leggi stderr nel messaggio. Il file finale non viene accettato. Correggi il
documento, il CSL o i metadati e ripeti il workflow.

#### Output stale

Qualcosa è cambiato dopo la preview. Il file esterno eventualmente creato da un
altro programma è stato preservato. Riparti dal comando e genera un nuovo piano.

#### Conversione troppo lunga

Attendi il limite o premi Cancel. Calamus termina il processo esatto e rimuove lo
staging. Per lavori eccezionalmente complessi usa Pandoc direttamente fuori da
Calamus: W90 non è un frontend generale a ogni opzione Pandoc.

### Checklist W90

Prima di confermare:

- documento salvato e citazioni valide;
- Research Check senza errori bloccanti;
- prodotto e scope corretti;
- Reference Set selezionato con case esatto;
- stile CSL locale corretto;
- nessun media remoto;
- destinazione distinta dalle autorità;
- semantic preview controllata;
- warning compresi;
- formato finale appropriato.

## Keyboard Shortcuts and About

`Help → Keyboard Shortcuts` shows the current command registry. `Help → About` shows application identity, purpose and licensing information.
