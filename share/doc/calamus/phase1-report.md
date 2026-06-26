# Calamus 1.7.0 rc2 phase 1 report

Phase 1 introduces a conservative modularization without changing the public UI or feature set.

## Extracted modules

- `/usr/lib/calamus/calamus_config.py`: configuration directory, JSON persistence, settings, recent files, favourites, and integer clamping.
- `/usr/lib/calamus/calamus_document.py`: document read/write helpers.
- `/usr/lib/calamus/calamus_search.py`: word regex, text statistics, literal search, whole-word search, and replace-all text transformation.
- `/usr/lib/calamus/calamus_spellcheck.py`: Hunspell dictionary selection, command discovery, misspelled-word lookup, and suggestions.

## Main script changes

- `/usr/bin/calamus` now delegates persistence, document I/O, search/statistics, replace-all, and Hunspell operations to the extracted modules.
- The GTK window class still owns UI state and event wiring, so behaviour remains compatible with phase 0.
- Version aligned to `1.7.0-rc2+phase1` in the application and `1.7.0~rc2+phase1` in the Debian metadata.

## Validation

- Python syntax validation passed for `/usr/bin/calamus` and all extracted modules.
- Lightweight module self-tests passed for search/replace, text statistics, and integer clamping.

## Remaining phase 1 debt

- UI methods are still concentrated in the `App` class.
- Session save/restore still uses raw JSON helpers directly from the main script.
- Printing and dialog construction have not yet been extracted.
- No formal test package is shipped yet; this should be addressed in phase 2/3.
