# Calamus W96 — direct published-source audit

Published baseline: `792ca0f76db39525a9052bd61e43fe929988af2e`.

W96 reuses these existing source authorities and gateways:

- `calamus_document_structure.py`: heading model/parser;
- `calamus_navigation_gateway.py`: semantic navigation;
- `calamus_citations.py`: exact Pandoc citation parsing;
- `calamus_source_note_store.py` / `calamus_source_notes.py`: document sidecar;
- `calamus_reference_store.py` / `calamus_references.py`: global library;
- `calamus_related_references.py`: explicit symmetric relationships;
- `calamus_reference_set_store.py` / `calamus_reference_sets.py`: transparent
  sets;
- `calamus_reference_integrity.py`: Research Check;
- `calamus_authoring_bridge.py`: explicit heading links and uses;
- `calamus_writing.py`: document statistics;
- `calamus_research_file.py`: immutable FileToken identity;
- existing App research runtimes and navigation gateways.

New justified Core modules:

- `calamus_document_dossier.py`: immutable GTK-free model/builder;
- `calamus_document_dossier_controller.py`: refresh/currentness owner;
- later Gate B view/runtime modules.

No new parser authority, persistent store or mutation engine is justified.
