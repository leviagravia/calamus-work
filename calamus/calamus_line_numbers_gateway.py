"""Application-service gateway for Calamus line numbers and custom gutter.

The gateway imports no GTK.  It coordinates strict preference planning,
persist-first lifecycle, menu synchronization and the runtime gutter adapter.
Document text and Undo state are never mutated.
"""
from __future__ import annotations

from typing import Any

from calamus_line_numbers import (
    line_number_settings_overrides,
    prepare_line_number_preference_plan,
)
from calamus_logging import log_nonfatal


def sync_line_number_control(host: Any) -> None:
    host._syncing_line_number_item = True
    try:
        if hasattr(host, "line_item"):
            host.line_item.set_active(host.line_numbers_enabled)
    finally:
        host._syncing_line_number_item = False


def _host_line_count(host: Any) -> int:
    _words, _chars, lines = host.text_stats()
    return lines


def refresh_line_number_gutter(host: Any, *, force: bool = False) -> bool:
    if not isinstance(force, bool):
        raise TypeError("force must be boolean")
    if not hasattr(host, "line_gutter"):
        return False
    try:
        host.line_gutter.render(
            host.line_numbers_enabled,
            _host_line_count(host),
            force=force,
        )
    except Exception as exc:
        log_nonfatal("line-number gutter refresh failed", exc)
        return False
    return True


def execute_line_number_preference_request(host: Any, requested_enabled: bool) -> bool:
    """Persist, render and commit one line-number visibility transition."""
    try:
        plan = prepare_line_number_preference_plan(
            host.line_numbers_enabled,
            requested_enabled,
        )
    except (TypeError, ValueError) as exc:
        sync_line_number_control(host)
        host.error(str(exc))
        return False

    if not plan.changed:
        refresh_line_number_gutter(host)
        sync_line_number_control(host)
        return False

    previous = plan.previous.enabled
    requested = plan.requested.enabled
    if not host.save_settings(line_number_settings_overrides(requested)):
        sync_line_number_control(host)
        host.error("Could not save the Line Numbers preference.")
        return False

    line_count = _host_line_count(host)
    try:
        host.line_gutter.render(requested, line_count)
    except Exception as exc:
        host.save_settings(line_number_settings_overrides(previous))
        try:
            host.line_gutter.render(previous, line_count)
        except Exception:
            pass
        sync_line_number_control(host)
        host.error(f"Could not apply the Line Numbers preference: {exc}")
        return False

    host.line_numbers_enabled = requested
    sync_line_number_control(host)
    host.update_title()
    return True
