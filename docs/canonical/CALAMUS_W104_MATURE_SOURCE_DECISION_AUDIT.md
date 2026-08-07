# Calamus W104 — Mature Source Decision Audit

Direct source comparison, no web substitution.

- gedit / Pluma: ADAPT stable action identity and central metadata reused across UI surfaces; REJECT deprecated GtkAction/GtkUIManager APIs.
- GNOME Text Editor: STRONGLY ADAPT namespaced IDs, parameterized actions, named action keyboard bindings and separate availability; adapt rather than import GTK4-specific implementation.
- Kate: ADAPT one reusable stable action identity with central default shortcut and separate enabled state; reject plugin/multi-view scope.
- NotepadNext: ADAPT reusable QAction identity; reject reflection-like string lookup and broad state-update sprawl.
- Micro: ADAPT explicit command map separated from key bindings; reject plugin/user-custom binding framework in W104.
- Geany: ADAPT stable keybinding/action IDs and central dispatch identity; reject plugin complexity.
- Airpad: current callback/accelerator separation is a negative precedent similar to pre-W104 Calamus.

Convergent rule: stable named command identity, one identity reused across invocation surfaces, explicit parameters for variants, availability separate from implementation, and input bindings targeting commands rather than arbitrary window callbacks.
