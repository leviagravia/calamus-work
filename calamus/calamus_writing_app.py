"""Thin App bridge for the initial Writing menu commands."""
from __future__ import annotations

from datetime import datetime

from calamus_commands import insert_at as command_insert_at


def insert_current_moment(app, command_name, fmt):
    txt, changed = app.command_layer_insert_date_time_text(datetime.now(), fmt)
    if not changed:
        return False
    cursor = app.get_cursor_offset()
    _, select = command_insert_at(app.buffer_text(), cursor, txt)

    def edit(buf):
        buf.insert_at_cursor(txt)

    return app.execute_command(command_name, edit, select_range=select)


def on_insert_date(app, *_):
    return insert_current_moment(app, "Insert Date", "%Y-%m-%d")


def on_insert_time(app, *_):
    return insert_current_moment(app, "Insert Time", "%H:%M")


def on_insert_datetime(app, *_):
    return insert_current_moment(app, "Insert Date and Time", "%Y-%m-%d %H:%M")
