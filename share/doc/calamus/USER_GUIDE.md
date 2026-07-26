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
8. Use `Research → Research Check…` before exporting to find missing citation keys, broken targets, duplicate aliases and tag-identity collisions.
9. Use `Research → Tag Integrity…` to inspect, rename, merge, remove or normalize Research tags without changing the document text.
10. Use `Research → Import BibTeX/BibLaTeX…` when a trusted `.bib` library must be reviewed and merged into `references.md`.
11. Use `Research → Export References as BibTeX/BibLaTeX…` to create a derived `.bib` file for another bibliographic tool.
12. Use `Research → Export Research Apparatus…` to create a derived Markdown dossier or one of its component reports.

The document, `references.md` and the document Source Notes sidecar remain separate authorities. Derived reports are not authorities and may be regenerated.

## Research Panel

`Research → Research Panel` opens the right-side Research workspace. It hosts the currently selected Research client: Clips, References, Source Notes or Authoring Bridge.

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

## Keyboard Shortcuts and About

`Help → Keyboard Shortcuts` shows the current command registry. `Help → About` shows application identity, purpose and licensing information.
