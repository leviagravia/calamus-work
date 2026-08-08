# W108 — True-App oracle hygiene rules — FROZEN

These rules apply to the current W108 true-App/GTK test and to any historical E2E test that W108 must amend because a W108-authorized facade is physically removed.

## Forbidden in current W108 true-App/GTK

- opening/reading `docs/canonical` or architecture ledger files;
- JSON/YAML/TOML parsing of architecture metadata;
- AST/source/LOC inspection;
- assertions on exact private ownership topology (`_components`, `_w107_subsystems`, `_research_components`) merely to certify structure;
- `composition_complete` as a GTK proof;
- exact binding cardinality (`117`) as a GTK proof;
- counting the 24 aliases or interpreting ledger field names;
- `hasattr()` loops over forwarding methods removed by W108;
- direct private-host invocation when the same product behavior can be triggered through a stable command or natural application event;
- adding a new private dependency to a historical E2E solely to replace a removed public facade.

## Required current W108 true-App pattern

For each of the nine W104 binding families, select at least one stable command that can produce a bounded observable effect on a live application. Invoke through the same `CommandLayer`/stable-ID path used by UI action dispatch and verify the effect.

Additional required GTK receipts:
- Character Map: real modal/presentation path, insert selected character, Undo restores exact buffer;
- synthetic DnD: real drop handler/open path, dropped file becomes visible document, drag completion receipt succeeds;
- panels/menu/presentation behavior where W108 moved wiring;
- normal dirty Quit -> Discard;
- no residual process;
- real config unchanged.

## Historical facade amendment rule

If W108 removes a facade used by a published historical E2E:
1. preserve the original behavioral invariant;
2. prefer the stable command/user event that the UI actually uses;
3. if the operation is not a command, call the narrow published owner only when the historical work item itself is explicitly testing that owner;
4. do not introduce `_components` or another private bundle merely to get access;
5. record the exact supersession in the matrix before packaging.
