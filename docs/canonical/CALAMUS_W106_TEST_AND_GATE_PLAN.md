# W106 Test and Gate Plan

## Pure codec tests

- decode every existing published settings key;
- legacy appearance booleans migrate exactly as before;
- numeric-string Font/Opacity compatibility remains;
- `"false"` does not enable always-on-top/workspace-visible/trim-on-save;
- invalid window sizes clamp to current bounds;
- invalid spell language falls back deterministically;
- malformed/non-object JSON yields typed defaults;
- encode/decode round-trip is deterministic.

## Repository tests

- one writer owns settings.json;
- unique same-directory temp file;
- file fsync before replace;
- temp cleanup on write failure;
- atomic replace;
- failed write leaves previous file and in-memory snapshot intact;
- custom config_dir never touches real ~/.config/calamus.

## Preference transaction tests

For Font, Word Wrap, Appearance, Opacity, Always on Top, Language, Line Numbers,
Trim-on-Save:
- no-op => no write/no projection;
- valid change => exactly one persisted preference transition;
- persistence failure => no live-state change;
- projection failure => previous persisted/logical state restored;
- W105 UI refresh emitted exactly once after successful logical change.

## Application-state tests

- Open/Save updates last_file only through explicit state API;
- preference update does not change width/height/last_file/workspace values;
- workspace root update does not change preferences;
- workspace visibility update does not change preferences;
- close records clamped geometry;
- missing stored last file remains safe at startup.

## Collection-store tests

- recent/favourite/workspace paths are deduped;
- canonical recent/favourite lists preserve temporarily missing paths;
- presentation filters missing paths;
- adding a new recent does not erase another temporarily missing recent;
- rename/trash reconciliation writes exact canonical collections.

## Static gates

- GTK-free W106 domain/repository/controller modules contain no gi/Gtk/Gdk/Pango;
- `bin/calamus` has no mutable raw `self.settings` authority;
- no broad `save_settings(dict)` compatibility gateway after migration;
- composition does not pass raw settings dict to document/workspace subsystems;
- composition does not pass whole StateManager where a narrow store exists;
- W105 UiStateSnapshot remains a separate type/domain;
- no W107 feature migration.

## True-App desktop lane

Automatic isolated fixture:
1. exact W106 System Info identity;
2. Font change persists and projects;
3. Word Wrap change persists and W105 check projection follows;
4. Appearance/Opacity change persists and projects;
5. Always on Top or Line Numbers changes through menu;
6. language selection round-trip where installed dictionary list permits;
7. open/save document updates last-file restore identity;
8. workspace root/visibility round-trip;
9. normal close records geometry;
10. restart same isolated XDG and verify restored preferences/application state;
11. no residual process;
12. real ~/.config/calamus unchanged.

Never use Ctrl+Alt+L as a Linux Mint manual validation step. That accelerator is
known to be intercepted by the desktop environment.
