"""Application-service gateway for the Calamus appearance preference.

W105 removes all menu-widget reach-through. Persistence and rendering remain
unchanged; the application UI-state boundary reprojects from logical truth.
"""
from __future__ import annotations

from typing import Any

from calamus_appearance_preferences import (
    appearance_settings_overrides,
    prepare_appearance_preference_plan,
)


def sync_appearance_controls(host: Any) -> None:
    """Compatibility name: reproject logical appearance state, never widgets."""
    refresh = getattr(host, "refresh_ui_state", None)
    if callable(refresh):
        refresh()


def execute_appearance_preference_request(host: Any, requested_mode: str) -> bool:
    try:
        plan = prepare_appearance_preference_plan(host.appearance_mode, requested_mode)
    except (TypeError, ValueError) as exc:
        sync_appearance_controls(host)
        host.error(str(exc))
        return False

    if not plan.changed:
        sync_appearance_controls(host)
        return False

    if not host.save_settings(appearance_settings_overrides(plan.requested.mode)):
        sync_appearance_controls(host)
        host.error("Could not save the Appearance preference.")
        return False

    host.appearance_mode = plan.requested.mode
    sync_appearance_controls(host)
    host.apply_font()
    return True
