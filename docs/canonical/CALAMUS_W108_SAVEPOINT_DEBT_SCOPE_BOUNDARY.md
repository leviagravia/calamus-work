# W108 savepoint/Undo debt scope boundary

Direct Emacs and Vim source re-audit shows a mature editor can restore clean/dirty state when Undo returns across the saved boundary. Calamus W102/W103 currently marks restored Undo state modified unconditionally.

This is acknowledged architectural debt but is not part of Thin GTK Shell.

W108 validation must therefore sequence behaviors without hiding the debt:
- Character Map insertion + Undo still proves exact text restoration;
- public `file.save` explicitly establishes clean state before clean DnD;
- dirty DnD + Cancel is tested independently;
- no private clean-state mutation or unsaved-gate bypass;
- no W102/W103 savepoint implementation in W108.
