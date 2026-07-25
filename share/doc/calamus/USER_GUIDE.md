# Calamus User Guide

Calamus is a lightweight, offline-first editor for plain-text and Markdown writing. This guide explains the visible commands and gives practical examples. The guide is part of the Calamus source and must be updated whenever a work item adds or changes a user-visible feature.

## A practical Research workflow

Example project:

- document: `~/Documents/Book/Chapter-01.md`
- global References authority: `$XDG_DATA_HOME/calamus/research/references.md`
- document Source Notes authority: `~/Documents/Book/Chapter-01.md.source-notes.md`

A typical path is:

1. Save the document as `~/Documents/Book/Chapter-01.md`.
2. Open `Research → References` and add a source with a stable key such as `ratzinger1968`.
3. Open `Research → Source Notes` and add a note linked to `ratzinger1968` and, when useful, to a document heading such as `#introduction`.
4. Place the cursor where the citation belongs and use `Research → Quick Cite…` to insert `[@ratzinger1968]`.
5. Use `Research → Research Check…` before exporting to find missing citation keys, broken targets, duplicate aliases and tag-identity collisions.
6. Use `Research → Tag Integrity…` to inspect, rename, merge, remove or normalize Research tags without changing the document text.
7. Use `Research → Import BibTeX/BibLaTeX…` when a trusted `.bib` library must be reviewed and merged into `references.md`.
8. Use `Research → Export References as BibTeX/BibLaTeX…` to create a derived `.bib` file for another bibliographic tool.
9. Use `Research → Export Research Apparatus…` to create a derived Markdown dossier or one of its component reports.

The document, `references.md` and the document Source Notes sidecar remain separate authorities. Derived reports are not authorities and may be regenerated.

## Research Panel

`Research → Research Panel` opens the right-side Research workspace. It hosts the currently selected Research client, such as References or Source Notes.

Practical example: while editing `Chapter-01.md`, open the Research Panel, select References, then double-click or activate a source to inspect it without leaving the document.

## References

`Research → References` manages the global Markdown reference library. References are stored in:

`$XDG_DATA_HOME/calamus/research/references.md`

When `XDG_DATA_HOME` is not set, the usual location is:

`~/.local/share/calamus/research/references.md`

Use stable, readable keys such as `guardini1950` or `ratzinger1968`. These keys are inserted into Pandoc-style citations and linked from Source Notes.

Practical example: add Joseph Ratzinger, *Introduction to Christianity*, key `ratzinger1968`, and tags `faith`, `theology`.

## Source Notes

`Research → Source Notes` manages notes belonging to the current saved document. For:

`~/Documents/Book/Chapter-01.md`

Calamus stores the sidecar at:

`~/Documents/Book/Chapter-01.md.source-notes.md`

A Source Note may contain a quotation, paraphrase or comment, a Reference key, a page locator, tags and a target heading.

Practical example: create a quotation note linked to `ratzinger1968`, page `42`, target `#introduction`, with the tag `faith`.

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

## Keyboard Shortcuts and About

`Help → Keyboard Shortcuts` shows the current command registry. `Help → About` shows application identity, purpose and licensing information.
