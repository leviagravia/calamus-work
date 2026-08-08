"""Narrow boundary for the initial Writing date/time commands."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Any

from calamus_commands import insert_at as command_insert_at


@dataclass(frozen=True)
class WritingInsertPorts:
    command_layer_insert_date_time_text: Callable[[datetime, str], tuple[str, bool]]
    get_cursor_offset: Callable[[], int]
    buffer_text: Callable[[], str]
    execute_command: Callable[..., bool]
    now: Callable[[], datetime] = datetime.now


def insert_current_moment(ports: WritingInsertPorts, command_name: str, fmt: str) -> bool:
    if not isinstance(ports, WritingInsertPorts):
        raise TypeError("ports must be WritingInsertPorts")
    txt, changed = ports.command_layer_insert_date_time_text(ports.now(), fmt)
    if not changed:
        return False
    cursor = ports.get_cursor_offset()
    _, select = command_insert_at(ports.buffer_text(), cursor, txt)

    def edit(buf):
        buf.insert_at_cursor(txt)

    return ports.execute_command(command_name, edit, select_range=select)


def on_insert_date(ports: WritingInsertPorts, *_: Any):
    return insert_current_moment(ports, "Insert Date", "%Y-%m-%d")


def on_insert_time(ports: WritingInsertPorts, *_: Any):
    return insert_current_moment(ports, "Insert Time", "%H:%M")


def on_insert_datetime(ports: WritingInsertPorts, *_: Any):
    return insert_current_moment(ports, "Insert Date and Time", "%Y-%m-%d %H:%M")
