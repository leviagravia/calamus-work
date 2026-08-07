# W106 Direct Calamus Source Audit

## Baseline and frozen ownership

W105 published baseline: `aa73cc830b2c2120e26fd7ffb5d21b56c95e709b`.
Certified source tree: **617 files**.

The W100 responsibility inventory assigned **53 App methods**
and **14 App attributes** to W106.

All **53 methods are still present** in the W105 App.
W105 already removed four obsolete W106-era widget-sync attributes:
`_favourite_dynamic_items`, `_syncing_line_number_item`,
`_syncing_opacity_item`, `_syncing_word_wrap_item`.

Ten W106-era mutable App attributes still survive:
`_opacity_widget_api`, `_wrap_reflow_source`, `always_on_top`, `font_family`,
`font_size`, `line_numbers_enabled`, `opacity_percent`, `settings`,
`trim_trailing_on_save`, `word_wrap`.

Not all ten belong in the same W106 domain: `_opacity_widget_api` and
`_wrap_reflow_source` are GTK/runtime adapter concerns and must not be absorbed
into the persisted preference model.

## 1. Raw settings dict and typed fields are dual authority

`App.__init__()` loads `self.settings` as a raw dictionary, then copies pieces
into independent mutable fields:
- `font_family`, `font_size`;
- `word_wrap`;
- `always_on_top`;
- `spell_lang`;
- `appearance_mode`;
- `opacity_percent`;
- `workspace_root`, `workspace_visible`;
- `line_numbers_enabled`;
- `trim_trailing_on_save`.

The raw dictionary remains present and is replaced after each successful
`save_settings()`.

This is a classic mirror-state problem: persistence data and live typed state
are both stored as mutable App authority.

W106 should make one typed snapshot/controller authoritative and expose
read-only projections where compatibility requires them.

## 2. Preferences and application state are mixed in one write

`App.save_settings()` serializes one dictionary containing **17
known keys**.

User preference keys include:
`opacity, font_size, font_family, word_wrap, spell_lang, inline_spell, always_on_top, appearance_mode, white_background, dark_mode, line_numbers, trim_trailing_on_save`.

Persisted application state keys include:
`width, height, last_file, workspace_root, workspace_visible`.

Every preference write therefore also captures unrelated window geometry,
document identity and workspace state. Conversely, opening/saving a document
rewrites all preferences.

There are currently **13 direct `self.save_settings()`
call sites** in App.

Representative coupling:
- changing Word Wrap writes current width/height/last_file/workspace;
- changing Font writes current width/height/last_file/workspace;
- successful Open/Save rewrites every preference;
- Workspace rename/trash reconciliation rewrites every preference;
- application close writes everything again.

This is the primary W106 seam.

## 3. W105 UiStateSnapshot is not persisted ApplicationState

W105 correctly owns runtime logical UI projection:
panel visibility, check state, command availability, etc.

W106 must not rename or reuse that type for persistence.

Required distinction:
- `UiStateSnapshot`: ephemeral W105 command/menu projection;
- `PreferencesSnapshot`: durable user choices;
- `ApplicationStateSnapshot`: durable launch/restore state.

`workspace_visible` is persisted application state even though it also
contributes to the W105 runtime UI snapshot.

## 4. Normalization is inconsistent

Calamus already has strong typed normalizers for:
- Font;
- Appearance;
- Opacity;
- Word Wrap;
- Line Numbers.

But startup still uses Python truthiness directly for:
- `always_on_top`;
- `workspace_visible`;
- `trim_trailing_on_save`.

Thus malformed JSON such as `"false"` becomes `True` for those fields.
`spell_lang` accepts any string without one central normalization policy.

W106 should decode every persisted field through one deterministic codec and
must never use generic Python truthiness for persisted booleans.

## 5. `StateManager` is a compatibility grab-bag

`calamus_state.StateManager` currently exposes **16
public methods/properties** spanning:
- settings;
- recent files;
- favourites;
- recent workspaces;
- Clip Collection compatibility;
- template-directory compatibility.

App directly calls **16 StateManager methods** across
**11 distinct operations**.

This is too broad for a final persistence authority.

Important boundaries:
- Clip Collection already has its own Markdown-backed domain store: it must not
  be reabsorbed into W106 application state.
- Templates are user-owned text assets with their own atomic store logic in
  `calamus_templates.py`; W106 should provide config-root/location authority,
  not absorb template contents into settings.
- recent files/favourites/recent workspaces are persistent application-state
  collections and should receive explicit typed store interfaces.

## 6. Persistence implementation is only partially robust

`calamus_config.save_json_file()` does use same-directory temporary output plus
`os.replace()`, which is a good atomic-replacement baseline.

However it uses a fixed `path + ".tmp"` name and does not fsync the file or
directory. `calamus_templates.write_template_atomic()` already demonstrates a
stronger same-filesystem pattern using `mkstemp`, file fsync, `os.replace`, and
best-effort directory fsync.

W106 should ADAPT that proven Calamus pattern for small technical-state JSON
files rather than inventing a new persistence mechanism.

## 7. Recent-file canonical state has an internal inconsistency

`load_recent_file_store()` deliberately preserves temporarily missing paths,
while the menu-facing `load_recent_files()` filters them.

But `StateManager.add_recent_file()` builds the updated canonical list from
`load_recent_files()`, so adding one new recent file can silently drop other
temporarily unavailable paths from the persisted list.

Favourites correctly separate canonical store from filtered presentation.

W106 should define one invariant:
canonical state keeps deduped stored identities; availability filtering belongs
to presentation/projection.

This is a state-integrity correction, not a new feature.

## 8. Application composition still receives raw persistence pieces

`compose_core_application_components()` reads:
- `app.settings.get("last_file")`;
- `app.state`;
- `app.workspace_root`;
- `app.workspace_visible`;
- `app.save_settings`.

Workspace runtime receives the broad StateManager and a generic
`save_settings(dict)` callback.

W106 should replace those with narrow typed inputs:
- startup document path;
- workspace state port;
- recent-workspace store;
- explicit workspace-root/visibility setters.

No subsystem should need raw settings dicts or whole StateManager.

## 9. Preference gateways still depend on whole host state

`calamus_appearance_gateway.py`, `calamus_opacity_gateway.py` and
`calamus_line_numbers_gateway.py` no longer touch menu widgets after W105, but
they still read/write arbitrary host attributes and call `host.save_settings()`.

W106 should retire this `host: Any` preference authority.
The logical preference controller owns state/persistence; GTK rendering remains
a narrow adapter/projection.

## Direct decision

### ADOPT
- existing typed preference value objects and transition planners;
- W105 UiStateSnapshot as a separate runtime projection;
- existing config-directory injection;
- atomic same-directory replace;
- separate canonical vs filtered recent/favourite presentation semantics.

### EXTRACT
- one typed `PreferencesSnapshot`;
- one typed `ApplicationStateSnapshot`;
- one settings codec/repository;
- one preference controller;
- one application-state controller/port;
- explicit recent/favourite/recent-workspace stores;
- startup composition from typed snapshots rather than raw dictionaries.

### ADAPT
- `calamus_config` low-level JSON helpers into durable atomic repository I/O;
- `StateManager` into narrow repositories/compatibility delegates;
- existing preference modules into the aggregate preference snapshot;
- W105 UI facts to consume typed preference/state authorities.

### DEFER
- subsystem host-port migration → W107;
- final thin GTK shell → W108;
- product features such as recovery/autosave/local history;
- user-custom settings UI redesign.

### REJECT
- one giant mutable `settings` dict as live application authority;
- persisting window/session state on every unrelated preference change;
- a new service locator/global state singleton;
- merging W105 `UiStateSnapshot` with persisted ApplicationState;
- moving Clip Collection content or template text into settings.json.
