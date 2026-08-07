"""GTK-free preference/application-state transaction controllers for W106."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from calamus_application_state import ApplicationStateSnapshot
from calamus_preferences import PreferencesSnapshot
from calamus_settings_repository import SettingsRepository


class PreferenceProjectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreferenceTransitionResult:
    changed: bool
    previous: PreferencesSnapshot
    current: PreferencesSnapshot


class PreferencesController:
    def __init__(self, repository: SettingsRepository) -> None:
        self._repository = repository

    @property
    def current(self) -> PreferencesSnapshot:
        return self._repository.snapshot.preferences

    def transition(
        self,
        requested: PreferencesSnapshot,
        *,
        project: Callable[[PreferencesSnapshot], Any] | None = None,
    ) -> PreferenceTransitionResult:
        previous = self.current
        if requested == previous:
            return PreferenceTransitionResult(False, previous, previous)
        if not self._repository.update_preferences(requested):
            raise OSError("could not persist preferences")
        if project is not None:
            try:
                project(requested)
            except Exception as exc:
                rollback_saved = self._repository.update_preferences(previous)
                rollback_projected = False
                if rollback_saved:
                    try:
                        project(previous)
                        rollback_projected = True
                    except Exception:
                        rollback_projected = False
                if not rollback_saved or not rollback_projected:
                    raise PreferenceProjectionError(
                        "preference projection failed and rollback was incomplete"
                    ) from exc
                raise PreferenceProjectionError("preference projection failed; state rolled back") from exc
        return PreferenceTransitionResult(True, previous, requested)

    def update(self, *, project: Callable[[PreferencesSnapshot], Any] | None = None, **changes: Any) -> PreferenceTransitionResult:
        return self.transition(self.current.updated(**changes), project=project)


class ApplicationStateController:
    def __init__(self, repository: SettingsRepository) -> None:
        self._repository = repository

    @property
    def current(self) -> ApplicationStateSnapshot:
        return self._repository.snapshot.application_state

    def _update(self, **changes: Any) -> bool:
        requested = self.current.updated(**changes)
        if requested == self.current:
            return True
        return self._repository.update_application_state(requested)

    def record_window_geometry(self, width: int, height: int) -> bool:
        from calamus_application_state import (
            DEFAULT_WINDOW_HEIGHT,
            DEFAULT_WINDOW_WIDTH,
            MAX_WINDOW_HEIGHT,
            MAX_WINDOW_WIDTH,
            MIN_WINDOW_HEIGHT,
            MIN_WINDOW_WIDTH,
        )
        from calamus_config import clamp_int
        return self._update(
            width=clamp_int(width, DEFAULT_WINDOW_WIDTH, MIN_WINDOW_WIDTH, MAX_WINDOW_WIDTH),
            height=clamp_int(height, DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_HEIGHT, MAX_WINDOW_HEIGHT),
        )

    def record_last_file(self, path: str | None) -> bool:
        if path is not None and (not isinstance(path, str) or not path.strip()):
            path = None
        return self._update(last_file=path)

    def record_workspace_root(self, path: str | None) -> bool:
        if path is not None and (not isinstance(path, str) or not path.strip()):
            path = None
        return self._update(workspace_root=path)

    def record_workspace_visible(self, visible: bool) -> bool:
        if not isinstance(visible, bool):
            raise TypeError("workspace visibility must be boolean")
        return self._update(workspace_visible=visible)
