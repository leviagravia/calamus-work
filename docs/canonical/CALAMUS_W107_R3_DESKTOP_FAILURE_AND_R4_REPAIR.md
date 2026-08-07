# W107 Candidate R3 Desktop Failure and Candidate R4 Repair

## Status

- Published baseline: `e8befafaf7f75d958eabbd2e273f83c630042b84`.
- R1/R2: retired before the mandatory ownership re-audit.
- R3 POST-AUDIT: valid desktop FAIL 1/2 in the resumed post-audit retry pair.
- R4 POST-AUDIT TEST-AUTHORITY REPAIR: final permitted retry before STOP 2/2.
- Canonical repository: not mutated.

## R3 observed failure

The T480 completed the full automated barrier through:

- W107 focused/historical headless gates;
- headless-core `1551/1551` PASS;
- filesystem `3/3` PASS;
- Pandoc real `14/14` PASS;
- GIO real `21/21` PASS;
- full discovery `1774` PASS with 58 ambient skips;
- W107 exact current identity true-App PASS.

The W107 subsystem host-port true-App lane then passed all Workspace ownership
identity assertions and executed Search replace-all successfully. It failed at
this test-only assertion:

```python
self.assertTrue(window.document_session.dirty)
```

with:

```text
AttributeError: 'DocumentSession' object has no attribute 'dirty'
```

## Direct Calamus authority reconstruction

W102 is frozen and authoritative:

- `DocumentSession.modified` is the only writable dirty state;
- `DocumentSession.requires_save_confirmation()` reports whether the session
  requires save/close confirmation;
- `App.modified` is only a read-only compatibility projection;
- there is no `DocumentSession.dirty` compatibility alias.

The R3 product path had already performed the intended mutation: replace-all
returned `2` and the buffer text was changed before the assertion failed.
Therefore the observed exception does not establish a W107 runtime failure.
It establishes a W107 true-App oracle/API-name defect.

## Mature-source comparison

The user-supplied mature sources reinforce the same rule:

- GNOME Text Editor exposes modified state from the concrete document/page
  relationship (`PROP_IS_MODIFIED`) rather than inventing a second generic
  dirty-state owner;
- NotepadNext derives save UI state from the concrete editor save-point state
  (`isSavedToDisk()` / local `isDirty`) instead of adding a broad application
  state alias;
- the W107 mature-source audit already freezes the convergent rule: target the
  smallest authoritative owner and do not introduce broad compatibility state.

Accordingly, adding a new `dirty` property to Calamus would be the wrong repair:
it would weaken the W102 authority merely to satisfy a faulty W107 test.

## R4 repair

Product/runtime code is unchanged from R3.

The true-App test now asserts the frozen W102 authority directly:

```python
self.assertTrue(window.document_session.modified)
self.assertTrue(window.document_session.requires_save_confirmation())
```

The existing W107 headless contract test also rejects
`document_session.dirty` and requires both authoritative assertions. This makes
the API-name error detectable without a GTK display.

## Acceptance barrier

R4 must rerun the complete T480 sequence from the beginning. No prior R3 PASS
marker is reusable. If R4 produces one valid desktop FAIL, that is FAIL 2/2:
STOP, no automatic R5, and return to direct Calamus plus user-supplied mature
source audit before any further implementation.
