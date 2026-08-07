# CALAMUS W106 — MO Supplement

Baseline: `aa73cc830b2c2120e26fd7ffb5d21b56c95e709b` (W105 published).
Work item: W106 — Preferences and Application State Extraction.

## Frozen implementation decisions

- `PreferencesSnapshot`, `ApplicationStateSnapshot`, and W105 `UiStateSnapshot` are distinct authorities.
- `SettingsRepository` is the one application writer for `settings.json`; preference and application-state updates are narrow typed operations.
- `PreferencesController` persists before projection and rolls back persisted/logical state if projection fails.
- Persisted booleans use strict normalization; arbitrary truthy strings are rejected.
- technical JSON writes use unique same-directory temporary files, file fsync, atomic replace, best-effort directory fsync, and cleanup.
- `RecentFileStore`, `FavouriteStore`, and `RecentWorkspaceStore` own canonical path collections; current filesystem availability is a projection only.
- adding a recent file never prunes a temporarily unavailable canonical entry.
- running App has no mutable `self.settings`, generic `save_settings`, or broad `StateManager` authority.
- Workspace composition receives narrow recent-workspace and state-recording ports.
- Clip Collection and template content remain separately owned; W106 does not absorb them into settings.
- W107 host-port migration is not part of W106.

## Desktop evidence rule

Candidate/launcher cryptographic identity plus synchronous `EXIT=0`, `ERR=NONE`, `FINAL_PHASE=RUNNER_RETURNED_PASS`, together with explicit human PASS.
Do not use asynchronous log tails as authority.

## Linux Mint caveat

`Ctrl+Alt+L` is intercepted by Linux Mint and must not be used as a Calamus manual validation shortcut. Validate Line Numbers through the menu/gutter or another non-conflicting route.
