"""Application-service gateway for the Calamus opacity preference.

W105 projects Transparent Mode from the canonical opacity value. The gateway
never reads or mutates a menu widget.
"""
from __future__ import annotations

from typing import Any

from calamus_opacity import (
    opacity_settings_overrides,
    prepare_opacity_preference_plan,
    transparent_mode_requested_percent,
)


def sync_transparent_control(host: Any) -> None:
    refresh = getattr(host, "refresh_ui_state", None)
    if callable(refresh):
        refresh()


def execute_opacity_preference_request(host: Any, requested_percent: int) -> bool:
    try:
        plan = prepare_opacity_preference_plan(host.opacity_percent, requested_percent)
    except (TypeError, ValueError) as exc:
        sync_transparent_control(host)
        host.error(str(exc))
        return False

    if not plan.changed:
        sync_transparent_control(host)
        return False

    requested = plan.requested.percent
    previous = plan.previous.percent
    if not host.save_settings(opacity_settings_overrides(requested)):
        sync_transparent_control(host)
        host.error("Could not save the Opacity preference.")
        return False

    try:
        host.apply_opacity_percent(requested)
    except Exception as exc:
        host.save_settings(opacity_settings_overrides(previous))
        try:
            host.apply_opacity_percent(previous)
        except Exception:
            pass
        sync_transparent_control(host)
        host.error(f"Could not apply the Opacity preference: {exc}")
        return False

    host.opacity_percent = requested
    sync_transparent_control(host)
    host.update_title()
    return True


def execute_transparent_mode_request(host: Any, enabled: bool) -> bool:
    try:
        requested = transparent_mode_requested_percent(host.opacity_percent, enabled)
    except (TypeError, ValueError) as exc:
        sync_transparent_control(host)
        host.error(str(exc))
        return False
    return execute_opacity_preference_request(host, requested)
