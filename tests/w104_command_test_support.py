"""Test-only accessors for the canonical W104 command/action metadata.

Historical wiring tests use this projection instead of treating the old
hand-written shortcut source file as an authority.
"""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CALAMUS_DIR = str(ROOT / "calamus")
if CALAMUS_DIR not in sys.path:
    sys.path.insert(0, CALAMUS_DIR)

from calamus_command_catalog import (  # noqa: E402
    command_spec,
    command_specs,
    shortcut_bindings,
    shortcut_guide_entries,
)


def guide_has(menu: str, command: str, shortcut: str) -> bool:
    return any(
        row.menu == menu and row.command == command and row.access == shortcut
        for row in shortcut_guide_entries()
    )


def command_exists(command_id: str) -> bool:
    try:
        command_spec(command_id)
    except KeyError:
        return False
    return True


def command_shortcut_has(command_id: str, accelerator: str, **payload) -> bool:
    expected = tuple(sorted(payload.items()))
    spec = command_spec(command_id)
    return any(
        row.accelerator == accelerator and row.payload == expected
        for row in spec.shortcuts
    )


def actual_binding_has(command_id: str, accelerator: str, **payload) -> bool:
    expected = dict(payload)
    return any(
        accel == accelerator and cid == command_id and data == expected
        for accel, cid, data in shortcut_bindings()
    )


def catalog_ids() -> tuple[str, ...]:
    return tuple(spec.command_id for spec in command_specs())
