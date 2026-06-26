# Calamus 1.7.0 rc2 phase 5.1 report

Phase 5.1 starts the architecture cleanup without changing the user-facing feature set.

## Added core modules

- `/usr/lib/calamus/calamus_model.py`: GTK-free `Document` model for text, current path, modified state, load/save, clear, and large-file checks.
- `/usr/lib/calamus/calamus_commands.py`: GTK-free command helpers for range replacement, insertion, text transforms, command metadata, and shortcut conflict checks.

## Main script changes

- `/usr/bin/calamus` now owns a `Document` instance and synchronizes it with the GTK text buffer.
- Open, save, save-as, new, undo/redo restoration, and edit finalization update the document model instead of relying only on scattered window attributes.
- Several text editing flows now use the command helper layer for selection-range calculation.
- Version aligned to `1.7.0-rc2+phase5.1` in the app and `1.7.0~rc2+phase5.1` in Debian metadata.

## Tests

- Added non-GUI tests for `Document` load/save/modified behavior.
- Added non-GUI tests for command range operations and shortcut conflict detection.
- Existing non-GUI tests are retained.

## Intentional non-changes

- No menu, shortcut, or UX changes.
- No new features.
- GTK UI still lives primarily in `App`; full UI separation is reserved for phase 5.2.
