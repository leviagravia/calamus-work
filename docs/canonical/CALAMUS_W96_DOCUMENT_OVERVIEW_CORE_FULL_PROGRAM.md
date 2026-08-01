# Calamus W96 — Document Overview Core / Document Overview Full

**Status:** binding implementation programme
**Published baseline:** `792ca0f76db39525a9052bd61e43fe929988af2e`
**Visible name:** Document Overview
**Internal architecture name:** Document Dossier

## 1. Product identity and permanent architectural rule

Document Overview is the operational projection of the current document. It is
not a document store, project manager, collection manager, second editor,
database, hidden index or knowledge graph.

The permanent flow is:

```text
current editor buffer
+ current document identity
+ Document Structure
+ bookmarks and internal links
+ Source Notes sidecar
+ references.md
+ Related References
+ reference-sets.md
+ Research Check
+ existing statistics
              ↓
     Document Dossier projection
              ↓
 navigation, context and delegated actions
```

Neither Core nor Full may persist a parallel dossier. Every classification is
recomputed from explicit authorities.

## 2. Two-phase product programme

Document Overview is divided into two independently authorized product phases:

1. **W96 — Document Overview Core** — implemented now and published as one
   complete work item.
2. **Document Overview Full** — evaluated only after W99. It receives no work
   item number and no automatic authorization now.

Core must already be a complete and useful feature, not a placeholder. Full is
an optional expansion of interaction depth and coordinated workflows.

---

# PART I — W96 DOCUMENT OVERVIEW CORE

## 3. Core objective

Core gives the user one non-modal, navigable, read-oriented control surface for
the open document. It answers:

- What document is open and is it modified?
- How is it structured?
- Where are citations, notes, bookmarks and internal links?
- Which references are actually relevant to this document?
- Which Related References and Reference Sets expand that immediate research
  context?
- Which explicit integrity problems exist?
- What are the descriptive statistics of the document and its sections?

Core never performs autonomous document or research-data mutation.

## 4. Core information architecture

Core has five fixed categories:

```text
Document Overview Core
├── Overview
├── Structure
├── Research
├── Integrity
└── Statistics
```

Visible entry point:

```text
Navigate → Document Overview
```

There is no duplicate Research-menu item and no shortcut is assigned before a
complete shortcut collision audit.

## 5. Core window and lifecycle

The Core UI is:

- one App-owned auxiliary window;
- non-modal;
- single-instance;
- no tabs;
- category navigator on the left;
- selected-category list/detail surface on the right;
- explicit Refresh and Close controls;
- focus returned to the editor after navigation or close;
- destroyed and disconnected on normal App shutdown;
- recreated with a fresh snapshot after close/reopen.

The window is not a permanent panel and not another editor surface.

## 6. Core GTK-free model

Core owns immutable, temporary Python values only:

- `DocumentDossierInputs`
- `DocumentDossierIdentity`
- `DocumentDossierAuthorityStamp`
- `DocumentDossierCapabilities`
- `DocumentDossierCounts`
- `DocumentDossierSection`
- `DocumentDossierBookmark`
- `DocumentDossierLink`
- `DocumentDossierCitation`
- `DocumentDossierSourceNote`
- `DocumentDossierReference`
- `DocumentDossierReferenceSet`
- `DocumentDossierIssue`
- `DocumentDossierStatistics`
- `DocumentDossierSnapshot`

The model and controller import no GTK/GDK/GIO symbols.

## 7. Core Overview category

Overview displays:

- document name;
- controlled path or Untitled state;
- saved/modified state;
- word and character counts;
- section count;
- bookmark and internal-link counts;
- citation and Source Note counts;
- distinct relevant-reference count;
- Related Reference count;
- collected-but-unused relevant-reference count;
- pertinent Reference Set count;
- error, warning and advisory counts;
- last explicit refresh time.

Overview contains no editing controls.

## 8. Core Structure category

Structure displays explicit Markdown structure derived from the live buffer:

- ATX heading hierarchy;
- stable explicit heading identifier when present;
- deterministic fallback identity by line when no explicit identifier exists;
- heading line and offsets;
- short read-only section excerpt;
- words per section;
- citations per section;
- Source Notes targeted to the section;
- bookmarks per section;
- incoming and outgoing explicit heading links.

Core navigation actions:

- Go to Section;
- Go to Bookmark;
- Go to Link Source;
- Go to Link Destination.

All navigation is sent through the existing navigation gateway. Structure does
not parse headings independently from `DocumentStructure`.

## 9. Core Research category

Research is deliberately unified in Core. It contains four groups.

### 9.1 Citations

For each explicit Pandoc citation:

- raw citation text;
- line and exact offsets;
- containing section;
- requested keys;
- resolved canonical keys;
- missing keys;
- ambiguous keys.

Actions are read/navigation only:

- Go to Citation;
- Show Reference when uniquely resolved;
- open the relevant Research Panel surface.

### 9.2 Source Notes

For each Source Note of the current document:

- stable note ID;
- kind;
- excerpt;
- requested and canonical reference key;
- locator;
- heading target;
- containing/target section;
- complete, incomplete or orphan status.

Actions:

- Open Source Note;
- Go to target section;
- Show Reference.

Core does not edit or insert Source Notes.

### 9.3 Document-relevant references

Core includes all of the following derived roles:

- **cited** — referenced by a citation in the current buffer;
- **source-note** — referenced by the current document Source Notes sidecar;
- **related** — one bounded, explicit, symmetric Related References expansion
  from cited/source-note records;
- **reference-set** — member of a pertinent Reference Set;
- **collected-unused** — relevant through Related References or a pertinent set
  but not yet cited and not used by a Source Note;
- **missing** — an unresolved or ambiguous requested key.

For each resolved record Core shows:

- canonical key;
- title;
- author/year;
- roles;
- citation count;
- Source Note count;
- Related References that brought it into scope;
- pertinent Reference Sets containing it.

The complete global library is not shown. A record wholly unrelated to the
current document is excluded.

### 9.4 Pertinent Reference Sets

A set is pertinent when at least one uniquely resolved member intersects the
current relevance closure:

```text
cited/source-note references
        + one Related References expansion
```

Core displays:

- set name and description;
- resolved members;
- members already relevant before the set expansion;
- missing or ambiguous members;
- members brought into context by the set and not yet used.

Actions:

- Open Reference Set;
- Show a member Reference.

Core does not create, edit or reorder sets.

## 10. Core Integrity category

Core projects the existing `ResearchCheckReport` and structure/link status.
It does not create a competing check engine.

Displayed classes include:

- unresolved or ambiguous citations;
- incomplete Source Notes;
- orphan Source Note targets;
- missing/ambiguous heading links;
- structure diagnostics;
- Related References problems;
- Reference Set missing/ambiguous/alias members;
- tag and authority diagnostics already produced by Research Check;
- collected-but-unused references that are relevant to this document.

Global-library `reference-unused` advisories for completely unrelated records
are filtered out of the current-document dossier.

Severities remain exactly:

- Error;
- Warning;
- Advisory.

No quality score, automatic repair or prose evaluation is introduced.

## 11. Core Statistics category

Core reuses `document_statistics()` and adds deterministic dossier counts:

- words;
- characters;
- characters without spaces;
- paragraphs;
- lines;
- estimated reading minutes;
- sections;
- citations;
- Source Notes;
- distinct relevant references;
- Related References;
- collected-but-unused relevant references;
- pertinent Reference Sets;
- issues by severity;
- words, citations, notes, bookmarks and link counts per section;
- sections with zero citations;
- sections with zero Source Notes.

These are descriptive values only.

## 12. Core refresh and authority policy

Core refreshes:

- when the window opens;
- when the current document changes;
- after Save;
- through the Refresh button;
- after a delegated read/navigation action known to expose changed context;
- when explicitly marked stale by the App runtime.

Core uses an authority stamp containing:

- current document path;
- live-buffer SHA-256 signature or equivalent deterministic revision;
- modified flag;
- document file token when available;
- Source Notes token;
- References token;
- Reference Sets token.

Core has no watcher, timer or polling loop.

Because Core is read/navigation-oriented, a changed authority triggers a fresh
snapshot before further use. No multi-authority write transaction is required.

## 13. Core behaviour for unsaved and modified documents

For an untitled document:

- structure, citations, links and statistics remain available from the buffer;
- Source Notes are unavailable because no sidecar identity exists;
- unavailable actions are disabled with a concise explanation.

For a modified saved document:

- live buffer is authoritative for structure, citations, links and statistics;
- sidecar/global authorities remain filesystem snapshots;
- Overview visibly reports the modified state.

## 14. Core explicit exclusions

Core does not include:

- direct text editing;
- Source Note editing or insertion;
- Quick Cite insertion;
- Reference CRUD;
- Rename Reference Key;
- export workflows;
- coordinated multi-authority writes;
- rollback logic;
- persistent dossier state;
- database, graph, vector or full-text index;
- AI/NLP, automatic summaries, semantic tags or inferred outline;
- Scratchpad integration;
- continuous synchronization;
- project or document-collection management.

## 15. Core implementation gates

### Gate A — model and deterministic projection

- immutable GTK-free model;
- live-buffer structure/citations/links/statistics;
- bookmarks;
- Source Notes projection;
- cited/source-note/related/set/missing classification;
- pertinent sets;
- integrity projection and local filtering;
- authority stamp;
- pure refresh controller;
- real-file and hostile unit tests;
- full headless regression.

### Gate B — GTK view and navigation

- Navigate menu command;
- single-instance non-modal window;
- five categories;
- summary/list/detail rendering;
- selection and Refresh;
- navigation gateways;
- untitled/modified behaviour;
- focus and lifecycle tests;
- no document mutation.

### Gate C — Research opening actions, Help and final validation

- Open Source Note;
- Show Reference;
- Open Reference Set;
- open exact Research Panel surface;
- current-build identity;
- complete User Guide;
- source provenance and boundary gates;
- full regression;
- all historical GTK lanes;
- W96 True App gate;
- isolated desktop candidate and final manual validation.

W96 publishes only once, after Gates A–C all pass.

---

# PART II — DOCUMENT OVERVIEW FULL

## 16. Authorization and timing

Document Overview Full is not W96 and is not automatically authorized. It is
only evaluated after W99 during backlog review, alongside Scratchpad Full.

It may receive a future W100+ number only after explicit user authorization.

## 17. Full objective

Full deepens interaction while preserving the same derived-authority model.
It may separate the Research category into richer domain-specific surfaces and
add certified delegated actions, but it still does not become an editor or
store.

Proposed Full categories:

```text
Document Overview Full
├── Overview
├── Structure
├── Notes
├── Bibliography
├── Integrity
├── Statistics
└── optional Scratchpad context (only after separate authorization)
```

## 18. Full Notes category

Potential additions:

- richer Source Note filtering by kind, section, reference and status;
- complete note detail;
- Show Uses;
- Insert Source Note through the certified controller;
- Edit Source Note by opening the owned editor/dialog;
- status-resolution workflows for incomplete/orphan notes;
- batch navigation through notes;
- distribution and coverage by section.

Document Overview Full still does not own Source Note persistence.

## 19. Full Bibliography category

Potential additions:

- separate cited, Source-Note, Related, pertinent-set and collected-unused
  filters;
- complete Show Uses across document, notes, relationships and sets;
- Quick Cite through the certified citation controller;
- Copy Key;
- Open Related References;
- open/edit via the future Bibliography Manager;
- export current-document bibliography or research apparatus;
- impact preview before any coordinated operation;
- stale revalidation before mutating delegates.

The future W97 Bibliography Manager remains the owner of library CRUD.

## 20. Full Integrity workflows

Potential additions:

- filter/sort by severity, authority and section;
- guided traversal of unresolved items;
- open the exact owner tool for repair;
- re-run targeted checks after a repair;
- readiness checklist for final document review;
- explicit before/after refresh state.

Full may coordinate existing checks but may not silently repair or invent a
quality score.

## 21. Full coordinated-action contract

Any mutating Full action must:

1. compare complete authority tokens/revisions;
2. block on stale data;
3. refresh and require a new explicit selection;
4. invoke an already certified domain controller;
5. show existing preview/impact confirmation when required;
6. use the existing atomic-write/rollback path;
7. refresh the dossier after successful completion;
8. leave the dossier itself without persistence authority.

No mutation is implemented directly in the GTK view or dossier model.

## 22. Full Scratchpad evaluation

After W99, Scratchpad Full (historically W93) and Document Overview Full are
evaluated separately.

Possible future integration is read/contextual only at first:

- Scratchpad items linked explicitly to the current document or section;
- counts by kind/status;
- navigation/open action;
- no inferred concepts, themes or graph;
- no automatic activation of W93.

Scratchpad Full requires its own explicit authorization regardless of the Full
dossier decision.

## 23. Full exclusions that remain permanent

Even Full excludes:

- new database or hidden index;
- knowledge graph;
- semantic/vector search;
- AI summaries or inferred structure;
- automatic concepts/themes;
- permanent watcher/polling service;
- second full editor;
- project/collection manager;
- dossier-owned CRUD or transactions.

---

# PART III — ROADMAP AND SOURCE-AUDIT POLICY

## 24. Binding roadmap

```text
W96 — Document Overview Core
W97 — Bibliography Manager
W98 — Research Panel Integral Closure
W99 — retrospective GTK-free and lifecycle audit

post-W99 backlog evaluation:
- Scratchpad Full (historical W93, still FROZEN)
- Document Overview Full (unassigned W100+ until authorized)
```

Neither Full item resumes automatically.

## 25. Mature-source upload decision

The historical product audit does not require a new feature comparator. The
architecture-rebuild gate nevertheless requires fresh direct reading of the
raw Xed, Gedit and GNOME Text Editor source archives before a final desktop
candidate may be issued. Derived reports or web sources are not substitutes.

Before any future Document Overview Full authorization, the existing corpus is
re-audited first. A new upload is requested only if a concrete architectural
gap remains; no speculative software intake is required now.
