"""Narrow GTK signal helpers for W95extra Typewriter Mode.

The historical whole-App bridge is retired in W108.  These functions accept
only the concrete Typewriter/Viewport runtimes or shell projection callables.
"""
from __future__ import annotations


def on_text_key_press(runtime, widget, event):
    return runtime.on_key_press(widget, event)


def on_text_key_release(runtime, widget, event):
    return runtime.on_key_release(widget, event)


def on_text_move_cursor(typewriter_runtime, viewport_runtime, *_args):
    if typewriter_runtime.enabled:
        typewriter_runtime.on_keyboard()
    else:
        viewport_runtime.queue_visible_to_insert(0.02)
    return False


def on_text_button_press(runtime, widget, event):
    return runtime.on_button_press(widget, event)


def on_text_motion_notify(runtime, widget, event):
    return runtime.on_motion(widget, event)


def on_text_button_release(runtime, widget, event):
    return runtime.on_button_release(widget, event)


def on_text_scroll(runtime, widget, event):
    return runtime.on_scroll(widget, event)


def on_text_focus_out(runtime, widget, event):
    return runtime.on_focus_out(widget, event)


def project_typewriter_state(enabled, *, set_enabled, refresh_ui_state, update_title):
    for callback in (set_enabled, refresh_ui_state, update_title):
        if not callable(callback):
            raise TypeError("typewriter projection capabilities must be callable")
    set_enabled(bool(enabled))
    refresh_ui_state()
    update_title()


def on_typewriter_item_toggled(runtime, item):
    requested = bool(item.get_active())
    if requested == bool(runtime.enabled):
        return runtime.enabled
    return runtime.set_enabled(requested)


def toggle_typewriter_mode(runtime, *_args):
    return runtime.toggle()
