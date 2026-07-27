# Calamus W90 — External Pandoc/citeproc Handoff

**Status:** REFROZEN AFTER R5 DESKTOP DATA-FIDELITY FAIL / UNITARY RECONSTRUCTION CANDIDATE R6
**Published baseline:** `673c17aa3239bf189f11c93af36e4ea137df2f6d`
**Work item:** W90 only

## 1. Purpose

W90 adds a narrow, optional handoff to an external user-installed Pandoc. It
formats a bibliography or converts the current Markdown document with citeproc,
without turning Pandoc, CSL, BibLaTeX or generated files into Calamus
authorities. The feature improves academic export while preserving Calamus as a
small, local, plain-text-first editor.

## 2. User-visible command

Exactly one new command is added:

`Research → Export with Pandoc/citeproc…`

There are no per-format commands and no shortcut. The existing transparent
BibTeX/BibLaTeX and Research Apparatus exports remain separate products.

## 3. Products and formats

### Formatted Bibliography

- Plain text `.txt`
- HTML `.html`
- OpenDocument Text `.odt`
- Microsoft Word `.docx`
- Rich Text Format `.rtf`
- LaTeX source `.tex`

### Current Document with Citations

- HTML `.html`
- OpenDocument Text `.odt`
- Microsoft Word `.docx`
- EPUB `.epub`
- Rich Text Format `.rtf`
- LaTeX source `.tex`

No PDF is part of W90. PDF requires a second external typesetting toolchain and
a separate support matrix.

## 4. Reference scopes

- References cited in the current document;
- all References;
- one exact, case-sensitive, static Reference Set.

The cited scope preserves first-citation order. All preserves canonical
`references.md` order. A Reference Set preserves stored member order; citeproc
may apply the selected CSL bibliography sorting rules. A document export is
blocked if its chosen scope omits a citation used by the document.

Missing, ambiguous or unresolved keys block the operation. Aliases are resolved
to primary keys only in the temporary derived document. The current document is
never rewritten by W90.

## 5. Authority and ownership

- `references.md` remains the sole bibliographic authority;
- `reference-sets.md` remains the transparent authority for static sets;
- the current document buffer and saved file are read-only inputs;
- its Source Notes sidecar remains untouched;
- an optional local `.csl` file is a read-only external input;
- temporary BibLaTeX, temporary Markdown, metadata and preview files are derived;
- every final output is derived and replaceable by regeneration.

W90 creates no database, index, cache, watcher, export history, profile file or
second bibliography store.

The transient BibLaTeX projection is a typed interoperability boundary, not a
text dump. Calamus models `publisher` and `location` as one scalar each, while
BibLaTeX models those fields as literal lists whose separator token is `and`.
The exporter therefore serializes each Calamus scalar as one protected literal
list atom. For example, `Herder and Herder` must become
`publisher = {{Herder and Herder}}`, so Pandoc/citeproc receives one publisher,
not two publishers. This mapping is covered by a Calamus round-trip test and a
real-Pandoc ODT regression test.

## 6. Preview contract

Before final conversion the controller freezes a complete plan and runs citeproc
to generate a semantic preview in plain text. The preview displays:

- Pandoc executable and version;
- product and Reference scope;
- exact selected key order and count;
- exact Reference Set name when used;
- output format and destination;
- selected local CSL or Pandoc default style;
- BibLaTeX mapping warnings;
- normalized Pandoc stderr warnings;
- semantic citeproc text.

The preview is not WYSIWYG. Confirming it authorizes one conversion of the frozen
plan, subject to a second stale gate.

## 7. External process boundary

- Pandoc is not bundled and is detected on demand with `shutil.which()`;
- the resolved executable must be a runnable regular file;
- `pandoc --version` must parse successfully;
- minimum supported version is Pandoc 2.11.0;
- argv contains only fixed, typed internal fields;
- `shell=False` is mandatory;
- stdin is closed, stdout/stderr are captured and bounded;
- only one Pandoc process may be active;
- preview timeout is 60 seconds and final conversion timeout is 120 seconds;
- cancel, timeout and application shutdown terminate the exact process group;
- Windows uses no-console/new-process-group flags when available;
- the GTK main thread never performs the blocking conversion.

The W90 argv surface is limited to input path, `--from`, `--to`, `--citeproc`,
`--standalone`, optional `--bibliography`, optional local `--csl`, optional
Calamus-owned `--metadata-file`, and `--output`.

## 8. No-network boundary

W90 performs no network operation and exposes no remote resource option. Because
a universal Pandoc `--sandbox` breaks accepted ODT/DOCX/EPUB writers on the
tested supported installation, Calamus rejects document input containing remote
Markdown images or remote HTML media before process launch. Ordinary hyperlinks
are allowed because they are rendered as links rather than fetched. Filters,
templates, includes and network-backed CSL are unavailable.

## 9. Tokens and stale behavior

The frozen plan contains:

- exact References `FileToken`;
- exact Reference Sets `FileToken` when used;
- current document file token and buffer SHA-256;
- optional CSL file token;
- Pandoc resolved path and version;
- exact selected records, keys and derived BibLaTeX text;
- destination pre-state token;
- destination directory device/inode/mode token.

The plan is rebuilt before preview, after preview, before final conversion and
immediately before publication. Any mismatch produces `stale`, writes no final
output and preserves an existing destination.

## 10. Safe publication

Temporary inputs are private mode `0600`, flushed and fsynced. Final conversion
writes to a unique staging file in the destination directory. Publication
requires:

1. zero Pandoc exit status;
2. regular non-symlink staged output;
3. non-empty output;
4. staged-file fsync;
5. exact plan reproduction;
6. unchanged destination-directory identity;
7. `os.replace()` into the destination;
8. best-effort directory fsync.

References, Reference Sets, current document, Source Notes and selected CSL are
protected destinations. Existing destination replacement is allowed only if its
exact preview token is unchanged.

## 11. GTK, modal-session and lifecycle boundary

GTK-free modules:

- `calamus_pandoc.py`
- `calamus_pandoc_process.py`
- `calamus_pandoc_controller.py`

GTK dialog/runtime modules:

- `calamus_pandoc_dialogs.py`
- `calamus_pandoc_runtime.py`

`App` owns only composition, one callback and shutdown wiring. Every modal
workflow is owned by `ModalSession`, which owns the exact dialog, response,
`hide`, registered GLib source IDs, source removal and final `destroy`. A W90
callback must not cycle several `Gtk.ComboBoxText` selections while
`Gtk.Dialog.run()` owns a nested main loop. Semantic model tests cover the full
format surface; a modal proof exercises one exact response in a fresh process.

Closing by X, File → Quit or Ctrl+Q must cancel the exact active Pandoc child,
join the worker, remove owned GLib sources and leave no Pandoc or Calamus
process. A worker or source that cannot terminate blocks normal close.

The regression architecture is part of the contract:

- pure/static/full regression runs headless and must not initialize a display;
- every real-GTK component or true-App workflow runs in a separately named,
  fresh subprocess with isolated HOME/XDG state;
- `G_DEBUG=fatal-criticals` remains mandatory in every GTK lane;
- no monolithic real-display `unittest discover` is accepted;
- actual GTK builders and modal ownership are component-tested in fresh lanes;
- the integrated true-App export proof substitutes only semantic options,
  destination, preview-acknowledgement and result-presentation boundaries while
  retaining the real App callback, controller, canonical stores and real Pandoc;
- `PandocWorkflowOutcome` is the stable terminal proof surface; transient dialog
  visibility and progress rendering are never operation-completion APIs;
- the complete native-dialog chain is reserved for isolated manual desktop
  validation, where the dialogs themselves are the object under test;
- the historical W85 product-dialog proof remains split into pure
  five-product/default coverage, builder coverage, one semantic modal response
  and a separate true-App export lane.

Runtime identity follows the same single-authority rule used by the audited
mature editors:

- `calamus_version.py` is the sole current authority for build label, work item
  and published baseline;
- historical W tests may verify stable product name, dialog ownership and the
  absence of obsolete package identity, but may not assert a superseded work
  item or baseline as current;
- the W90 true-App identity lane projects the current constants rather than
  duplicating literals;
- exactly one current-build true-App identity lane may assert exact W90 metadata;
- historical work-item numbers remain provenance labels for behaviour, never a
  second runtime identity authority.

## 12. Bloat ceiling

- exactly one new visible command;
- at most five new production modules;
- at most six pre-existing production files modified, including one shared pure W87 BibLaTeX boundary module;
- no new Python dependency and no bundled executable;
- no settings authority;
- at most 1,800 nonblank/non-comment logical lines in the five new modules;
- no generic exporter/plugin framework.

## 13. Help and beginner tutorial contract

`Help → User Guide` must contain a complete, beginner-oriented Pandoc export
tutorial. It must explain both products, all three Reference scopes, every
supported output format, both CSL choices, destination rules, semantic preview,
cancel/re-arm, stale recovery, missing-Pandoc recovery and post-export checks.
At least one worked example is required for bibliography TXT, bibliography HTML,
document ODT, document DOCX, document EPUB and document LaTeX.

The tutorial must state that the document currently open in Calamus is the input
for document export. The user may choose any writable destination and any name
compatible with the selected format. Desktop validation must verify the exact
paths actually chosen by the user; a runner must never reinterpret its suggested
folder as a product requirement. A missing final artifact is a validation failure,
but a valid artifact saved elsewhere is not.

## 14. Explicit non-goals

No PDF. No custom Pandoc arguments; template/CSS chooser; Lua or executable filters;
writer-extension editor; persistent export profiles; export history; clipboard
export; batch/book compilation; multiple bibliographies; CSL download/manager;
embedded browser preview; Crowbook integration; SoloMD Git/search/cache/AI;
nb plugins/index/Git; remote media retrieval.

## 15. Acceptance gate

Certification requires:

- compile PASS;
- pure, process, real-filesystem and real-Pandoc focused tests PASS;
- bibliography and document products PASS;
- cited/all/exact-set scopes PASS;
- plain/HTML/ODT/DOCX plus representative RTF/LaTeX/EPUB evidence;
- local CSL PASS;
- alias projection and source immutability PASS;
- malformed/missing/ambiguous/set-omission/remote-media gates PASS;
- stale References/sets/document/CSL/destination/directory PASS;
- timeout/cancel/nonzero/cleanup PASS;
- source provenance, scope/bloat and GTK boundary PASS;
- headless full regression of exactly 1322 tests PASS;
- the real desktop runner performs Pandoc detection before manual validation;
- no W90 real-GTK or true-App lane may be reported PASS when unittest reports a skip;
- every named fresh-process real-GTK lane PASS with fatal criticals enabled;
- historical W89 stable-identity regression PASS without asserting W89 as the current work item;
- the single current-build true-App identity lane renders exact W90 metadata from `calamus_version.py`;
- the split W85 model, builder, one-response modal and true-App lanes PASS;
- true App/GTK preview/export and process lifecycle PASS on the ThinkPad;
- complete manual click-by-click validation PASS;
- exact post-validation verifier PASS;
- only then exact stage, commit, push, fetch and actual remote verification.

No W91 work enters W90.

## R7 typed-handoff, literal-list fidelity and semantic-artifact proof rule

The true-App workflow MUST synchronize only on user-stable modal endpoints:
options, destination, semantic preview and final result. Progress dialogs are
transient projections of background state and MUST NOT be required to remain
visible until a polling test observes them. Their widget ownership is verified
separately by component lanes. The full workflow proves completion through the
stable preview, final typed result, output artifact, unchanged authorities and
normal close. This rule is derived from the uploaded mature sources: Zettlr's
LongRunningTask terminal states, Pandoc Preview's RenderResult and per-spec proof
artifact, MarkText's promise/result boundary, and Apostrophe's callback-based
background preview.

A W90 true-App test that automates a multi-dialog chain by polling transient
windows is blocking and invalid even when it passes on a slower machine. A test
timeout must never close a product dialog before the diagnostic state has been
asserted, because that converts a test-driver timeout into a false product cancel.

## 16. R7 desktop artifact-path and semantic-comparison rule

The manual desktop validator may suggest a folder but must accept any user-chosen
regular output file. After Calamus closes, the runner asks for the actual TXT and
ODT paths, normalizes them, verifies format and content, and only then asks for
manual PASS. The verifier checks semantic titles case-insensitively, exact
Reference Set exclusion, valid ODT structure, rendered citation, and exact
publisher fidelity: `Herder and Herder` must be present and `Herder; Herder`
must be absent. Canonical References, Reference Sets, document, Source Notes and
CSL remain byte-identical.


## 17. R7 rendered-artifact normalization contract

Rendered Pandoc artifacts are not compared as raw contiguous byte strings. Plain
text may contain nonsemantic line wrapping, and structured formats may divide text
across XML nodes. Every semantic artifact gate therefore applies exactly this
projection before comparison:

1. decode with the format's declared encoding or parse its structured container;
2. normalize Unicode to NFC;
3. collapse every whitespace run to one ASCII space;
4. casefold only for checks whose contract is explicitly case-insensitive, such as
   rendered title identity;
5. preserve punctuation, word order and list separators.

Thus `Herder and\nHerder` is equivalent to `Herder and Herder`, while
`Herder; Herder` remains a failure. Validators must not remove punctuation, sort
tokens, apply fuzzy matching or force Pandoc `--wrap=none` merely to make raw
substring assertions pass. The policy is enforced in one test helper, real-Pandoc
plain and ODT tests, true-App tests, the scope gate and the final desktop artifact
verifier.
