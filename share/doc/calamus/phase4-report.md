# Calamus 1.7.0 rc2 phase 4 report

Scope: add a minimal regression-test layer and local verification entry point without changing the GUI behaviour.

## Added

- `/usr/bin/calamus-selftest`: command-line runner for non-GUI regression tests.
- `/usr/share/calamus/tests/test_config.py`: settings JSON, defaults, clamping, recent-file handling.
- `/usr/share/calamus/tests/test_document.py`: UTF-8 read/write and large-file detection.
- `/usr/share/calamus/tests/test_search.py`: text statistics, case-sensitive/case-insensitive search, whole-word search, literal replace-all.
- `/usr/share/calamus/tests/test_history.py`: bounded undo/redo semantics, duplicate commit handling, large-document limiting, total-history trimming.

## Packaging cleanup

- Removed generated `__pycache__` content from `/usr/bin`.
- Updated package/runtime version to `1.7.0~rc2+phase4` / `1.7.0-rc2+phase4`.

## Validation

Run after installation:

```bash
calamus-selftest
```

The tests intentionally avoid launching GTK windows, so they can run in a terminal or CI job without a display server.
