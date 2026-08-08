"""Narrow Scratchpad editor interaction gateways.

W108 removes the historical whole-App compatibility surface.  Each helper now
receives only the concrete view/runtime/callable capability it uses.
"""
from __future__ import annotations

from typing import Any, Callable


def current_section_target(current_heading_identifier: Callable[[], str | None]) -> str | None:
    if not callable(current_heading_identifier):
        raise TypeError("current_heading_identifier must be callable")
    identifier = current_heading_identifier()
    return f"#{identifier}" if identifier else None


def selected_text(text_view: Any) -> str:
    buffer = text_view.get_buffer()
    if not buffer.get_has_selection():
        return ""
    start, end = buffer.get_selection_bounds()
    return buffer.get_text(start, end, True)


def insert_body(
    text_view: Any,
    body: Any,
    *,
    execute_command: Callable[..., bool],
    set_cursor_offset: Callable[[int], Any],
) -> bool:
    if not isinstance(body, str) or not body:
        return False
    if not callable(execute_command) or not callable(set_cursor_offset):
        raise TypeError("scratchpad insertion capabilities must be callable")
    buffer = text_view.get_buffer()
    cursor = buffer.get_iter_at_mark(buffer.get_insert()).get_offset()

    def edit(target_buffer):
        target_buffer.insert(target_buffer.get_iter_at_offset(cursor), body)

    changed = execute_command("Insert Scratchpad Body", edit)
    if changed:
        set_cursor_offset(cursor + len(body))
        text_view.grab_focus()
    return bool(changed)


def copy_body(body: Any, *, clipboard_provider: Callable[[], Any]) -> bool:
    if not isinstance(body, str):
        return False
    if not callable(clipboard_provider):
        raise TypeError("clipboard_provider must be callable")
    clipboard = clipboard_provider()
    clipboard.set_text(body, -1)
    clipboard.store()
    return True


def sync_document(runtime: Any, *, force: bool = False) -> None:
    if runtime is not None:
        runtime.sync_document(force=force)
