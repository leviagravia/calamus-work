# Calamus User Guide

Calamus is a lightweight, offline-first editor for plain-text and Markdown writing. This guide explains the visible commands and gives practical examples. The guide is part of the Calamus source and must be updated whenever a work item adds or changes a user-visible feature.

## Learning the Research apparatus

The Research apparatus is easiest to learn when each object has one clear job. Calamus deliberately keeps the document, bibliography and notes separate so that every file remains readable, portable and recoverable.

### The five objects you must distinguish

| Object | What it is | Where it lives | What it is for |
|---|---|---|---|
| **Reference** | One bibliographic record identified by a stable key such as `ratzinger1968` | Global `references.md` | Describes a source once: author, title, date, publisher, tags and related metadata |
| **Citation** | A Pandoc citation marker such as `[@ratzinger1968]` inside the manuscript | Current document | Shows where a source is cited in the prose |
| **Source Note** | A quotation, paraphrase or research comment with its own stable ID | Document sidecar `Document.md.source-notes.md` | Preserves research material and its provenance without inserting it into the manuscript |
| **Document Target** | An explicit heading identifier such as `#introduction` created by `## Introduction {#introduction}` | Current document | Connects a Source Note or internal link to a precise section of the manuscript |
| **Backlink** | A read-only result calculated from the files above | Nowhere: it is derived on demand | Answers questions such as “Where is this Reference cited?” or “Which notes belong to this section?” |

A Reference is not a citation. A citation is not a Source Note. A Source Note may point both to a Reference and to a document heading, but neither relationship is mandatory for a **Comment** note. Backlinks are never stored and never become a fourth authority.

### Three rules that prevent most mistakes

1. **Create the Reference before creating quotations or paraphrases.** Quote and Paraphrase notes require a valid Reference key.
2. **Give important headings explicit IDs.** Write `## Method {#method}` rather than relying on an automatically generated slug. Calamus offers only explicit, unique IDs as stable targets.
3. **Refresh derived views after an authority changes.** Authoring Bridge is a snapshot. After editing the document, References or Source Notes, press **Refresh** before opening an old result.

### Which command should I use?

| Your intention | Use this command |
|---|---|
| Register a book, article or archival source | `Research → References` |
| Save a quotation, paraphrase or research observation | `Research → Source Notes` |
| Turn selected manuscript text into a note without retyping it | `Research → Create Source Note from Selection…` |
| Insert a citation key in the manuscript | `Research → Quick Cite…` |
| Link prose to a stable section of the same document | `Research → Insert Link to Heading…` |
| See every citation and note connected to a source | `Research → Authoring Bridge → Backlinks by Reference` |
| See every link and note connected to a section | `Research → Authoring Bridge → Backlinks by Heading` |
| Find missing keys, missing targets or ambiguous heading IDs | `Research → Authoring Bridge → Broken Research Links` |
| Audit the whole Research apparatus for consistency | `Research → Research Check…` |
| Standardize Research tags | `Research → Tag Integrity…` |
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

Calamus will later keep the document-specific research notes beside this file in:

`tradition-and-renewal.md.source-notes.md`

Do not create or edit that sidecar manually while Calamus is using it.

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
4. Review tag variants in Tag Integrity.
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

Use `Research → Tag Integrity…`. Calamus treats Unicode-normalized, whitespace-collapsed, case-insensitive variants as one logical identity and lets you review the impact before rewriting them.

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
11. Use `Research → Tag Integrity…` to inspect, rename, merge, remove or normalize Research tags without changing the document text.
12. Use `Research → Import BibTeX/BibLaTeX…` when a trusted `.bib` library must be reviewed and merged into `references.md`.
13. Use `Research → Export References as BibTeX/BibLaTeX…` to create a derived `.bib` file for another bibliographic tool.
14. Use `Research → Export Research Apparatus…` to create a derived Markdown dossier or one of its component reports.

The document, `references.md` and the document Source Notes sidecar remain separate authorities. Derived reports are not authorities and may be regenerated.

## Research Panel

`Research → Research Panel` opens the right-side Research workspace. It hosts the currently selected Research client: Clips, References, Reference Sets, Source Notes or Authoring Bridge.

Practical example: while editing `Chapter-01.md`, open the Research Panel, select References, then double-click or activate a source to inspect it without leaving the document.

## References

`Research → References` manages the global Markdown reference library. References are stored in:

`$XDG_DATA_HOME/calamus/research/references.md`

When `XDG_DATA_HOME` is not set, the usual location is:

`~/.local/share/calamus/research/references.md`

Use stable, readable keys such as `guardini1950` or `ratzinger1968`. These keys are inserted into Pandoc-style citations and linked from Source Notes.

Practical example: add Joseph Ratzinger, *Introduction to Christianity*, key `ratzinger1968`, and tags `faith`, `theology`.

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

## Guida canonica completa del pannello Research (Scratchpad escluso)

Questa è la guida operativa completa dell’apparato Research di Calamus. È pensata per chi scrive saggi, articoli, tesi, omelie documentate, libri o ricerche teologiche e desidera lavorare con fonti, citazioni e note senza affidare il proprio materiale a un database opaco.

La guida dello **Scratchpad** sarà aggiunta in seguito. Tutto ciò che segue riguarda le funzioni Research già disponibili: Clip Collection, References, Related References, Reference Sets, Source Notes, Create Source Note from Selection, Insert Link to Heading, Authoring Bridge, Quick Cite, Open Citation in References, Rename Reference Key, Research Check, Tag Integrity, import/export BibTeX o BibLaTeX ed Export Research Apparatus.

Le etichette dei menu e dei pulsanti sono riportate in inglese perché corrispondono all’interfaccia reale. Le spiegazioni sono in italiano.

### 1. Prima idea fondamentale: Research non è un unico archivio

Il pannello Research presenta più strumenti nello stesso spazio laterale, ma i dati non appartengono tutti allo stesso file. Questa separazione è intenzionale: rende ogni informazione leggibile, esportabile e recuperabile anche senza Calamus.

Le autorità sono quattro:

1. **Documento attivo**: il file `.md` o `.txt` che stai scrivendo. Contiene il testo, le citazioni Pandoc e gli eventuali link interni alle intestazioni.
2. **References**: la biblioteca globale in `references.md`. Contiene una sola scheda canonica per ogni fonte.
3. **Source Notes**: il sidecar del documento, per esempio `Chapter-01.md.source-notes.md`. Contiene note di lettura appartenenti a quel documento.
4. **Reference Sets**: il file globale `reference-sets.md`. Contiene liste statiche e ordinate di citation key.

Authoring Bridge, Research Check e gli export sono **proiezioni derivate**: leggono le autorità e mostrano o producono risultati. Non diventano una quinta autorità e non conservano un grafo o un indice nascosto.

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

reference-sets.md
    └── insiemi statici di citation key

Authoring Bridge / Research Check / Export
    └── risultati ricostruiti leggendo i quattro file
```

Questa mappa risolve molti dubbi:

- una Reference non è una citazione;
- una citazione non è una Source Note;
- un Related Reference non è un membro di set;
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

Le Source Notes stanno accanto al documento:

```text
~/Documents/Libro/Capitolo-01.md
~/Documents/Libro/Capitolo-01.md.source-notes.md
```

Questo significa che un backup serio deve includere:

- i documenti `.md` e `.txt`;
- tutti i sidecar `.source-notes.md`;
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

3. Apri `Research → References` e registra due o tre fonti.
4. Inserisci una prima citazione con `Research → Quick Cite…`.
5. Crea una Source Note da una frase selezionata.
6. Collega la Source Note a una Reference e, quando utile, a una heading del documento.
7. Apri `Research → Authoring Bridge` per vedere citazioni, note e link derivati.
8. Crea una relazione esplicita tra due References solo se esiste un motivo scientifico.
9. Crea un Reference Set per il lavoro corrente.
10. Esegui `Research → Research Check…`.
11. Correggi errori e warning.
12. Esporta soltanto alla fine.

Questo itinerario è il modo più semplice per apprendere il sistema: prima le autorità, poi i collegamenti, infine i controlli e gli export.

### 4. Aprire, cambiare e chiudere il Research Panel

`Research → Research Panel` oppure `Ctrl+Alt+C` mostra o nasconde il pannello destro.

I client disponibili sono:

- **Clip Collection**;
- **References**;
- **Reference Sets**;
- **Source Notes**;
- **Authoring Bridge**.

Quando scegli uno di questi comandi, Calamus apre il pannello se necessario e mostra il client richiesto. Il pulsante `X` nell’intestazione nasconde il pannello attraverso lo stesso gateway del menu: non elimina dati e non chiude il documento.

Buona abitudine: tieni aperto un solo client alla volta e usa il menu Research per cambiare contesto. Il pannello è uno spazio di lavoro, non una seconda finestra indipendente.

### 5. Clip Collection: frammenti riutilizzabili, non fonti

`Research → Clip Collection` gestisce piccoli frammenti testuali da conservare e reinserire. È utile per formule ricorrenti, schemi, clausole, richiami pastorali, abbreviazioni o strutture Markdown.

Esempi di clip:

```text
Titolo: Citazione lunga
Testo:
> Testo della citazione.
>
> — Autore, Opera, pagina
```

```text
Titolo: Schema conclusione
Testo:
In sintesi, il percorso svolto consente di affermare tre risultati:
1.
2.
3.
```

Usa Clip Collection per testo riutilizzabile. Non usarla per sostituire References o Source Notes:

- una clip non possiede identità bibliografica;
- non viene controllata da Research Check come fonte;
- non genera backlink;
- non deve diventare un deposito indistinto di appunti di lettura.

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

### 10. Create Source Note from Selection

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

### 11. Insert Link to Heading

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

### 12. Quick Cite: inserire citazioni senza ricordare le key

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

### 13. Open Citation in References

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

### 14. Rename Reference Key: una migrazione controllata

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

### 15. Authoring Bridge: leggere le relazioni derivate

Authoring Bridge è una mappa ricostruita dai file attuali. Non salva backlink e non mantiene un indice persistente.

Modalità disponibili:

- **By Reference**: occorrenze legate a una Reference;
- **By Heading**: elementi legati a una heading;
- **Related References**: relazioni esplicite tra References;
- **Broken Research links**: problemi navigabili.

#### 15.1 By Reference

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

#### 15.2 By Heading

Scegli una heading per vedere:

- link Markdown diretti a quell’ID;
- Source Notes con quel Document Target;
- diagnostica della struttura.

È utile per verificare se una sezione possiede fonti e note sufficienti prima della redazione.

#### 15.3 Related References

Scegli una Reference e naviga le relazioni esplicite. Il conteggio deriva da `references.md` e deve aggiornarsi dopo **Refresh**.

#### 15.4 Broken Research links

Questa modalità raccoglie problemi come:

- citation key assente;
- Source Note con Reference mancante;
- link a heading inesistente;
- Source Note target mancante;
- heading ambigua o priva di identità utilizzabile.

Usala come elenco operativo: apri un problema, correggi l’autorità proprietaria, poi premi **Refresh**.

### 16. Research Check: controllo complessivo

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

### 17. Tag Integrity: rinominare e unificare tag senza sostituzioni cieche

`Research → Tag Integrity…` analizza i tag di References e Source Notes.

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

### 18. Import BibTeX/BibLaTeX

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

### 19. Export References as BibTeX/BibLaTeX

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

### 20. Export Research Apparatus

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

### 21. Gestire modifiche esterne e stato stale

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

### 22. Esempio completo: costruire un articolo teologico

Progetto:

```text
Titolo: Tradizione e rinnovamento nella vita parrocchiale
Documento: Tradizione-Rinnovamento.md
```

#### 22.1 Registra le fonti

```text
ratzinger1968 — Introduction to Christianity
newman1870 — An Essay on the Development of Christian Doctrine
lubac1949 — Catholicism
```

#### 22.2 Crea una relazione

```text
ratzinger1968 ↔ newman1870
```

Motivo: entrambe le opere aiutano a comprendere continuità, sviluppo e identità della fede.

#### 22.3 Crea i set

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

#### 22.4 Crea Source Notes

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

#### 22.5 Scrivi con Quick Cite

```markdown
    ## Fondamenti teologici {#fondamenti-teologici}

La tradizione cristiana non coincide con una ripetizione immobile del passato
[@ratzinger1968, p. 52]. Il concetto di sviluppo permette di comprendere una
continuità capace di crescita [@newman1870, p. 40]. La dimensione ecclesiale
impedisce di ridurre questo processo a una scelta puramente individuale
[@lubac1949, pp. 101-103].
```

#### 22.6 Verifica con Authoring Bridge

- By Reference: ogni fonte deve mostrare le occorrenze previste;
- By Heading: `#fondamenti-teologici` deve mostrare le Source Notes collegate;
- Related References: `ratzinger1968` deve mostrare `newman1870`;
- Broken Research links: nessun risultato inatteso.

#### 22.7 Esegui Research Check

Risultato ideale:

```text
0 errors
0 warnings
advisories comprese e giustificate
```

#### 22.8 Esporta

1. genera il `.bib` derivato;
2. genera il Complete Research Dossier;
3. conserva gli export nella cartella `Exports`;
4. continua a correggere i dati soltanto nelle autorità canoniche.

### 23. Workflow per diversi tipi di lavoro

#### 23.1 Articolo breve

- 5-15 References;
- un set `Core sources`;
- Source Notes collegate alle 3-5 heading principali;
- Quick Cite durante la redazione;
- Research Check prima della consegna.

#### 23.2 Capitolo di libro o tesi

- References globali riutilizzate tra capitoli;
- un sidecar Source Notes per capitolo;
- set distinti per capitolo o funzione;
- heading ID stabili;
- dossier Research per revisione e supervisione.

#### 23.3 Omelia o conferenza documentata

- set `Testi biblici`, `Padri`, `Magistero`, `Studi`;
- Source Notes brevi con locator;
- tag per tema pastorale;
- export della bibliografia o dossier per l’archivio.

#### 23.4 Ricerca esplorativa

- References con annotation chiare;
- tag `da-leggere`, `letto`, `da-verificare`;
- set temporanei per domande specifiche;
- evitare relazioni inferite: aggiungere Related References solo dopo una lettura reale.

### 24. Errori comuni e recupero

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

#### Ho modificato un export pensando che fosse la libreria

Riporta la correzione in References e rigenera l’export. Il file derivato non è l’autorità.

#### Research Check mostra References non usate

È un’advisory, non necessariamente un errore. Decidi se la fonte è preparatoria, appartiene a un altro capitolo o può essere rimossa.

### 25. Disciplina consigliata per una biblioteca che cresce

1. Registra una fonte una sola volta.
2. Usa key stabili e leggibili.
3. Compila soltanto metadati verificati.
4. Usa Annotation per valutare l’opera, Source Notes per estratti e idee puntuali.
5. Usa tag coerenti e periodicamente esegui Tag Integrity.
6. Collega Related References soltanto quando sai spiegare il rapporto.
7. Crea set con uno scopo operativo chiaro.
8. Usa heading ID stabili nei documenti lunghi.
9. Esegui Research Check prima di export, consegna o archiviazione.
10. Conserva backup di documenti, sidecar e file globali Research.
11. Tratta gli export come prodotti rigenerabili.
12. Non modificare simultaneamente le stesse autorità in Calamus e in un editor esterno.

### 26. Checklist finale prima di consegnare un lavoro

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

Relations and Sets:

- Related References sono motivate e simmetriche;
- i set contengono membri esistenti;
- nomi, descrizioni e ordine sono corretti;
- nessuna vecchia key è rimasta dopo una rinomina.

Integrity and export:

- Research Check non presenta errori;
- warning compresi e risolti o motivati;
- Tag Integrity eseguita quando necessario;
- `.bib` e dossier rigenerati dopo le ultime correzioni.

### 27. Glossario essenziale

- **Authority**: file che possiede un dato e può essere modificato come fonte canonica.
- **Reference**: scheda bibliografica globale.
- **Citation key**: identità stabile di una Reference.
- **Alias**: key precedente o alternativa che risolve alla key primaria.
- **Citation**: marker Pandoc nel documento.
- **Source Note**: nota di lettura appartenente a un documento.
- **Sidecar**: file compagno del documento.
- **Locator**: pagina, capitolo, sezione o paragrafo della fonte.
- **Document Target**: heading ID a cui una Source Note è collegata.
- **Related Reference**: relazione esplicita e simmetrica tra due fonti.
- **Reference Set**: lista statica, nominata e ordinata di References.
- **Projection**: risultato calcolato leggendo le autorità senza diventare autorità.
- **Stale**: stato in cui un file è cambiato dopo il caricamento o la preview.
- **Impact preview**: piano dettagliato delle modifiche prima della scrittura.
- **Derived export**: file prodotto dalle autorità e rigenerabile.

### 28. Regola conclusiva

Il Research Panel funziona bene quando ogni informazione viene collocata nel posto giusto:

```text
Dati bibliografici        → References
Citazione nel testo       → documento
Estratto o idea puntuale  → Source Notes
Rapporto tra due opere    → Related References
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
