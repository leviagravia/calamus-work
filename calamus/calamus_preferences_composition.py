"""W106 persistence composition boundary."""
from __future__ import annotations

from dataclasses import dataclass

from calamus_persistent_collections import FavouriteStore, RecentFileStore, RecentWorkspaceStore
from calamus_preferences_controller import ApplicationStateController, PreferencesController
from calamus_settings_repository import SettingsRepository


@dataclass(frozen=True)
class PreferencesApplicationStateComponents:
    config_dir: str
    repository: SettingsRepository
    preferences: PreferencesController
    application_state: ApplicationStateController
    recent_files: RecentFileStore
    favourites: FavouriteStore
    recent_workspaces: RecentWorkspaceStore


def build_preferences_application_state_components(config_dir: str) -> PreferencesApplicationStateComponents:
    repository = SettingsRepository(config_dir)
    return PreferencesApplicationStateComponents(
        config_dir=config_dir,
        repository=repository,
        preferences=PreferencesController(repository),
        application_state=ApplicationStateController(repository),
        recent_files=RecentFileStore(config_dir),
        favourites=FavouriteStore(config_dir),
        recent_workspaces=RecentWorkspaceStore(config_dir),
    )
