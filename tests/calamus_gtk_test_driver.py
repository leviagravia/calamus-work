"""Deterministic helpers for real Calamus GTK dialog tests.

This module is test-only.  It never patches production dialog functions.  It
uses GTK's own main loop, bounded polling, semantic widget names, and explicit
cleanup so a failed assertion cannot leave a modal dialog or process blocked.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Callable

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, GLib, Gtk
    HAVE_GTK = True
except Exception:  # pragma: no cover - exercised on headless builders
    Gdk = GLib = Gtk = None
    HAVE_GTK = False


def display_ready() -> bool:
    if not HAVE_GTK:
        return False
    try:
        result = Gtk.init_check()
    except TypeError:
        result = Gtk.init_check(None)
    ok = bool(result[0]) if isinstance(result, tuple) else bool(result)
    return bool(ok and Gdk.Display.get_default() is not None)


def pump() -> None:
    if not HAVE_GTK:
        return
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


def visible_dialog(title: str):
    if not HAVE_GTK:
        return None
    return next(
        (
            window
            for window in Gtk.Window.list_toplevels()
            if isinstance(window, Gtk.Dialog)
            and window.get_visible()
            and (window.get_title() or "") == title
        ),
        None,
    )


def visible_dialogs() -> tuple:
    if not HAVE_GTK:
        return ()
    return tuple(
        window
        for window in Gtk.Window.list_toplevels()
        if isinstance(window, Gtk.Dialog) and window.get_visible()
    )


def named_widgets(widget, name: str, widget_type) -> tuple:
    values = []
    if isinstance(widget, widget_type) and widget.get_name() == name:
        values.append(widget)
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            values.extend(named_widgets(child, name, widget_type))
    return tuple(values)


def named_widget(widget, name: str, widget_type):
    values = named_widgets(widget, name, widget_type)
    if len(values) != 1:
        raise AssertionError(
            f"expected exactly one {widget_type.__name__} named {name!r}; "
            f"found {len(values)}"
        )
    return values[0]


def label_texts(widget) -> tuple[str, ...]:
    """Return complete label strings without recursively splitting characters."""
    values: list[str] = []
    if isinstance(widget, Gtk.Label):
        values.append(widget.get_text())
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            values.extend(label_texts(child))
    return tuple(values)


def dialog_text(widget) -> str:
    return "\n".join(label_texts(widget))


def close_visible_dialogs() -> None:
    for dialog in visible_dialogs():
        try:
            dialog.response(Gtk.ResponseType.CANCEL)
        except Exception:
            try:
                dialog.destroy()
            except Exception:
                pass
    pump()


@dataclass
class ModalDriver:
    """Bounded GTK-main-loop driver for one nested modal workflow."""

    phases: list[Callable[[], bool]]
    timeout_seconds: float = 10.0
    poll_ms: int = 25
    failures: list[BaseException] = field(default_factory=list)
    _index: int = 0
    _started: float = field(default_factory=time.monotonic)

    def start(self) -> None:
        if not HAVE_GTK:
            raise RuntimeError("GTK is unavailable")
        GLib.timeout_add(self.poll_ms, self._poll)

    def _poll(self) -> bool:
        try:
            if time.monotonic() - self._started > self.timeout_seconds:
                raise TimeoutError(
                    f"modal workflow timed out at phase {self._index + 1}/"
                    f"{len(self.phases)}"
                )
            if self._index >= len(self.phases):
                return False
            completed = bool(self.phases[self._index]())
            if completed:
                self._index += 1
            return self._index < len(self.phases)
        except BaseException as error:  # keep assertion for the test thread
            self.failures.append(error)
            close_visible_dialogs()
            return False

    def assert_complete(self) -> None:
        if self.failures:
            raise self.failures[0]
        if self._index != len(self.phases):
            raise AssertionError(
                f"modal workflow incomplete: {self._index}/{len(self.phases)} phases"
            )
