# Calamus W96 — mature-source audit status

## Historical product evidence retained

The earlier direct-source audits remain relevant to the product contract:

- GNOME Text Editor: derived document statistics/properties and bounded lifecycle;
- Xed/Gedit: semantic activation, selected detail, close/focus actions;
- ghostwriter: outline projection and semantic heading navigation;
- Zim: explicit links/backlinks without notebook authority;
- KeepNote/NoteKit: tree/list/detail separation without a second editor;
- GNOME Citations and Pandoc: bounded bibliographic projection and explicit citation syntax;
- IWE: stale-aware delegated actions;
- org-roam/AppFlowy: contextual relations/progressive disclosure, while rejecting graph/database/web infrastructure.

These conclusions support retaining the W96 product model. They do not replace
a fresh direct-source audit of the rebuilt test/build/composition topology.

## Fresh gate required before a final rebuilt candidate

The current audit environment does not contain the raw mature source trees.
Finalization therefore requires direct reading of exactly these archives:

1. `xed-master.zip` — test registration, workdir, helper ownership and program construction;
2. `gedit-master.zip` — centralized test executable/include/dependency ownership;
3. `gnome-text-editor-main.zip` — Meson composition roots and artifact/test topology.

No web or repository substitute is permitted. Until those archives are read,
the reconstructed source is an audit build only, not a desktop candidate.
