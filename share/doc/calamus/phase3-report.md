# Calamus phase 3 report

Scope: safer undo/redo and first-pass large-file handling.

Changes:
- Added `/usr/lib/calamus/calamus_history.py` with a bounded `TextHistory` manager.
- Replaced the unbounded 100 full-text snapshot stack in the main window with bounded history.
- Undo history is automatically limited for large documents to avoid multiplying memory usage.
- Added `/usr/lib/calamus/calamus_document.py` helpers for file size and large-file detection.
- Opening files >= 1 MB now warns the user that undo history is limited.
- Status bar shows `undo limited` when large-file history limiting is active.
- Updated package/app version to `1.7.0~rc2+phase3`.

Validation:
- Python syntax compilation passed for `/usr/bin/calamus` and `/usr/lib/calamus/*.py`.
- Micro-tests passed for the new history manager.

Notes:
- This is intentionally conservative. Calamus still uses GTK TextView and keeps document text in memory.
- True very-large-file support would require a different buffer model and belongs to a later phase.
