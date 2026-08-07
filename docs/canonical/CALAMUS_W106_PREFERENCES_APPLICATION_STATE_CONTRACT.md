# W106 Preferences and Application State Extraction — Frozen Contract

## Identity

Work item: W106
Name: Preferences and Application State Extraction
Baseline: `aa73cc830b2c2120e26fd7ffb5d21b56c95e709b`
Nature: architecture + persistence-integrity hardening
Visible feature additions: none
Settings UI redesign: none
W107 host-port migration: not included

## 1. Three distinct state domains

### A. `PreferencesSnapshot` — durable user choices

Aggregate existing typed preference concepts:
- Font preference;
- Word Wrap;
- Appearance;
- Opacity;
- Always on Top;
- Spell language;
- Line Numbers;
- Trim Trailing Spaces on Save.

`inline_spell` remains the published disabled compatibility value unless a
future work item explicitly reintroduces it.

### B. `ApplicationStateSnapshot` — durable launch/restore state

Own:
- window width;
- window height;
- last active document path;
- workspace root;
- workspace visible.

It does not contain document text, Undo history or W105 command/menu state.

### C. `UiStateSnapshot` — W105 runtime only

Unchanged. It remains an ephemeral projection for menus/availability.

## 2. One settings repository, two typed APIs

Because Preferences and ApplicationState currently share one historical
`settings.json`, W106 must not introduce two independent writers to that file.

Define one GTK-free repository/codec, for example:
- `CalamusSettingsSnapshot(preferences, application_state)`;
- `SettingsCodec.decode(raw_mapping)`;
- `SettingsCodec.encode(snapshot)`;
- `SettingsRepository.load()`;
- `SettingsRepository.update_preferences(...)`;
- `SettingsRepository.update_application_state(...)`.

The APIs are separate; physical persistence remains one owner.

## 3. On-disk compatibility

W106 preserves the current user configuration location and JSON filenames.

`settings.json` must remain backward-readable with the existing published keys.
No proprietary binary format and no database.

Legacy appearance keys remain accepted and may continue to be written for
published compatibility.

No schema-version key is required in W106.

## 4. Strict decoding

Every persisted boolean uses strict normalization; arbitrary truthy strings are
never accepted as booleans.

Required normalized fields include:
- always_on_top;
- workspace_visible;
- trim_trailing_on_save.

Spell language must normalize to a non-empty safe string; availability of an
installed Hunspell dictionary remains a runtime capability question, not a
persistence decoding requirement.

Window geometry is clamped with the current published bounds.

Invalid workspace roots and missing last-file paths must preserve existing
startup safety semantics.

## 5. Atomic persistence

Technical JSON state writes use:
- unique same-directory temporary file;
- UTF-8 deterministic JSON;
- flush + file fsync;
- `os.replace`;
- best-effort parent-directory fsync;
- guaranteed temporary cleanup.

Failed persistence never advances the in-memory authoritative snapshot.

## 6. Preference transactions

One `PreferencesController` owns logical preference transitions.

For each preference:
1. validate/plan from current typed state;
2. persist the requested snapshot;
3. project through a narrow adapter;
4. on projection failure, restore previous persisted snapshot and projection;
5. publish one logical change result for title/W105 UI refresh where needed.

The controller imports no GTK.

Existing individual preference planners remain reusable.

## 7. Application-state updates are explicit

Replace broad `save_settings()` calls with narrow intent:
- `record_window_geometry(width, height)`;
- `record_last_file(path_or_none)`;
- `record_workspace_root(path_or_none)`;
- `record_workspace_visible(bool)`.

Open/Save may persist last-file identity without rewriting preferences.
Workspace operations may update workspace state without rewriting font,
appearance or geometry.
Window geometry is captured at the application-state boundary, especially on
normal close, rather than as an accidental consequence of any preference write.

## 8. Recent/favourite/workspace collections

Create/retain explicit narrow stores:
- `RecentFileStore`;
- `FavouriteStore`;
- `RecentWorkspaceStore`.

Canonical stored paths remain deduplicated independently of current filesystem
availability. Menu projection filters unavailable entries.

Adding a recent file must not delete other temporarily unavailable canonical
recent paths.

## 9. Templates and clips

`calamus_templates.py` remains the owner of template text/assets.
W106 may provide the canonical config root/path but does not move template
contents into application settings.

Clip Collection content remains in its existing Markdown-backed subsystem.
Remove/deprecate StateManager compatibility methods that pretend Clip content is
generic application state.

## 10. Composition boundary

Add typed preferences/application-state components before editor/workspace
composition.

Downstream composition receives explicit values/ports:
- startup last-file path;
- initial Word Wrap;
- workspace root/visibility;
- recent-workspace store;
- preference/app-state update ports.

No subsystem receives:
- raw settings dict;
- whole StateManager;
- generic `save_settings(dict)`.

W107 remains responsible for broader subsystem host-port cleanup.

## 11. App compatibility surface

`App.settings` ceases to be mutable authority.

If temporary compatibility is required, expose read-only projections for
published tests/callers. Do not create writable mirrors.

Preference fields such as font size, opacity and Word Wrap should ultimately
project from the controller snapshot rather than being independently mutable.

## 12. W105 integration

W105 `ui_state_facts()` reads logical values from W106 authorities plus runtime
panel state.

Preference/application-state changes trigger one W105 refresh result.
W105 widgets never persist anything directly.

## 13. Failure semantics

- malformed JSON falls back safely to typed defaults;
- persistence failure leaves logical state unchanged;
- projection failure attempts exact rollback;
- rollback failure is surfaced, never silently hidden;
- unrelated state categories are not rewritten by a narrow update API.

## 14. Out of scope

- W107 Subsystem Host-Port Migration;
- W108 Thin GTK Shell;
- autosave/recovery/local history;
- new Preferences dialog;
- user-custom keybinding system;
- cloud/database/settings synchronization;
- document-format changes.

## 15. Completion criteria

W106 is complete only when:
1. no mutable raw `App.settings` authority remains;
2. no generic App `save_settings(dict)` authority remains;
3. preferences and persisted application state are distinct typed snapshots;
4. there is exactly one writer for settings.json;
5. malformed booleans cannot become true by Python truthiness;
6. preference writes do not incidentally persist document/workspace/geometry;
7. Open/Save can update last-file state without rewriting preferences;
8. workspace state uses explicit state ports;
9. canonical recent paths survive temporary unavailability;
10. Clip Collection/template content is not absorbed into settings;
11. core persistence/controller modules import no GTK;
12. W105/W104/W103/W102/W101/W99/W98 gates pass;
13. full suite and desktop validation pass;
14. real user config remains unchanged by isolated validation.
