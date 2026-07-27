"""Thin App/GTK adapter functions for Scratchpad editor interactions.

The module imports no GI namespace.  It receives the composed App object and
routes mutations through the application's canonical command and clipboard
gateways.
"""
from __future__ import annotations

from typing import Any


def current_section_target(app: Any) -> str | None:
    identifier = app.current_heading_identifier()
    return f"#{identifier}" if identifier else None


def selected_text(app: Any) -> str:
    buffer = app.text.get_buffer()
    if not buffer.get_has_selection():
        return ""
    start, end = buffer.get_selection_bounds()
    return buffer.get_text(start, end, True)


def insert_body(app: Any, body: Any) -> bool:
    if not isinstance(body, str) or not body:
        return False
    buffer = app.text.get_buffer()
    cursor = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()

    def edit(target_buffer):
        target_buffer.insert(target_buffer.get_iter_at_offset(cursor), body)

    changed = app.execute_command("Insert Scratchpad Body", edit)
    if changed:
        app.set_cursor_offset(cursor + len(body))
        app.text.grab_focus()
    return bool(changed)


def copy_body(app: Any, body: Any) -> bool:
    if not isinstance(body, str):
        return False
    clipboard = app._clipboard()
    clipboard.set_text(body, -1)
    clipboard.store()
    return True

def sync_document(app: Any, *, force: bool = False) -> None:
    runtime = getattr(app, "scratchpad_runtime", None)
    if runtime is not None:
        runtime.sync_document(force=force)
