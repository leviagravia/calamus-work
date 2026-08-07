"""Single GTK-free writer for Calamus settings.json."""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping

from calamus_application_state import ApplicationStateSnapshot, decode_application_state
from calamus_config import load_json_file, save_json_file
from calamus_preferences import PreferencesSnapshot, decode_preferences


@dataclass(frozen=True)
class CalamusSettingsSnapshot:
    preferences: PreferencesSnapshot
    application_state: ApplicationStateSnapshot

    def to_mapping(self) -> dict[str, Any]:
        data = self.application_state.to_settings_mapping()
        data.update(self.preferences.to_settings_mapping())
        return data


class SettingsCodec:
    @staticmethod
    def decode(raw: Mapping[str, Any] | None) -> CalamusSettingsSnapshot:
        if raw is None:
            raw = {}
        if not isinstance(raw, Mapping):
            raw = {}
        return CalamusSettingsSnapshot(
            preferences=decode_preferences(raw),
            application_state=decode_application_state(raw),
        )

    @staticmethod
    def encode(snapshot: CalamusSettingsSnapshot) -> dict[str, Any]:
        if not isinstance(snapshot, CalamusSettingsSnapshot):
            raise TypeError("snapshot must be CalamusSettingsSnapshot")
        return snapshot.to_mapping()


class SettingsRepository:
    """Own the only physical settings.json write path used by the application."""

    def __init__(self, config_dir: str) -> None:
        if not isinstance(config_dir, str) or not config_dir:
            raise ValueError("config_dir must be non-empty")
        self.config_dir = config_dir
        self.settings_file = os.path.join(config_dir, "settings.json")
        self._snapshot = SettingsCodec.decode(load_json_file(self.settings_file, {}))

    @property
    def snapshot(self) -> CalamusSettingsSnapshot:
        return self._snapshot

    def reload(self) -> CalamusSettingsSnapshot:
        loaded = SettingsCodec.decode(load_json_file(self.settings_file, {}))
        self._snapshot = loaded
        return loaded

    def _commit(self, requested: CalamusSettingsSnapshot) -> bool:
        payload = SettingsCodec.encode(requested)
        if not save_json_file(self.settings_file, payload):
            return False
        self._snapshot = requested
        return True

    def update_preferences(self, requested: PreferencesSnapshot) -> bool:
        if not isinstance(requested, PreferencesSnapshot):
            raise TypeError("requested must be PreferencesSnapshot")
        return self._commit(CalamusSettingsSnapshot(requested, self._snapshot.application_state))

    def update_application_state(self, requested: ApplicationStateSnapshot) -> bool:
        if not isinstance(requested, ApplicationStateSnapshot):
            raise TypeError("requested must be ApplicationStateSnapshot")
        return self._commit(CalamusSettingsSnapshot(self._snapshot.preferences, requested))

    def replace(self, requested: CalamusSettingsSnapshot) -> bool:
        return self._commit(requested)
