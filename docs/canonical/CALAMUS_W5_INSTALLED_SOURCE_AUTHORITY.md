# Calamus W5 — Installed Source Authority

Status: accepted

Date: 2026-06-26T15:30:57+02:00

## Decision

The authoritative development source for `calamus-work` is reconstructed from the currently installed Calamus package:

```text
Package: calamus
Version: 1.7.0~rc3+stable4.3
Architecture: all
Status: install ok installed
```

The older local candidate:

```text
/home/luciano/Projects/calamus/calamus-1.7.0-rc3
```

is rejected as direct source authority because it lacks installed stable4.3 modules and tests.

## Required installed feature set

The reconstructed source must preserve all installed package features, including these modules:

```text
calamus_audit.py
calamus_clip_panel.py
calamus_clips.py
calamus_commands.py
calamus_config.py
calamus_dialogs.py
calamus_document.py
calamus_editor.py
calamus_external.py
calamus_history.py
calamus_layout.py
calamus_logging.py
calamus_model.py
calamus_search.py
calamus_shortcuts.py
calamus_spellcheck.py
calamus_state.py
calamus_ui.py
calamus_version.py
calamus_writing.py
```

and these tests:

```text
test_audit.py
test_config.py
test_document.py
test_history.py
test_layout_hardening.py
test_model_commands.py
test_release_regression.py
test_search.py
test_stable4_regressions.py
test_state.py
test_ui.py
test_writing.py
```

## Test provenance rule

Never test the working copy by running:

```text
calamus
calamus-selftest
```

Working-copy tests must run through:

```text
scripts/prove-source-provenance.sh
scripts/selftest-from-source.sh
scripts/run-from-source.sh
```

The provenance check must show modules loaded from:

```text
/home/luciano/Projects/calamus-work/calamus/
```

and never from:

```text
/usr/lib/calamus/
```

## Architectural direction

AirPad is the primary model of order for future Calamus modularization.

No high-risk modularization may begin before the source authority and provenance gates are closed.
