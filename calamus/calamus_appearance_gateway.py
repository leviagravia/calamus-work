"""Application-service gateway for the Calamus appearance preference.

The gateway coordinates persistence, compatibility menu controls, and the
existing appearance renderer without importing GTK or touching document state.
The host is the thin App adapter and must provide the small methods/attributes
used below.
"""
from __future__ import annotations

from typing import Any

from calamus_appearance_preferences import (
    APPEARANCE_DARK,
    APPEARANCE_LIGHT,
    appearance_settings_overrides,
    prepare_appearance_preference_plan,
)


def sync_appearance_controls(host: Any) -> None:
    """Synchronize the two legacy check controls from one canonical mode."""
    host._syncing_appearance_items = True
    try:
        if hasattr(host, "white_item"):
            host.white_item.set_active(host.appearance_mode == APPEARANCE_LIGHT)
        if hasattr(host, "dark_item"):
            host.dark_item.set_active(host.appearance_mode == APPEARANCE_DARK)
    finally:
        host._syncing_appearance_items = False


def execute_appearance_preference_request(host: Any, requested_mode: str) -> bool:
    """Persist an appearance transition before committing or rendering it."""
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
