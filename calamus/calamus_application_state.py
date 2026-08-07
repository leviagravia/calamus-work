"""GTK-free durable launch/application state for Calamus W106."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from calamus_config import clamp_int
from calamus_view_preferences import normalize_boolean

DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 650
MIN_WINDOW_WIDTH = 520
MIN_WINDOW_HEIGHT = 360
MAX_WINDOW_WIDTH = 1600
MAX_WINDOW_HEIGHT = 1000


def _optional_path(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        if value and "\x00" not in value and "\n" not in value and "\r" not in value:
            return value
    return None


@dataclass(frozen=True)
class ApplicationStateSnapshot:
    width: int = DEFAULT_WINDOW_WIDTH
    height: int = DEFAULT_WINDOW_HEIGHT
    last_file: str | None = None
    workspace_root: str | None = None
    workspace_visible: bool = False

    def __post_init__(self) -> None:
        if self.width != clamp_int(self.width, DEFAULT_WINDOW_WIDTH, MIN_WINDOW_WIDTH, MAX_WINDOW_WIDTH):
            raise ValueError("width is not normalized")
        if self.height != clamp_int(self.height, DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_HEIGHT, MAX_WINDOW_HEIGHT):
            raise ValueError("height is not normalized")
        if self.last_file is not None and _optional_path(self.last_file) != self.last_file:
            raise ValueError("last_file is not normalized")
        if self.workspace_root is not None and _optional_path(self.workspace_root) != self.workspace_root:
            raise ValueError("workspace_root is not normalized")
        if not isinstance(self.workspace_visible, bool):
            raise TypeError("workspace_visible must be boolean")

    def updated(self, **changes: Any) -> "ApplicationStateSnapshot":
        return replace(self, **changes)

    def to_settings_mapping(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "last_file": self.last_file,
            "workspace_root": self.workspace_root,
            "workspace_visible": self.workspace_visible,
        }


def decode_application_state(settings: Mapping[str, Any] | None) -> ApplicationStateSnapshot:
    if settings is None:
        settings = {}
    if not isinstance(settings, Mapping):
        raise TypeError("settings must be a mapping")
    return ApplicationStateSnapshot(
        width=clamp_int(settings.get("width"), DEFAULT_WINDOW_WIDTH, MIN_WINDOW_WIDTH, MAX_WINDOW_WIDTH),
        height=clamp_int(settings.get("height"), DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_HEIGHT, MAX_WINDOW_HEIGHT),
        last_file=_optional_path(settings.get("last_file")),
        workspace_root=_optional_path(settings.get("workspace_root")),
        workspace_visible=normalize_boolean(settings.get("workspace_visible"), False),
    )
