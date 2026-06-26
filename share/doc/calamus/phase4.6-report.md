# Calamus Phase 4.6 Report

Goal: add writing-focused features while keeping Calamus lightweight and modular.

Added modules:
- `/usr/lib/calamus/calamus_writing.py`
- `/usr/lib/calamus/calamus_clips.py`
- `/usr/lib/calamus/calamus_external.py`

Added/extended features:
- Edit > Paste Clean from PDF (`Ctrl+Alt+V`)
- Edit > Clean Selected Text from PDF (`Ctrl+Alt+Shift+V`)
- Edit > Sort Alphabetically A-Z (`Ctrl+Alt+Up`)
- Edit > Sort Alphabetically Z-A (`Ctrl+Alt+Down`)
- Edit > Smart Typography (`Ctrl+Alt+Quote`)
- Edit > Reflow Paragraph (`Ctrl+Alt+J`)
- Edit > Join Lines (`Ctrl+J`)
- Edit > Remove Extra Spaces
- Edit > Remove Trailing Spaces
- Edit > Title Case (`Ctrl+Alt+T`)
- Edit > Sentence case (`Ctrl+Alt+Shift+T`)
- Edit > Toggle/Next/Previous Bookmark (`Ctrl+F2`, `F2`, `Shift+F2`)
- File > New from Template
- View > Clip Collection (`Alt+F10`)
- View > Focus Mode (`F9`)
- View > Distraction-Free Mode (`F11`)
- View > Highlight Current Line (`Ctrl+Alt+I`)
- Tools > Document Statistics (`Ctrl+Alt+W`)

Design notes:
- No heavy dependencies added.
- No background indexing or grammar engine added.
- Clip Collection persists to `~/.config/calamus/clips.json`.
- Templates live in `~/.config/calamus/templates/`.
- Writing operations are routed through the existing command/undo pathway.

Validation:
- Python syntax validation: OK.
- Non-GUI regression tests: 20/20 OK.
