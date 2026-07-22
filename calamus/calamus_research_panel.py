"""Canonical runtime for the single Calamus Research shell."""
from __future__ import annotations

from typing import Any, Callable


class ResearchPanelRuntime:
    def __init__(
        self,
        host: Any,
        view: Any,
        menu_item: Any,
        focus_editor: Callable[[], None],
        *,
        default_client: str = "clip-collection",
    ) -> None:
        if any(value is None for value in (host, view, menu_item)):
            raise TypeError("host, view and menu_item are required")
        if not callable(focus_editor):
            raise TypeError("focus_editor must be callable")
        self._host = host
        self._view = view
        self._menu_item = menu_item
        self._focus_editor = focus_editor
        self._default_client = default_client
        self._syncing_menu = False

    @property
    def active_client(self) -> str | None:
        return self._view.active_client

    @property
    def is_visible(self) -> bool:
        return bool(self._host.is_visible)

    def show(self, client_id: str | None = None) -> bool:
        target = client_id or self.active_client or self._default_client
        self._view.show_client(target)
        self._host.show("research")
        self._sync_menu(True)
        self._view.focus_active()
        return True

    def hide(self) -> bool:
        self._host.hide()
        self._sync_menu(False)
        self._focus_editor()
        return False

    def toggle(self) -> bool:
        return self.hide() if self.is_visible else self.show()

    def on_menu_toggled(self, item: Any) -> bool:
        if self._syncing_menu:
            return self.is_visible
        return self.show() if item.get_active() else self.hide()

    def _sync_menu(self, active: bool) -> None:
        if self._menu_item.get_active() == active:
            return
        self._syncing_menu = True
        try:
            self._menu_item.set_active(active)
        finally:
            self._syncing_menu = False
