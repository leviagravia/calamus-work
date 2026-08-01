# Calamus W96 — Document Overview Core contract

This contract supersedes the earlier single-phase W96 dossier proposal.

## Frozen product scope

- visible command: `Navigate → Document Overview`;
- non-modal, single-instance auxiliary window;
- five categories: Overview, Structure, Research, Integrity, Statistics;
- immutable GTK-free `DocumentDossierSnapshot`;
- live buffer for structure/citations/links/statistics;
- existing snapshots for Source Notes, References and Reference Sets;
- explicit Related References and pertinent Reference Sets included in Core;
- collected-but-unused relevant references included in Core;
- read/navigation actions only;
- explicit refresh, no watcher;
- no persistent dossier authority;
- no Scratchpad integration;
- no database, graph, AI/NLP or semantic indexing.

## Core bibliographic closure

```text
cited references
+ Source Note references
+ one bounded explicit symmetric Related References expansion
+ all resolved members of Reference Sets intersecting that closure
```

References outside this closure are not shown.

## Publication

W96 is one work item with Gate A, Gate B and Gate C. It is committed and
published only after the complete real-App and desktop validation passes.
