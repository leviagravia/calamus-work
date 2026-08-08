# W108 Modal Transition Closure — frozen pre-packaging gate

This gate is retained from the Emacs/Vim/Org post-audit R1 re-audit.

For every modal-capable step in current W108 automatic true-App, freeze precondition, expected modal, deterministic driver and terminal behavioral receipt.

Required current sequence:
- About -> Close driver;
- Character Map -> Ω click + Close driver -> Undo exact byte restoration;
- System Info -> Close driver;
- public file.save -> clean DnD -> no modal -> successful drag/open;
- public edit -> dirty DnD -> Save changes? -> Cancel driver -> failed drag + unchanged identity/content;
- public file.save -> public file.quit -> no modal expected.

Forbidden:
- operator intervention in automated lane;
- direct DocumentSession clean/dirty mutation;
- monkeypatch/bypass of `may_continue` or unsaved gate;
- treating Cancel as successful drag;
- opportunistic W102/W103 savepoint redesign.

PASS is mandatory before Candidate sealing.
