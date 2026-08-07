CALAMUS MEMORIA OPERATIVA — W102 AUDIT R1
Date: 2026-08-06

W101 CLOSED/CERTIFIED/PUBLISHED
Commit: 17b409a05f356477173b2bdd348a67a4cf01f43c
Subject: W101: extract core composition boundary

W102 Document Session Extraction
Status: AUDIT COMPLETE / CONTRACT PROPOSED / IMPLEMENTATION NOT STARTED

FINDINGS
- Document is GTK-free but App duplicates path, modified, and loading.
- Gtk.TextBuffer remains live per-keystroke surface.
- New/Open/Save/Save As are manually orchestrated in App.
- set_buffer and save normalization have unsafe loading toggles.
- Workspace rename/trash mutate active identity directly.
- W101 Workspace still receives App document callbacks.
- W99 lifecycle stays separate.
- Pure lifecycle plans remain useful.

MATURE CONVERGENCE
GNOME Text Editor, gedit, Pluma, NotepadNext, Geany, Kate, and Airpad converge
on one identity owner, explicit loading/save state, post-success identity
commit, guarded replacement, UI prompts outside core, and close after save
success.

FROZEN DIRECTION
One GTK-free DocumentSession; Gtk buffer retained until W103; read-only App
projections; typed Workspace ports; no visible/persistence changes; exact
failure-injection tests.

DESKTOP AUTHORITY
Candidate/launcher cryptographic identity plus EXIT=0, ERR=NONE,
FINAL_PHASE=RUNNER_RETURNED_PASS.

NEXT
Explicit contract acceptance, then one Candidate from baseline 17b409a05f356477173b2bdd348a67a4cf01f43c.
No Git mutation occurred in this audit.


W102 CANDIDATE R1 IMPLEMENTATION
- authoritative GTK-free DocumentSession added;
- App path/dirty/loading mirrors replaced by read-only projections;
- New/Open/Save/Save As and template transitions delegated;
- Workspace current-document path reads the session port;
- exact W102 release profiles and true-App gates added.

W102 CANDIDATE R1 — FAIL 1/2
Date: 2026-08-07
Automated T480 gates before failure:
- 1700 full discovery PASS, 48 ambient GTK skips;
- W102 identity true-App PASS;
- W102 document-session true-App PASS;
- W101 composition true-App PASS;
- W99 lifecycle true-App PASS.
Failure:
- historical W98 product smoke attempted `win.modified = False`;
- W102 intentionally exposes `App.modified` as a read-only projection;
- AttributeError occurred before manual desktop validation.
Classification:
- historical true-App fixture migration defect;
- not a DocumentSession product defect;
- Candidate R1 retired, FAIL 1/2.

W102 CANDIDATE R2 — TEST-AUTHORITY REPAIR
- no product/runtime behavior changed from Candidate R1;
- W98 close/cleanup now calls `DocumentSession.mark_clean()`;
- W95 cleanup now calls `DocumentSession.mark_clean()`;
- Workspace true-App fixtures now call `DocumentSession.mark_modified()`;
- new AST gate forbids true-App fixtures from assigning read-only App session projections;
- focused inventory: 30 tests;
- release inventory: 1701 tests, all assigned.
