"""Application-service gateway for the Calamus opacity preference.

The gateway coordinates persistence, the legacy Transparent Mode checkbox and
runtime application.  It imports no GTK and never touches document or Undo
state.  All opacity entry points share this gateway so the checkbox cannot
become stale after choosing a fixed percentage.
"""
from __future__ import annotations

from typing import Any

from calamus_opacity import (
    MAX_OPACITY_PERCENT,
    apply_widget_opacity,
    opacity_settings_overrides,
    prepare_opacity_preference_plan,
    transparent_mode_requested_percent,
)


def sync_transparent_control(host: Any) -> None:
    host._syncing_opacity_item = True
    try:
        if hasattr(host, "transparent_item"):
            host.transparent_item.set_active(host.opacity_percent < MAX_OPACITY_PERCENT)
    finally:
        host._syncing_opacity_item = False


def execute_opacity_preference_request(host: Any, requested_percent: int) -> bool:
    """Persist, apply and commit one canonical opacity transition.

    Persistence failure leaves runtime state unchanged.  If the GTK adapter
    fails after persistence, the gateway performs a best-effort persistence
    rollback, restores the previous runtime opacity and resynchronizes the
    checkbox before reporting the error.
    """
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
        apply_widget_opacity(host, requested, widget_api=host._opacity_widget_api)
    except Exception as exc:
        host.save_settings(opacity_settings_overrides(previous))
        try:
            apply_widget_opacity(host, previous, widget_api=host._opacity_widget_api)
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
    """Translate the legacy checkbox state and execute the shared transition."""
    try:
        requested = transparent_mode_requested_percent(host.opacity_percent, enabled)
    except (TypeError, ValueError) as exc:
        sync_transparent_control(host)
        host.error(str(exc))
        return False
    return execute_opacity_preference_request(host, requested)
