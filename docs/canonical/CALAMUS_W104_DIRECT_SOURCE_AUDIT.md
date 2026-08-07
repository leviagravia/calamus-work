# Calamus W104 — Direct Source Audit

Audit baseline: published W103 commit `ca1a9774085d81d087f7a257dbffbbaa858a3889`, exact 588-file source tree.

The W103 baseline had six parallel command/action authorities: `calamus_command_registry`, `LOW_RISK_COMMANDS`, legacy `COMMANDS`, `RESEARCH_COMMANDS`, `calamus_shortcuts.SHORTCUTS`, and GTK menu/shortcut wiring in `calamus_ui`. W100 marked 188 App methods for W104 command-surface review, but their actual migration owners remain distributed: W102=13, W103=27, W106=44, W107=89, W108=15. W104 therefore normalizes invocation identity and binding rather than absorbing those methods.

`CommandContext` still carried whole `App`; `CommandSpec.enabled` was a static boolean rather than runtime availability; the 94 shortcut-guide rows differed from the 77 real GTK bindings, notably missing Move Line Alt+Up/Alt+Down and drifting on plus/minus/slash/PageUp/PageDown spelling. Dynamic menus hid parameters inside closures.

Decision: converge identity, metadata, shortcuts and invocation on one stable-ID catalog; preserve distributed domain execution and defer GTK UI-state projection to W105.
