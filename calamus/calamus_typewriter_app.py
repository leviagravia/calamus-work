"""Thin App bridge for W95extra Typewriter Mode."""
from __future__ import annotations


def on_text_key_press(app, widget, event):
    return app.typewriter_runtime.on_key_press(widget, event)


def on_text_key_release(app, widget, event):
    return app.typewriter_runtime.on_key_release(widget, event)


def on_text_move_cursor(app, *_args):
    if app.typewriter_runtime.enabled:
        app.typewriter_runtime.on_keyboard()
    else:
        app.viewport_runtime.queue_visible_to_insert(0.02)
    return False


def on_text_button_press(app, widget, event):
    return app.typewriter_runtime.on_button_press(widget, event)


def on_text_motion_notify(app, widget, event):
    return app.typewriter_runtime.on_motion(widget, event)


def on_text_button_release(app, widget, event):
    return app.typewriter_runtime.on_button_release(widget, event)


def on_text_scroll(app, widget, event):
    return app.typewriter_runtime.on_scroll(widget, event)


def on_text_focus_out(app, widget, event):
    return app.typewriter_runtime.on_focus_out(widget, event)


def on_typewriter_state_changed(app, enabled):
    app.typewriter_mode = bool(enabled)
    refresh = getattr(app, "refresh_ui_state", None)
    if callable(refresh):
        refresh()
    app.update_title()


def on_typewriter_item_toggled(app, item):
    requested = bool(item.get_active())
    if requested == bool(app.typewriter_runtime.enabled):
        return app.typewriter_runtime.enabled
    return app.typewriter_runtime.set_enabled(requested)


def toggle_typewriter_mode(app, *_args):
    return app.typewriter_runtime.toggle()
