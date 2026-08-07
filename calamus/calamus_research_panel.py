"""Canonical runtime for the single Calamus Research shell."""
from __future__ import annotations

from typing import Any, Callable


class ResearchPanelRuntime:
    def __init__(
        self,
        host: Any,
        view: Any,
        focus_editor: Callable[[], None],
        *,
        default_client: str = "clip-collection",
        on_visibility_changed: Callable[[bool], None] | None = None,
    ) -> None:
        if any(value is None for value in (host, view)):
            raise TypeError("host and view are required")
        if not callable(focus_editor):
            raise TypeError("focus_editor must be callable")
        if on_visibility_changed is not None and not callable(on_visibility_changed):
            raise TypeError("on_visibility_changed must be callable")
        self._host = host
        self._view = view
        self._focus_editor = focus_editor
        self._default_client = default_client
        self._on_visibility_changed = on_visibility_changed or (lambda _visible: None)

    @property
    def active_client(self) -> str | None:
        return self._view.active_client

    @property
    def is_visible(self) -> bool:
        return bool(self._host.is_visible)

    def show(self, client_id: str | None = None) -> bool:
        target = client_id or self.active_client or self._default_client
        self._host.show("research")
        self._view.show_client(target)
        self._on_visibility_changed(True)
        return True

    def hide(self) -> bool:
        self._host.hide()
        self._focus_editor()
        self._on_visibility_changed(False)
        return False

    def set_visible(self, visible: bool) -> bool:
        return self.show() if bool(visible) else self.hide()

    def toggle(self) -> bool:
        return self.hide() if self.is_visible else self.show()
